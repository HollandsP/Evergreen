"""
AI Content Pipeline API
Main FastAPI application
"""

from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import structlog
import asyncio

from src.core.config import settings
from api.json_utils import CustomJSONResponse
from api.routes import projects, generation, health, auth, scripts, editor, scene_status, video_streaming, ai_enhancements
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
app.include_router(editor.router, prefix=settings.API_PREFIX)
app.include_router(ai_enhancements.router, prefix=settings.API_PREFIX)
app.include_router(scene_status.router)
app.include_router(video_streaming.router)

# WebSocket endpoint
from api.websocket import websocket_endpoint, manager, system_status_broadcaster

@app.websocket("/ws")
async def websocket_route(websocket: WebSocket, client_id: str = None):
    """WebSocket endpoint for real-time updates."""
    if not client_id:
        import uuid
        client_id = str(uuid.uuid4())
    await websocket_endpoint(websocket, client_id)

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Starting AI Content Pipeline API")
    
    # Initialize performance services
    try:
        from src.services.scene_index_manager import get_scene_index_manager
        from src.services.file_watcher import get_file_watcher
        
        # Initialize scene index manager
        scene_manager = await get_scene_index_manager()
        logger.info("Scene Index Manager initialized successfully")
        
        # Initialize file watcher
        file_watcher = await get_file_watcher()
        logger.info("File Watcher initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize performance services: {e}")
        # Don't fail startup, services will initialize on first use
    
    # Start WebSocket system status broadcaster
    asyncio.create_task(system_status_broadcaster())
    logger.info("WebSocket system status broadcaster started")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down AI Content Pipeline API")
    
    # Cleanup performance services
    try:
        from src.services.scene_index_manager import cleanup_scene_index_manager
        from src.services.file_watcher import cleanup_file_watcher
        
        await cleanup_file_watcher()
        await cleanup_scene_index_manager()
        logger.info("Performance services cleaned up successfully")
        
    except Exception as e:
        logger.error(f"Error cleaning up performance services: {e}")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI Content Pipeline API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }
