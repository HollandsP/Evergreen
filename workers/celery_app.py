"""
Main Celery application configuration for AI Content Generation Pipeline.
"""

import os
import logging
from celery import Celery, signals
from celery.utils.log import get_task_logger
from .config import CELERY_CONFIG

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = get_task_logger(__name__)

# Create Celery instance
app = Celery('evergreen')

# Load configuration
app.config_from_object(CELERY_CONFIG)

# Auto-discover tasks
app.autodiscover_tasks([
    'workers.tasks.video_generation',
])

# Signal handlers for worker events
@signals.worker_init.connect
def setup_worker_logging(**kwargs):
    """Configure logging when worker starts."""
    logging.getLogger('celery').setLevel(logging.INFO)
    logging.getLogger('celery.task').setLevel(logging.INFO)
    logger.info("Worker initialized with configuration")

@signals.task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kw):
    """Log task execution start."""
    logger.info(f"Task {task.name} [{task_id}] started with args: {args}, kwargs: {kwargs}")

@signals.task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, 
                        retval=None, state=None, **kw):
    """Log task execution completion."""
    logger.info(f"Task {task.name} [{task_id}] completed with state: {state}")

@signals.task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, args=None, 
                        kwargs=None, traceback=None, einfo=None, **kw):
    """Log task failures with full traceback."""
    logger.error(f"Task {sender.name} [{task_id}] failed with exception: {exception}")
    logger.error(f"Traceback: {traceback}")

@signals.task_retry.connect
def task_retry_handler(sender=None, task_id=None, reason=None, **kw):
    """Log task retry attempts."""
    logger.warning(f"Task {sender.name} [{task_id}] retrying. Reason: {reason}")

# Health check task
@app.task(name='workers.health_check')
def health_check():
    """Simple health check task for monitoring."""
    return {'status': 'healthy', 'worker': 'online'}

if __name__ == '__main__':
    app.start()