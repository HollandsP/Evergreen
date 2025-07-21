"""
Video generation endpoints
"""
import uuid
from typing import Annotated, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import redis.asyncio as redis
import structlog
import asyncio
import json
import os

from src.core.config import settings
from src.core.database.connection import get_db
from src.core.database.models import Project, GenerationJob, User
from api.dependencies import (
    get_current_user,
    get_redis,
    check_project_ownership,
    rate_limit_per_hour
)
from api.validators import (
    GenerationRequest,
    GenerationResponse,
    GenerationProgressResponse,
    GenerationStatus,
    ProjectStatus,
)
from workers.tasks.video_generation import process_video_generation

router = APIRouter(prefix="/generation", tags=["generation"])
logger = structlog.get_logger()


async def check_generation_limits(
    user: User,
    redis_client: redis.Redis
) -> None:
    """Check user's generation limits"""
    # Check monthly generation limit
    monthly_key = f"generation_limit:monthly:{user.id}:{datetime.utcnow().strftime('%Y-%m')}"
    monthly_count = await redis_client.get(monthly_key)
    
    if monthly_count and int(monthly_count) >= 100:  # 100 videos per month
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Monthly generation limit exceeded (100 videos)"
        )
    
    # Check concurrent generation limit
    concurrent_key = f"generation_concurrent:{user.id}"
    concurrent_count = await redis_client.get(concurrent_key)
    
    if concurrent_count and int(concurrent_count) >= 3:  # 3 concurrent generations
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Maximum concurrent generations reached (3)"
        )


@router.post("/", response_model=GenerationResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_generation(
    request: GenerationRequest,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    redis_client: Annotated[redis.Redis, Depends(get_redis)],
    _: Annotated[None, Depends(rate_limit_per_hour)]
) -> GenerationResponse:
    """
    Start video generation for a project
    
    Initiates the video generation process which includes:
    - Script parsing and validation
    - Voice synthesis
    - Visual generation
    - Video assembly
    
    The process runs asynchronously and progress can be tracked via the status endpoint.
    """
    # Check generation limits
    await check_generation_limits(current_user, redis_client)
    
    # Get project
    result = await db.execute(
        select(Project).where(
            Project.id == request.project_id,
            Project.user_id == current_user.id
        )
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check project status
    if project.status == ProjectStatus.PROCESSING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project is already being processed"
        )
    
    # Create generation job
    job_id = str(uuid.uuid4())
    generation_job = GenerationJob(
        id=job_id,
        project_id=project.id,
        user_id=current_user.id,
        status=GenerationStatus.PENDING,
        progress=0.0,
        metadata={
            "quality": request.quality,
            "priority": request.priority,
            "webhook_url": request.webhook_url,
            "requested_at": datetime.utcnow().isoformat()
        }
    )
    
    db.add(generation_job)
    
    # Update project status
    project.status = ProjectStatus.PROCESSING
    
    await db.commit()
    
    # Update Redis counters
    monthly_key = f"generation_limit:monthly:{current_user.id}:{datetime.utcnow().strftime('%Y-%m')}"
    await redis_client.incr(monthly_key)
    await redis_client.expire(monthly_key, 31 * 24 * 3600)  # Expire after 31 days
    
    concurrent_key = f"generation_concurrent:{current_user.id}"
    await redis_client.incr(concurrent_key)
    await redis_client.expire(concurrent_key, 24 * 3600)  # Expire after 24 hours
    
    # Queue generation task
    try:
        # Prepare task arguments
        story_file = project.script_content  # Use script content from project
        generation_settings = {
            "voice_type": project.voice_type,
            "style": project.style,
            "quality": request.quality,
            "priority": request.priority,
            "project_name": project.name,
            "webhook_url": request.webhook_url
        }
        
        # Send to Celery queue
        process_video_generation.apply_async(
            args=[job_id, story_file, generation_settings],
            priority=request.priority,
            queue='video'
        )
        
        logger.info(
            "Video generation started",
            user_id=str(current_user.id),
            project_id=str(project.id),
            job_id=job_id,
            quality=request.quality,
            priority=request.priority
        )
        
    except Exception as e:
        logger.error(
            "Failed to queue generation task",
            user_id=str(current_user.id),
            project_id=str(project.id),
            job_id=job_id,
            error=str(e),
            exc_info=True
        )
        
        # Rollback job creation
        generation_job.status = GenerationStatus.FAILED
        generation_job.error = str(e)
        project.status = ProjectStatus.FAILED
        await db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start generation process"
        )
    
    # Calculate estimated completion
    metadata = project.project_metadata or {}  # Use project_metadata field 
    estimated_duration = metadata.get("estimated_duration", 300)  # Default 5 minutes
    estimated_completion = datetime.utcnow() + timedelta(seconds=estimated_duration)
    
    return GenerationResponse(
        job_id=job_id,
        project_id=str(project.id),
        status=GenerationStatus.PENDING,
        progress=0.0,
        message="Video generation queued successfully",
        estimated_completion=estimated_completion,
        created_at=generation_job.created_at,
        updated_at=generation_job.updated_at
    )


