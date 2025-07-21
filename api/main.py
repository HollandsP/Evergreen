"""
AI Content Pipeline API
Main FastAPI application
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

from src.core.config import settings
from api.json_utils import CustomJSONResponse
from api.routes import projects, generation, health, auth, scripts
from api.middleware import (
    RequestIDMiddleware,
    LoggingMiddleware,
    RateLimitMiddleware,
    ErrorHandlingMiddleware,
    add_security_headers
)

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


# Create FastAPI app with custom JSON response
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Automated video generation for AI apocalypse narratives",
    docs_url=f"{settings.API_PREFIX}/docs",
    redoc_url=f"{settings.API_PREFIX}/redoc",
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    default_response_class=CustomJSONResponse
)

# Add middleware in order (applied in reverse)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(RateLimitMiddleware, max_requests=settings.RATE_LIMIT_PER_MINUTE, window_seconds=60)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(BaseHTTPMiddleware, dispatch=add_security_headers)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(projects.router, prefix=settings.API_PREFIX)
app.include_router(scripts.router, prefix=settings.API_PREFIX)
app.include_router(generation.router, prefix=settings.API_PREFIX)

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Starting AI Content Pipeline API")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down AI Content Pipeline API")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI Content Pipeline API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }
