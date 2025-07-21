#!/usr/bin/env python3
"""
Direct Celery task test - bypassing FastAPI
"""
import sys
import os
import asyncio
from celery import Celery

# Add the project path so we can import from the workers
sys.path.append('/mnt/c/Users/holla/OneDrive/Desktop/CodeProjects/Evergreen')

# Create Celery app to connect to the running broker
app = Celery('test')
app.config_from_object({
    'broker_url': 'redis://localhost:6380/0',
    'result_backend': 'redis://localhost:6380/0',
    'task_serializer': 'json',
    'accept_content': ['json'],
    'result_serializer': 'json',
    'timezone': 'UTC',
    'enable_utc': True,
})

def test_celery_connection():
    """Test if we can connect to Celery"""
    try:
        # Try to inspect the workers
        inspect = app.control.inspect()
        stats = inspect.stats()
        if stats:
            print("✅ Celery workers detected:")
            for worker, info in stats.items():
                print(f"   • {worker}: {info.get('broker', {}).get('transport', 'unknown')} transport")
            return True
        else:
            print("❌ No Celery workers found")
            return False
    except Exception as e:
        print(f"❌ Celery connection failed: {e}")
        return False

def test_task_submission():
    """Test submitting a simple task"""
    try:
        # Try to send a simple task that should exist
        result = app.send_task('workers.tasks.test_task', args=['Hello from direct test'])
        print(f"✅ Task submitted: {result.id}")
        print(f"   Task state: {result.state}")
        return True
    except Exception as e:
        print(f"❌ Task submission failed: {e}")
        return False

def main():
    print("🔧 Testing Direct Celery Connection")
    print("=" * 40)
    
    print("\n1. Testing Celery worker connection...")
    if not test_celery_connection():
        print("\n❌ Cannot connect to Celery workers")
        print("   Make sure workers are running: docker-compose ps")
        return
    
    print("\n2. Testing task submission...")
    if test_task_submission():
        print("\n✅ Direct Celery access is working!")
        print("\n🌸 You can now monitor tasks at: http://localhost:5556 (admin/admin)")
        print("   The video generation pipeline uses these same workers")
    else:
        print("\n❌ Task submission failed")

if __name__ == "__main__":
    main()