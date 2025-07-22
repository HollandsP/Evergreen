#!/bin/bash

# Stop all Celery workers

echo "Stopping Celery workers..."

# Stop all Celery workers
celery -A workers.celery_app control shutdown

# Stop Celery Beat
if pgrep -f "celery.*beat" > /dev/null; then
    echo "Stopping Celery Beat..."
    pkill -f "celery.*beat"
fi

# Stop Flower if running
if pgrep -f "celery.*flower" > /dev/null; then
    echo "Stopping Flower..."
    pkill -f "celery.*flower"
fi

echo "All workers stopped."