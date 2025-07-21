"""
Shared utilities for Celery workers.
"""

import os
import redis
import json
import logging
import random
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from functools import wraps
from celery import Task, current_task
from celery.utils.log import get_task_logger
from sqlalchemy.orm import Session
from src.core.database.connection import get_db
from src.core.database.models import Job
from api.validators import JobStatus

logger = get_task_logger(__name__)

# Redis client for progress reporting
redis_client = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))

class ProgressReporter:
    """Utility class for reporting task progress to Redis."""
    
    def __init__(self, job_id: str, total_steps: int = 100):
        self.job_id = job_id
        self.total_steps = total_steps
        self.current_step = 0
        self.redis_key = f"job:progress:{job_id}"
        
    def update(self, step: int, message: str = "", metadata: Dict[str, Any] = None):
        """Update progress for the job."""
        self.current_step = step
        progress_data = {
            'current': step,
            'total': self.total_steps,
            'percentage': round((step / self.total_steps) * 100, 2),
            'message': message,
            'updated_at': datetime.utcnow().isoformat(),
            'metadata': metadata or {}
        }
        
        # Store in Redis with 1 hour expiry
        redis_client.setex(
            self.redis_key,
            3600,
            json.dumps(progress_data)
        )
        
        # Also update Celery task state
        if current_task:
            current_task.update_state(
                state='PROGRESS',
                meta=progress_data
            )
        
        logger.info(f"Progress update for job {self.job_id}: {step}/{self.total_steps} - {message}")
        
    def complete(self, message: str = "Task completed successfully"):
        """Mark the task as complete."""
        self.update(self.total_steps, message)
        
    def get_progress(self) -> Optional[Dict[str, Any]]:
        """Get current progress from Redis."""
        data = redis_client.get(self.redis_key)
        return json.loads(data) if data else None

def update_job_status(job_id: str, status: JobStatus, error_message: str = None,
                     result_data: Dict[str, Any] = None):
    """Update job status in the database."""
    db: Session = next(get_db())
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = status
            if error_message:
                job.error_message = error_message
            if result_data:
                job.result = result_data
            if status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                job.completed_at = datetime.utcnow()
            db.commit()
            logger.info(f"Updated job {job_id} status to {status.value}")
        else:
            logger.error(f"Job {job_id} not found in database")
    except Exception as e:
        logger.error(f"Error updating job status: {str(e)}")
        db.rollback()
    finally:
        db.close()

def exponential_backoff_retry(max_retries: int = 3, base_delay: int = 1, 
                             max_delay: int = 300, jitter: bool = True):
    """
    Decorator for retry with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        jitter: Add random jitter to prevent thundering herd
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(f"Max retries ({max_retries}) exceeded for {func.__name__}")
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    
                    # Add jitter if enabled
                    if jitter:
                        delay = delay * (0.5 + random.random())
                    
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}. "
                        f"Retrying in {delay:.1f}s. Error: {str(e)}"
                    )
                    
                    import time
                    time.sleep(delay)
            
            raise last_exception
        return wrapper
    return decorator

def task_with_db_update(job_id: str):
    """
    Decorator to automatically update job status based on task execution.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Update status to processing
                update_job_status(job_id, JobStatus.PROCESSING)
                
                # Execute the task
                result = func(*args, **kwargs)
                
                # Update status to completed
                update_job_status(job_id, JobStatus.COMPLETED, result_data=result)
                
                return result
            except Exception as e:
                # Update status to failed
                update_job_status(job_id, JobStatus.FAILED, error_message=str(e))
                raise
        return wrapper
    return decorator

def chunk_list(lst: list, chunk_size: int) -> list:
    """Split a list into chunks of specified size."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def estimate_processing_time(file_size_mb: float, operation_type: str) -> int:
    """
    Estimate processing time in seconds based on file size and operation type.
    
    Args:
        file_size_mb: File size in megabytes
        operation_type: Type of operation (voice, video, assembly)
    
    Returns:
        Estimated time in seconds
    """
    # Base estimates per MB
    estimates = {
        'voice': 10,  # 10 seconds per MB for voice synthesis
        'video': 60,  # 60 seconds per MB for video generation
        'assembly': 5,  # 5 seconds per MB for assembly
        'script': 1,  # 1 second per MB for script parsing
    }
    
    base_time = estimates.get(operation_type, 10)
    return int(file_size_mb * base_time)

def get_redis_lock(key: str, timeout: int = 300) -> bool:
    """
    Acquire a Redis lock for distributed task coordination.
    
    Args:
        key: Lock key
        timeout: Lock timeout in seconds
    
    Returns:
        True if lock acquired, False otherwise
    """
    return redis_client.set(f"lock:{key}", "1", nx=True, ex=timeout)

def release_redis_lock(key: str):
    """Release a Redis lock."""
    redis_client.delete(f"lock:{key}")

class TaskMetrics:
    """Helper class for tracking task metrics."""
    
    def __init__(self, task_name: str):
        self.task_name = task_name
        self.start_time = datetime.utcnow()
        self.metrics_key = f"metrics:{task_name}:{self.start_time.date()}"
        
    def record_execution(self, success: bool, duration: float):
        """Record task execution metrics."""
        metrics = {
            'task': self.task_name,
            'timestamp': datetime.utcnow().isoformat(),
            'success': success,
            'duration': duration,
        }
        
        # Store in Redis list (keep last 1000 entries)
        redis_client.lpush(self.metrics_key, json.dumps(metrics))
        redis_client.ltrim(self.metrics_key, 0, 999)
        redis_client.expire(self.metrics_key, 86400 * 7)  # Keep for 7 days
        
    def get_stats(self) -> Dict[str, Any]:
        """Get task execution statistics."""
        entries = redis_client.lrange(self.metrics_key, 0, -1)
        if not entries:
            return {'total': 0, 'success_rate': 0, 'avg_duration': 0}
        
        metrics = [json.loads(entry) for entry in entries]
        total = len(metrics)
        successful = sum(1 for m in metrics if m['success'])
        avg_duration = sum(m['duration'] for m in metrics) / total
        
        return {
            'total': total,
            'success_rate': (successful / total) * 100,
            'avg_duration': round(avg_duration, 2),
            'last_execution': metrics[0]['timestamp'] if metrics else None
        }