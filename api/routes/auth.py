"""
Authentication endpoints with OAuth2 and JWT
"""
from datetime import datetime, timedelta
from typing import Annotated, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext
import structlog

from src.core.config import settings
from src.core.database.connection import get_db
from src.core.database.models import User
from api.dependencies import create_access_token, get_current_user
from api.validators import (
    UserCreate,
    UserResponse,
    Token,
    UserLogin,
)

router = APIRouter(prefix="/auth", tags=["authentication"])
logger = structlog.get_logger()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


async def authenticate_user(
    db: AsyncSession,
    username: str,
    password: str
) -> Optional[User]:
    """Authenticate a user by username and password"""
    result = await db.execute(
        select(User).where(User.email == username)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    """
    Register a new user
    
    - **email**: User's email address (must be unique)
    - **password**: Password (min 8 characters)
    - **full_name**: User's full name
    """
    # Check if user already exists
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    
    user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        is_active=True,
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    logger.info(
        "User registered",
        user_id=str(user.id),
        email=user.email
    )
    
    return user


@router.post("/token", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> dict:
    """
    Login with username and password to get access token
    
    OAuth2 compatible token endpoint
    
    - **username**: User's email address
    - **password**: User's password
    """
    user = await authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        logger.warning(
            "Failed login attempt",
            username=form_data.username
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )
    
    logger.info(
        "User logged in",
        user_id=str(user.id),
        email=user.email
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(
    current_user: Annotated[User, Depends(get_current_user)]
) -> dict:
    """
    Refresh access token
    
    Get a new access token using the current valid token
    """
    # Create new access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(current_user.id)},
        expires_delta=access_token_expires
    )
    
    logger.info(
        "Token refreshed",
        user_id=str(current_user.id)
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    Get current user information
    
    Returns the authenticated user's profile information
    """
    return current_user


@router.post("/logout")
async def logout(
    current_user: Annotated[User, Depends(get_current_user)]
) -> dict:
    """
    Logout current user
    
    This is a placeholder endpoint. In a real application,
    you might want to blacklist the token or perform other cleanup.
    """
    logger.info(
        "User logged out",
        user_id=str(current_user.id)
    )
    
    return {"message": "Successfully logged out"}


@router.put("/me", response_model=UserResponse)
async def update_user_profile(
    user_update: dict,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    """
    Update current user profile
    
    - **full_name**: Update user's full name
    - **password**: Update password (optional)
    """
    # Update allowed fields
    if "full_name" in user_update:
        current_user.full_name = user_update["full_name"]
    
    if "password" in user_update:
        if len(user_update["password"]) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters"
            )
        current_user.hashed_password = get_password_hash(user_update["password"])
    
    current_user.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(current_user)
    
    logger.info(
        "User profile updated",
        user_id=str(current_user.id)
    )
    
    return current_user