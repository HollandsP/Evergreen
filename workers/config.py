"""
Celery configuration module for AI Content Generation Pipeline.
"""

import os
from typing import Dict, Any
from kombu import Queue, Exchange
from datetime import timedelta

# Get configuration from environment
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
RABBITMQ_URL = os.getenv('RABBITMQ_URL', 'amqp://guest:guest@localhost:5672//')

# Use RabbitMQ as broker and Redis as result backend
CELERY_CONFIG: Dict[str, Any] = {
    # Broker settings
    'broker_url': RABBITMQ_URL,
    'broker_connection_retry_on_startup': True,
    
    # Result backend
    'result_backend': REDIS_URL,
    'result_expires': 3600,  # 1 hour
    'result_persistent': True,
    
    # Task settings
    'task_serializer': 'json',
    'result_serializer': 'json',
    'accept_content': ['json'],
    'timezone': 'UTC',
    'enable_utc': True,
    
    # Task execution settings
    'task_acks_late': True,
    'task_reject_on_worker_lost': True,
    'task_default_retry_delay': 30,  # 30 seconds
    'task_max_retries': 3,
    
    # Worker settings
    'worker_prefetch_multiplier': 4,
    'worker_max_tasks_per_child': 1000,
    'worker_disable_rate_limits': False,
    
    # Task routing
    'task_default_queue': 'default',
    'task_default_exchange': 'default',
    'task_default_exchange_type': 'direct',
    'task_default_routing_key': 'default',
    
    # Queue configuration
    'task_queues': (
        # Script parsing queue - high priority, fast processing
        Queue('script', Exchange('script'), routing_key='script.#',
              queue_arguments={'x-max-priority': 10}),
        
        # Voice synthesis queue - medium priority
        Queue('voice', Exchange('voice'), routing_key='voice.#',
              queue_arguments={'x-max-priority': 5}),
        
        # Video generation queue - low priority, resource intensive
        Queue('video', Exchange('video'), routing_key='video.#',
              queue_arguments={'x-max-priority': 3}),
        
        # Assembly queue - medium priority
        Queue('assembly', Exchange('assembly'), routing_key='assembly.#',
              queue_arguments={'x-max-priority': 5}),
        
        # Default queue
        Queue('default', Exchange('default'), routing_key='default'),
    ),
    
    # Task routes
    'task_routes': {
        'workers.tasks.script_tasks.*': {
            'queue': 'script',
            'routing_key': 'script.parse'
        },
        'workers.tasks.voice_tasks.*': {
            'queue': 'voice',
            'routing_key': 'voice.synthesis'
        },
        'workers.tasks.video_tasks.*': {
            'queue': 'video',
            'routing_key': 'video.generation'
        },
        'workers.tasks.assembly_tasks.*': {
            'queue': 'assembly',
            'routing_key': 'assembly.media'
        },
    },
    
    # Beat schedule for periodic tasks
    'beat_schedule': {
        'cleanup-expired-jobs': {
            'task': 'workers.tasks.maintenance.cleanup_expired_jobs',
            'schedule': timedelta(hours=1),
        },
        'monitor-worker-health': {
            'task': 'workers.tasks.maintenance.monitor_worker_health',
            'schedule': timedelta(minutes=5),
        },
    },
    
    # Task annotations for specific retry configurations
    'task_annotations': {
        'workers.tasks.voice_tasks.synthesize_voice': {
            'max_retries': 5,
            'default_retry_delay': 60,
        },
        'workers.tasks.video_tasks.generate_video': {
            'max_retries': 3,
            'default_retry_delay': 120,
            'time_limit': 3600,  # 1 hour hard limit
            'soft_time_limit': 3000,  # 50 minutes soft limit
        },
    },
}

# Flower monitoring configuration
FLOWER_CONFIG = {
    'port': int(os.getenv('FLOWER_PORT', '5555')),
    'broker_api': RABBITMQ_URL,
    'basic_auth': os.getenv('FLOWER_BASIC_AUTH', 'admin:password').split(':'),
}

# Exponential backoff configuration
RETRY_BACKOFF_CONFIG = {
    'max_delay': 600,  # Maximum 10 minutes
    'base': 2,  # Exponential base
    'jitter': True,  # Add random jitter to prevent thundering herd
}