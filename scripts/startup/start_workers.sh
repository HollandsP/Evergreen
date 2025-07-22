#!/bin/bash

# Start Celery workers for AI Content Generation Pipeline

set -e

echo "Starting Celery workers..."

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "Error: Redis is not running. Please start Redis first."
    exit 1
fi

# Check if RabbitMQ is running (or use Redis as broker)
if [ -z "$RABBITMQ_URL" ]; then
    echo "Using Redis as message broker"
    export CELERY_BROKER_URL=${REDIS_URL:-redis://localhost:6379/0}
else
    echo "Using RabbitMQ as message broker"
    export CELERY_BROKER_URL=$RABBITMQ_URL
fi

# Create necessary directories
mkdir -p output/projects
mkdir -p output/temp
mkdir -p logs

# Function to start a worker
start_worker() {
    local queue=$1
    local concurrency=$2
    local name=$3
    
    echo "Starting $name worker for queue: $queue"
    celery -A workers.celery_app worker \
        --loglevel=info \
        --queues=$queue \
        --concurrency=$concurrency \
        --hostname=$name@%h \
        --logfile=logs/celery-$name.log \
        --detach
}

# Start workers
start_worker "script" 4 "script-worker"
start_worker "voice" 2 "voice-worker"
start_worker "video" 1 "video-worker"
start_worker "assembly" 2 "assembly-worker"

# Start Celery Beat scheduler
echo "Starting Celery Beat scheduler..."
celery -A workers.celery_app beat \
    --loglevel=info \
    --logfile=logs/celery-beat.log \
    --detach

# Start Flower monitoring (optional)
if [ "$START_FLOWER" = "true" ]; then
    echo "Starting Flower monitoring..."
    celery -A workers.celery_app flower \
        --port=${FLOWER_PORT:-5555} \
        --basic_auth=${FLOWER_BASIC_AUTH:-admin:password} \
        --logfile=logs/flower.log &
fi

echo "All workers started successfully!"
echo ""
echo "You can monitor workers at:"
echo "  - Flower UI: http://localhost:5555 (if enabled)"
echo "  - Logs: ./logs/"
echo ""
echo "To stop all workers, run: ./scripts/stop_workers.sh"