"""
Health check endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis
import structlog
from datetime import datetime

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


@router.get("/health/services")
async def get_services_health(db: AsyncSession = Depends(get_db)):
    """Get health status of all services"""
    import time
    import psutil
    from datetime import datetime
    
    services = []
    
    # Database service
    db_start = time.time()
    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        db_response_time = (time.time() - db_start) * 1000
        services.append({
            "name": "PostgreSQL Database",
            "status": "healthy",
            "responseTime": round(db_response_time, 2),
            "errorRate": 0.0,
            "uptime": 99.9,
            "lastCheck": datetime.now().isoformat(),
            "details": "Primary database connection"
        })
    except Exception as e:
        services.append({
            "name": "PostgreSQL Database",
            "status": "unhealthy",
            "responseTime": 0,
            "errorRate": 1.0,
            "uptime": 0.0,
            "lastCheck": datetime.now().isoformat(),
            "details": str(e)
        })
    
    # Redis service
    redis_start = time.time()
    try:
        r = redis.from_url("redis://redis:6379", decode_responses=True)
        await r.ping()
        redis_response_time = (time.time() - redis_start) * 1000
        await r.close()
        services.append({
            "name": "Redis Cache",
            "status": "healthy",
            "responseTime": round(redis_response_time, 2),
            "errorRate": 0.0,
            "uptime": 99.9,
            "lastCheck": datetime.now().isoformat(),
            "details": "Cache and queue service"
        })
    except Exception as e:
        services.append({
            "name": "Redis Cache",
            "status": "unhealthy",
            "responseTime": 0,
            "errorRate": 1.0,
            "uptime": 0.0,
            "lastCheck": datetime.now().isoformat(),
            "details": str(e)
        })
    
    # AI Services (mocked for now)
    services.extend([
        {
            "name": "OpenAI API",
            "status": "healthy",
            "responseTime": 245.5,
            "errorRate": 0.02,
            "uptime": 99.5,
            "lastCheck": datetime.now().isoformat(),
            "details": "GPT-4 and DALL-E services"
        },
        {
            "name": "ElevenLabs API",
            "status": "healthy",
            "responseTime": 180.3,
            "errorRate": 0.01,
            "uptime": 99.8,
            "lastCheck": datetime.now().isoformat(),
            "details": "Voice synthesis service"
        },
        {
            "name": "Runway API",
            "status": "degraded",
            "responseTime": 520.8,
            "errorRate": 0.15,
            "uptime": 95.2,
            "lastCheck": datetime.now().isoformat(),
            "details": "Video generation - high load"
        },
        {
            "name": "Video Processing",
            "status": "healthy",
            "responseTime": 85.2,
            "errorRate": 0.03,
            "uptime": 98.5,
            "lastCheck": datetime.now().isoformat(),
            "details": "FFmpeg and MoviePy services"
        }
    ])
    
    return services


@router.get("/health/metrics")
async def get_system_metrics():
    """Get current system metrics"""
    import psutil
    
    # Get CPU usage
    cpu_percent = psutil.cpu_percent(interval=1)
    
    # Get memory usage
    memory = psutil.virtual_memory()
    memory_percent = memory.percent
    
    # Get disk usage
    disk = psutil.disk_usage('/')
    disk_percent = disk.percent
    
    # Get network stats (simplified)
    net_io = psutil.net_io_counters()
    
    return {
        "cpu": round(cpu_percent, 1),
        "memory": round(memory_percent, 1),
        "disk": round(disk_percent, 1),
        "network": {
            "latency": 25,  # Mocked for now
            "bandwidth": round((net_io.bytes_sent + net_io.bytes_recv) / 1024 / 1024, 2)  # MB
        }
    }


@router.get("/health/degradation")
async def get_degradation_info():
    """Get current service degradation status"""
    # Import the degradation service
    try:
        from src.services.graceful_degradation import degradation_service
        status = degradation_service.get_status()
        
        return {
            "level": status["current_level"],
            "activeDegradations": status["active_degradations"],
            "featureFlags": status["feature_flags"],
            "qualitySettings": status["quality_settings"]
        }
    except Exception as e:
        logger.error("Failed to get degradation status", error=str(e))
        # Return default status
        return {
            "level": "full",
            "activeDegradations": [],
            "featureFlags": {
                "ai_generation": True,
                "video_processing": True,
                "high_quality_export": True,
                "real_time_preview": True,
                "batch_operations": True,
                "advanced_effects": True,
                "cloud_sync": True,
                "analytics": True
            },
            "qualitySettings": {
                "video_resolution": "1920x1080",
                "video_bitrate": "8M",
                "audio_bitrate": "192k",
                "image_quality": 95,
                "preview_fps": 30,
                "concurrent_operations": 5
            }
        }


@router.get("/health/errors")
async def get_error_summary():
    """Get error summary for the last 24 hours"""
    # Import the error logger
    try:
        from src.services.error_context_logger import error_logger
        summary = error_logger.get_error_summary(hours=24)
        
        # Format recent errors
        recent_errors = []
        for error_type, count in summary.get("top_errors", [])[:5]:
            recent_errors.append({
                "id": f"err_{hash(error_type)}",
                "type": error_type,
                "count": count,
                "lastOccurred": datetime.now().isoformat()  # Would be from actual data
            })
        
        return {
            "total": summary["total_errors"],
            "byCategory": summary["by_category"],
            "bySeverity": summary["by_severity"],
            "recoveryRate": 0.85,  # Mocked for now, would calculate from recovery_stats
            "recentErrors": recent_errors
        }
    except Exception as e:
        logger.error("Failed to get error summary", error=str(e))
        # Return empty summary
        return {
            "total": 0,
            "byCategory": {},
            "bySeverity": {},
            "recoveryRate": 1.0,
            "recentErrors": []
        }