"""
FastAPI middleware for request processing
"""
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

from src.core.config import settings
from api.validators import ErrorResponse
from api.json_utils import CustomJSONResponse

logger = structlog.get_logger()


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add unique request ID to each request"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add request ID to request state and response headers"""
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Add request ID to structlog context
        structlog.contextvars.bind_contextvars(request_id=request_id)
        
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            structlog.contextvars.clear_contextvars()


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests and responses"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request details and response status"""
        start_time = time.time()
        
        # Log request
        logger.info(
            "Request started",
            method=request.method,
            path=request.url.path,
            client_host=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        
        try:
            response = await call_next(request)
            
            # Calculate request duration
            duration = time.time() - start_time
            
            # Log response
            logger.info(
                "Request completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_seconds=round(duration, 3),
            )
            
            # Add timing header
            response.headers["X-Process-Time"] = str(round(duration, 3))
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                "Request failed",
                method=request.method,
                path=request.url.path,
                error=str(e),
                duration_seconds=round(duration, 3),
                exc_info=True,
            )
            raise


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple IP-based rate limiting middleware"""
    
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.request_counts = {}
        self.window_start = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check rate limit for client IP"""
        # Skip rate limiting for health checks
        if request.url.path.startswith("/health"):
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Skip rate limiting in testing mode
        if settings.TESTING:
            return await call_next(request)
        
        current_time = time.time()
        
        # Initialize or reset window for IP
        if (client_ip not in self.window_start or 
            current_time - self.window_start[client_ip] > self.window_seconds):
            self.request_counts[client_ip] = 0
            self.window_start[client_ip] = current_time
        
        # Increment request count
        self.request_counts[client_ip] += 1
        
        # Check rate limit
        if self.request_counts[client_ip] > self.max_requests:
            logger.warning(
                "Rate limit exceeded",
                client_ip=client_ip,
                requests=self.request_counts[client_ip],
                window_seconds=self.window_seconds,
            )
            
            error_response = ErrorResponse(
                detail=f"Rate limit exceeded. Max {self.max_requests} requests per {self.window_seconds} seconds",
                status_code=429,
            )
            
            return CustomJSONResponse(
                status_code=429,
                content=error_response.dict(),
                headers={
                    "Retry-After": str(self.window_seconds),
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(self.window_start[client_ip] + self.window_seconds)),
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = max(0, self.max_requests - self.request_counts[client_ip])
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(self.window_start[client_ip] + self.window_seconds))
        
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Global error handling middleware"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle uncaught exceptions"""
        try:
            return await call_next(request)
        except Exception as e:
            # Log the error
            logger.error(
                "Unhandled exception",
                error=str(e),
                path=request.url.path,
                method=request.method,
                exc_info=True,
            )
            
            # Return error response
            error_response = ErrorResponse(
                detail="Internal server error",
                status_code=500,
            )
            
            return CustomJSONResponse(
                status_code=500,
                content=error_response.dict(),
            )


async def add_security_headers(request: Request, call_next: Callable) -> Response:
    """Add security headers to responses"""
    response = await call_next(request)
    
    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Add CSP header for API responses
    if request.url.path.startswith("/api"):
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none';"
    
    return response