@router.get("/{job_id}/status", response_model=GenerationProgressResponse)
async def get_generation_status(
    job_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    redis_client: Annotated[redis.Redis, Depends(get_redis)]
) -> GenerationProgressResponse:
    """
    Get video generation job status
    
    Returns detailed progress information including:
    - Current status and progress percentage
    - Current processing step
    - Any error messages
    - Video URL if completed
    """
    # Get job from database
    result = await db.execute(
        select(GenerationJob).where(
            GenerationJob.id == job_id,
            GenerationJob.user_id == current_user.id
        )
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generation job not found"
        )
    
    # Get real-time progress from Redis
    progress_key = f"generation_progress:{job_id}"
    progress_data = await redis_client.get(progress_key)
    
    if progress_data:
        progress_info = json.loads(progress_data)
    else:
        progress_info = {
            "current_step": "Queued",
            "steps_completed": 0,
            "total_steps": 5,
            "messages": []
        }
    
    # Get video URL if completed
    video_url = None
    if job.status == GenerationStatus.COMPLETED and job.output_url:
        video_url = f"/api/v1/generation/{job_id}/download"
    
    return GenerationProgressResponse(
        job_id=job_id,
        status=job.status,
        progress=job.progress,
        current_step=progress_info.get("current_step"),
        steps_completed=progress_info.get("steps_completed", 0),
        total_steps=progress_info.get("total_steps", 5),
        messages=progress_info.get("messages", []),
        video_url=video_url,
        error=job.error
    )


@router.get("/{job_id}/download")
async def download_generated_video(
    job_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> FileResponse:
    """
    Download completed video
    
    Returns the generated video file for completed jobs.
    The video will be in MP4 format with H.264 encoding.
    """
    # Get job
    result = await db.execute(
        select(GenerationJob).where(
            GenerationJob.id == job_id,
            GenerationJob.user_id == current_user.id
        )
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generation job not found"
        )
    
    if job.status != GenerationStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Video not ready. Current status: {job.status}"
        )
    
    if not job.output_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video file not found"
        )
    
    # Check if file exists
    if not os.path.exists(job.output_url):
        logger.error(
            "Generated video file not found",
            job_id=job_id,
            file_path=job.output_url
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video file not found on server"
        )
    
    # Get project name for filename
    project_result = await db.execute(
        select(Project).where(Project.id == job.project_id)
    )
    project = project_result.scalar_one()
    
    filename = f"{project.name.replace(' ', '_')}_{job_id[:8]}.mp4"
    
    logger.info(
        "Video download requested",
        user_id=str(current_user.id),
        job_id=job_id,
        filename=filename
    )
    
    return FileResponse(
        path=job.output_url,
        media_type="video/mp4",
        filename=filename,
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.post("/{job_id}/cancel")
async def cancel_generation(
    job_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    redis_client: Annotated[redis.Redis, Depends(get_redis)]
) -> dict:
    """
    Cancel a video generation job
    
    Cancels a pending or processing generation job.
    Completed jobs cannot be cancelled.
    """
    # Get job
    result = await db.execute(
        select(GenerationJob).where(
            GenerationJob.id == job_id,
            GenerationJob.user_id == current_user.id
        )
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generation job not found"
        )
    
    if job.status in [GenerationStatus.COMPLETED, GenerationStatus.FAILED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel job with status: {job.status}"
        )
    
    # Update job status
    job.status = GenerationStatus.FAILED
    job.error = "Cancelled by user"
    job.updated_at = datetime.utcnow()
    
    # Update project status
    project_result = await db.execute(
        select(Project).where(Project.id == job.project_id)
    )
    project = project_result.scalar_one()
    project.status = ProjectStatus.DRAFT
    
    await db.commit()
    
    # Update Redis
    concurrent_key = f"generation_concurrent:{current_user.id}"
    await redis_client.decr(concurrent_key)
    
    # Set cancellation flag in Redis for worker
    cancel_key = f"generation_cancel:{job_id}"
    await redis_client.set(cancel_key, "1", ex=3600)  # Expire after 1 hour
    
    logger.info(
        "Generation job cancelled",
        user_id=str(current_user.id),
        job_id=job_id
    )
    
    return {
        "message": "Generation job cancelled successfully",
        "job_id": job_id
    }


@router.get("/limits")
async def get_generation_limits(
    current_user: Annotated[User, Depends(get_current_user)],
    redis_client: Annotated[redis.Redis, Depends(get_redis)]
) -> dict:
    """
    Get user's generation limits and usage
    
    Returns information about:
    - Monthly generation limit and current usage
    - Concurrent generation limit and active jobs
    - Reset dates
    """
    # Get monthly usage
    monthly_key = f"generation_limit:monthly:{current_user.id}:{datetime.utcnow().strftime('%Y-%m')}"
    monthly_count = await redis_client.get(monthly_key)
    monthly_used = int(monthly_count) if monthly_count else 0
    
    # Get concurrent usage
    concurrent_key = f"generation_concurrent:{current_user.id}"
    concurrent_count = await redis_client.get(concurrent_key)
    concurrent_used = int(concurrent_count) if concurrent_count else 0
    
    # Calculate reset date (first day of next month)
    now = datetime.utcnow()
    if now.month == 12:
        reset_date = datetime(now.year + 1, 1, 1)
    else:
        reset_date = datetime(now.year, now.month + 1, 1)
    
    return {
        "monthly": {
            "limit": 100,
            "used": monthly_used,
            "remaining": max(0, 100 - monthly_used),
            "reset_date": reset_date.isoformat()
        },
        "concurrent": {
            "limit": 3,
            "used": concurrent_used,
            "remaining": max(0, 3 - concurrent_used)
        }
    }