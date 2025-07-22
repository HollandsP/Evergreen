"""
Refactored Video Generation Task

Uses the new orchestrator-based architecture with proper separation of concerns,
error handling, and resource management.
"""

import asyncio
from typing import Dict, Any
from celery import Task

from workers.celery_app import app
from src.services.video_generation_orchestrator import VideoGenerationOrchestrator

import structlog

logger = structlog.get_logger()


class VideoGenerationTaskV2(Task):
    """Base class for video generation tasks with improved architecture."""
    name = "video_generation.process_v2"
    max_retries = 3
    default_retry_delay = 60


@app.task(bind=True, base=VideoGenerationTaskV2, name="video_generation.process_v2")
def process_video_generation_v2(self, job_id: str, story_file: str, settings: dict):
    """
    Enhanced video generation task using orchestrator pattern.
    
    Args:
        job_id: Unique job identifier
        story_file: Script content string
        settings: Generation settings (voice, style, quality)
    """
    logger.info(
        "Starting enhanced video generation",
        job_id=job_id,
        story_content_length=len(story_file) if isinstance(story_file, str) else "unknown",
        settings=settings
    )
    
    try:
        # Run the async orchestrator
        result = asyncio.run(_run_orchestrated_generation(job_id, story_file, settings))
        
        logger.info("Enhanced video generation completed successfully", result=result)
        return result
        
    except Exception as e:
        logger.error(
            "Enhanced video generation failed",
            job_id=job_id,
            error=str(e),
            exc_info=True
        )
        
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


async def _run_orchestrated_generation(job_id: str, script_content: str, 
                                     settings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the orchestrated video generation pipeline.
    
    Args:
        job_id: Unique job identifier
        script_content: Script content to process
        settings: Generation settings
        
    Returns:
        Generation result with job status and artifacts
    """
    # Initialize orchestrator
    orchestrator = VideoGenerationOrchestrator()
    
    # Add job_id to settings for tracking
    settings = {**settings, 'job_id': job_id}
    
    try:
        # Run the full generation pipeline
        result = await orchestrator.generate_video(job_id, script_content, settings)
        return result
        
    except Exception as e:
        logger.error(
            "Orchestrated generation failed",
            job_id=job_id,
            error=str(e),
            exc_info=True
        )
        raise


@app.task(name="video_generation.get_status_v2")  
def get_generation_status_v2(job_id: str) -> dict:
    """
    Get status of video generation job.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Job status information
    """
    try:
        # This would typically use a persistent store like Redis
        # For now, create temporary orchestrator to check status
        orchestrator = VideoGenerationOrchestrator()
        status = orchestrator.get_job_status(job_id)
        
        if status:
            return status
        else:
            return {
                'job_id': job_id,
                'status': 'not_found',
                'error': 'Job not found'
            }
            
    except Exception as e:
        logger.error("Failed to get job status", job_id=job_id, error=str(e))
        return {
            'job_id': job_id,
            'status': 'error',
            'error': str(e)
        }


@app.task(name="video_generation.cancel_v2")
def cancel_generation_v2(job_id: str) -> dict:
    """
    Cancel video generation job.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Cancellation result
    """
    try:
        orchestrator = VideoGenerationOrchestrator()
        success = asyncio.run(orchestrator.cancel_job(job_id))
        
        return {
            'job_id': job_id,
            'cancelled': success,
            'message': 'Job cancelled successfully' if success else 'Job not found or already completed'
        }
        
    except Exception as e:
        logger.error("Failed to cancel job", job_id=job_id, error=str(e))
        return {
            'job_id': job_id,
            'cancelled': False,
            'error': str(e)
        }


@app.task(name="video_generation.health_check_v2")
def health_check_v2() -> dict:
    """
    Check health of video generation services.
    
    Returns:
        Health status of all services
    """
    try:
        orchestrator = VideoGenerationOrchestrator()
        health_status = orchestrator.get_health_status()
        
        return {
            'status': 'healthy',
            'timestamp': time.time(),
            'services': health_status
        }
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': time.time()
        }


# Keep original task for backward compatibility
@app.task(bind=True, name="video_generation.process")
def process_video_generation_legacy(self, job_id: str, story_file: str, settings: dict):
    """
    Legacy video generation task - delegates to new implementation.
    
    This provides backward compatibility while using the new architecture.
    """
    logger.info("Legacy task called, delegating to enhanced implementation", job_id=job_id)
    
    # Add migration flag to settings
    settings = {**settings, '_migrated_from_legacy': True}
    
    # Delegate to new implementation
    return process_video_generation_v2(job_id, story_file, settings)