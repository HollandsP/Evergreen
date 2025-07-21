"""
Common dependencies for FastAPI routes
"""
from typing import Optional, Annotated
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import redis.asyncio as redis
import structlog

from src.core.config import settings
from src.core.database.connection import get_db
from src.core.database.models import User

logger = structlog.get_logger()

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/token")


async def get_redis() -> redis.Redis:
    """Get Redis connection"""
    r = redis.from_url(str(settings.REDIS_URL), decode_responses=True)
    try:
        yield r
    finally:
        await r.close()


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    """Get current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=["HS256"]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Get user from database
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """Ensure user is active"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt


class RateLimiter:
    """Rate limiting dependency"""
    
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
    
    async def __call__(
        self,
        user: Annotated[User, Depends(get_current_user)],
        redis_client: Annotated[redis.Redis, Depends(get_redis)]
    ) -> None:
        """Check rate limit for user"""
        key = f"rate_limit:user:{user.id}"
        
        try:
            current = await redis_client.incr(key)
            if current == 1:
                await redis_client.expire(key, self.window_seconds)
            
            if current > self.max_requests:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Max {self.max_requests} requests per {self.window_seconds} seconds"
                )
        except redis.RedisError as e:
            logger.error("Redis error in rate limiting", error=str(e))
            # Don't block requests if Redis is down
            pass


# Pre-configured rate limiters
rate_limit_per_minute = RateLimiter(
    max_requests=settings.RATE_LIMIT_PER_MINUTE,
    window_seconds=60
)

rate_limit_per_hour = RateLimiter(
    max_requests=settings.RATE_LIMIT_PER_HOUR,
    window_seconds=3600
)


class Pagination:
    """Pagination parameters dependency"""
    
    def __init__(
        self,
        skip: int = 0,
        limit: int = 20,
        max_limit: int = 100
    ):
        self.skip = skip
        self.limit = min(limit, max_limit)


async def check_project_ownership(
    project_id: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> None:
    """Check if user owns the project"""
    from src.core.database.models import Project
    
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == user.id
        )
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )