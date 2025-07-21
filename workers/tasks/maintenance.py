"""
Maintenance and monitoring tasks for Celery workers.
"""

import os
import json
import redis
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from celery import Task
from celery.utils.log import get_task_logger
from sqlalchemy.orm import Session
from workers.celery_app import app
from src.core.database.connection import get_db
from src.core.database.models import Job, JobStatus

logger = get_task_logger(__name__)

# Redis client for worker health monitoring
redis_client = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))

@app.task(name='workers.tasks.maintenance.cleanup_expired_jobs')
def cleanup_expired_jobs(days_to_keep: int = 7) -> Dict[str, Any]:
    """
    Clean up expired jobs and their associated files.
    
    Args:
        days_to_keep: Number of days to keep completed/failed jobs
    
    Returns:
        Cleanup statistics
    """
    logger.info(f"Starting cleanup of jobs older than {days_to_keep} days")
    
    db: Session = next(get_db())
    stats = {
        'jobs_deleted': 0,
        'files_deleted': 0,
        'space_freed_mb': 0
    }
    
    try:
        # Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Find expired jobs
        expired_jobs = db.query(Job).filter(
            Job.completed_at < cutoff_date,
            Job.status.in_([JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED])
        ).all()
        
        for job in expired_jobs:
            # Clean up associated files
            job_dir = f"/mnt/c/Users/holla/OneDrive/Desktop/CodeProjects/Evergreen/output/projects/{job.id}"
            if os.path.exists(job_dir):
                space_freed = cleanup_directory(job_dir)
                stats['space_freed_mb'] += space_freed / (1024 * 1024)
                stats['files_deleted'] += 1
            
            # Clean up Redis data
            cleanup_redis_data(job.id)
            
            # Delete job from database
            db.delete(job)
            stats['jobs_deleted'] += 1
        
        db.commit()
        
        logger.info(f"Cleanup completed: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

@app.task(name='workers.tasks.maintenance.monitor_worker_health')
def monitor_worker_health() -> Dict[str, Any]:
    """
    Monitor health of all Celery workers.
    
    Returns:
        Worker health status
    """
    logger.info("Monitoring worker health")
    
    try:
        # Get worker stats from Celery
        inspector = app.control.inspect()
        
        # Get active workers
        active_workers = inspector.active()
        registered_tasks = inspector.registered()
        stats = inspector.stats()
        
        health_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'workers': {},
            'summary': {
                'total_workers': 0,
                'active_tasks': 0,
                'healthy_workers': 0,
                'unhealthy_workers': 0
            }
        }
        
        if active_workers:
            for worker_name, tasks in active_workers.items():
                worker_stats = stats.get(worker_name, {}) if stats else {}
                
                worker_health = {
                    'name': worker_name,
                    'active_tasks': len(tasks),
                    'registered_tasks': len(registered_tasks.get(worker_name, [])),
                    'total_tasks': worker_stats.get('total', 0),
                    'status': 'healthy' if len(tasks) < 100 else 'overloaded',
                    'last_heartbeat': datetime.utcnow().isoformat()
                }
                
                health_data['workers'][worker_name] = worker_health
                health_data['summary']['total_workers'] += 1
                health_data['summary']['active_tasks'] += len(tasks)
                
                if worker_health['status'] == 'healthy':
                    health_data['summary']['healthy_workers'] += 1
                else:
                    health_data['summary']['unhealthy_workers'] += 1
        
        # Store health data in Redis
        redis_client.setex(
            'worker:health:latest',
            300,  # 5 minutes
            json.dumps(health_data)
        )
        
        # Alert if issues detected
        if health_data['summary']['unhealthy_workers'] > 0:
            send_health_alert(health_data)
        
        logger.info(f"Worker health check completed: {health_data['summary']}")
        return health_data
        
    except Exception as e:
        logger.error(f"Error monitoring worker health: {str(e)}")
        return {
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }

@app.task(name='workers.tasks.maintenance.cleanup_temp_files')
def cleanup_temp_files(hours_old: int = 24) -> Dict[str, Any]:
    """
    Clean up temporary files older than specified hours.
    
    Args:
        hours_old: Age threshold in hours
    
    Returns:
        Cleanup statistics
    """
    logger.info(f"Cleaning up temp files older than {hours_old} hours")
    
    temp_dir = "/mnt/c/Users/holla/OneDrive/Desktop/CodeProjects/Evergreen/output/temp"
    stats = {
        'files_deleted': 0,
        'space_freed_mb': 0
    }
    
    if not os.path.exists(temp_dir):
        return stats
    
    cutoff_time = datetime.utcnow() - timedelta(hours=hours_old)
    
    for root, dirs, files in os.walk(temp_dir):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                # Check file age
                file_stat = os.stat(file_path)
                file_time = datetime.fromtimestamp(file_stat.st_mtime)
                
                if file_time < cutoff_time:
                    file_size = file_stat.st_size
                    os.unlink(file_path)
                    stats['files_deleted'] += 1
                    stats['space_freed_mb'] += file_size / (1024 * 1024)
                    
            except Exception as e:
                logger.error(f"Error deleting file {file_path}: {str(e)}")
    
    logger.info(f"Temp file cleanup completed: {stats}")
    return stats

@app.task(name='workers.tasks.maintenance.optimize_redis')
def optimize_redis() -> Dict[str, Any]:
    """
    Optimize Redis by cleaning up expired keys and running memory optimization.
    
    Returns:
        Optimization statistics
    """
    logger.info("Starting Redis optimization")
    
    stats = {
        'keys_before': redis_client.dbsize(),
        'memory_before_mb': 0,
        'keys_after': 0,
        'memory_after_mb': 0,
        'keys_deleted': 0
    }
    
    try:
        # Get memory info
        memory_info = redis_client.info('memory')
        stats['memory_before_mb'] = memory_info.get('used_memory', 0) / (1024 * 1024)
        
        # Clean up expired progress keys
        progress_pattern = 'job:progress:*'
        for key in redis_client.scan_iter(match=progress_pattern):
            # Check if key has TTL, if not set one
            ttl = redis_client.ttl(key)
            if ttl == -1:  # No expiration
                redis_client.expire(key, 86400)  # 24 hours
        
        # Clean up old metrics
        metrics_pattern = 'metrics:*'
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        
        for key in redis_client.scan_iter(match=metrics_pattern):
            # Extract date from key if possible
            try:
                key_str = key.decode() if isinstance(key, bytes) else key
                if cutoff_date.date().isoformat() in key_str:
                    continue
                
                # Check age of entries in the list
                entries = redis_client.lrange(key, 0, 0)
                if entries:
                    first_entry = json.loads(entries[0])
                    entry_time = datetime.fromisoformat(first_entry.get('timestamp'))
                    if entry_time < cutoff_date:
                        redis_client.delete(key)
                        stats['keys_deleted'] += 1
                        
            except Exception as e:
                logger.error(f"Error processing key {key}: {str(e)}")
        
        # Run Redis memory optimization
        redis_client.memory_purge()
        
        # Get final stats
        stats['keys_after'] = redis_client.dbsize()
        memory_info = redis_client.info('memory')
        stats['memory_after_mb'] = memory_info.get('used_memory', 0) / (1024 * 1024)
        stats['memory_saved_mb'] = stats['memory_before_mb'] - stats['memory_after_mb']
        
        logger.info(f"Redis optimization completed: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Error optimizing Redis: {str(e)}")
        raise

@app.task(name='workers.tasks.maintenance.generate_usage_report')
def generate_usage_report(days: int = 30) -> Dict[str, Any]:
    """
    Generate usage report for the specified period.
    
    Args:
        days: Number of days to include in report
    
    Returns:
        Usage statistics
    """
    logger.info(f"Generating usage report for last {days} days")
    
    db: Session = next(get_db())
    report = {
        'period_days': days,
        'start_date': (datetime.utcnow() - timedelta(days=days)).isoformat(),
        'end_date': datetime.utcnow().isoformat(),
        'jobs': {
            'total': 0,
            'completed': 0,
            'failed': 0,
            'cancelled': 0,
            'processing': 0
        },
        'processing_time': {
            'total_hours': 0,
            'average_minutes': 0
        },
        'by_type': {},
        'daily_stats': []
    }
    
    try:
        # Get jobs for the period
        start_date = datetime.utcnow() - timedelta(days=days)
        jobs = db.query(Job).filter(Job.created_at >= start_date).all()
        
        report['jobs']['total'] = len(jobs)
        
        total_processing_time = timedelta()
        
        for job in jobs:
            # Count by status
            if job.status == JobStatus.COMPLETED:
                report['jobs']['completed'] += 1
            elif job.status == JobStatus.FAILED:
                report['jobs']['failed'] += 1
            elif job.status == JobStatus.CANCELLED:
                report['jobs']['cancelled'] += 1
            elif job.status == JobStatus.PROCESSING:
                report['jobs']['processing'] += 1
            
            # Count by type
            job_type = job.type
            if job_type not in report['by_type']:
                report['by_type'][job_type] = {
                    'count': 0,
                    'completed': 0,
                    'failed': 0
                }
            
            report['by_type'][job_type]['count'] += 1
            if job.status == JobStatus.COMPLETED:
                report['by_type'][job_type]['completed'] += 1
            elif job.status == JobStatus.FAILED:
                report['by_type'][job_type]['failed'] += 1
            
            # Calculate processing time
            if job.completed_at and job.created_at:
                processing_time = job.completed_at - job.created_at
                total_processing_time += processing_time
        
        # Calculate averages
        if report['jobs']['total'] > 0:
            avg_processing_seconds = total_processing_time.total_seconds() / report['jobs']['total']
            report['processing_time']['average_minutes'] = avg_processing_seconds / 60
            report['processing_time']['total_hours'] = total_processing_time.total_seconds() / 3600
        
        # Generate daily stats
        for i in range(days):
            date = datetime.utcnow() - timedelta(days=i)
            daily_jobs = [j for j in jobs if j.created_at.date() == date.date()]
            
            daily_stat = {
                'date': date.date().isoformat(),
                'total': len(daily_jobs),
                'completed': sum(1 for j in daily_jobs if j.status == JobStatus.COMPLETED),
                'failed': sum(1 for j in daily_jobs if j.status == JobStatus.FAILED)
            }
            
            report['daily_stats'].append(daily_stat)
        
        # Store report in Redis
        redis_client.setex(
            f'usage_report:{datetime.utcnow().date().isoformat()}',
            86400 * 7,  # Keep for 7 days
            json.dumps(report)
        )
        
        logger.info(f"Usage report generated: {report['jobs']}")
        return report
        
    except Exception as e:
        logger.error(f"Error generating usage report: {str(e)}")
        raise
    finally:
        db.close()

# Helper functions
def cleanup_directory(directory: str) -> int:
    """
    Recursively delete directory and return space freed in bytes.
    """
    total_size = 0
    
    for dirpath, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            try:
                total_size += os.path.getsize(filepath)
                os.unlink(filepath)
            except Exception as e:
                logger.error(f"Error deleting file {filepath}: {str(e)}")
    
    # Remove empty directories
    try:
        for dirpath, dirnames, filenames in os.walk(directory, topdown=False):
            os.rmdir(dirpath)
    except Exception as e:
        logger.error(f"Error removing directory {directory}: {str(e)}")
    
    return total_size

def cleanup_redis_data(job_id: str):
    """Clean up Redis data for a job."""
    patterns = [
        f'job:progress:{job_id}',
        f'job:status:{job_id}',
        f'job:result:{job_id}',
        f'lock:{job_id}*'
    ]
    
    for pattern in patterns:
        for key in redis_client.scan_iter(match=pattern):
            redis_client.delete(key)

def send_health_alert(health_data: Dict[str, Any]):
    """Send health alert notification."""
    # This would integrate with your notification system
    # For now, just log the alert
    logger.warning(f"Worker health alert: {health_data['summary']['unhealthy_workers']} unhealthy workers detected")
    
    # Store alert in Redis for dashboard
    alert = {
        'timestamp': datetime.utcnow().isoformat(),
        'type': 'worker_health',
        'severity': 'warning',
        'message': f"{health_data['summary']['unhealthy_workers']} workers are overloaded",
        'data': health_data
    }
    
    redis_client.lpush('alerts:worker_health', json.dumps(alert))
    redis_client.ltrim('alerts:worker_health', 0, 99)  # Keep last 100 alerts