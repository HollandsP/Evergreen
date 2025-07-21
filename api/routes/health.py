"""
Health check endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis
import structlog

from src.core.database.connection import get_db

router = APIRouter()
logger = structlog.get_logger()


@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "ai-content-pipeline",
        "version": "1.0.0"
    }


@router.get("/health/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    """Detailed health check with dependency status"""
    health_status = {
        "status": "healthy",
        "service": "ai-content-pipeline",
        "version": "1.0.0",
        "checks": {
            "database": "unknown",
            "redis": "unknown",
            "storage": "unknown"
        }
    }
    
    # Check database
    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        health_status["checks"]["database"] = "unhealthy"
        health_status["status"] = "degraded"
    
    # Check Redis
    try:
        r = redis.from_url("redis://redis:6379", decode_responses=True)
        await r.ping()
        health_status["checks"]["redis"] = "healthy"
        await r.close()
    except Exception as e:
        logger.error("Redis health check failed", error=str(e))
        health_status["checks"]["redis"] = "unhealthy"
        health_status["status"] = "degraded"
    
    # Check storage (simplified check)
    try:
        import os
        output_path = "/app/output"
        if os.path.exists(output_path) and os.access(output_path, os.W_OK):
            health_status["checks"]["storage"] = "healthy"
        else:
            health_status["checks"]["storage"] = "unhealthy"
            health_status["status"] = "degraded"
    except Exception as e:
        logger.error("Storage health check failed", error=str(e))
        health_status["checks"]["storage"] = "unhealthy"
        health_status["status"] = "degraded"
    
    # Set overall status
    if all(check == "healthy" for check in health_status["checks"].values()):
        health_status["status"] = "healthy"
    elif any(check == "unhealthy" for check in health_status["checks"].values()):
        health_status["status"] = "unhealthy"
    
    return health_status


@router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Kubernetes readiness probe endpoint"""
    try:
        # Check if database is ready
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        
        # Check if Redis is ready
        r = redis.from_url("redis://redis:6379", decode_responses=True)
        await r.ping()
        await r.close()
        
        return {"ready": True}
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        return {"ready": False}, 503


@router.get("/live")
async def liveness_check():
    """Kubernetes liveness probe endpoint"""
    return {"alive": True}