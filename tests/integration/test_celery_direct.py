#!/usr/bin/env python3
"""
Test script parsing by calling Celery task directly
"""
import uuid
from workers.tasks.video_generation import process_video_generation

def test_direct_celery():
    """Test the script parsing directly via Celery task"""
    
    # Read LOG_0002 script content
    script_file = "/mnt/c/Users/holla/OneDrive/Desktop/CodeProjects/Evergreen/scripts/ScriptLog0002TheDescent.txt"
    
    print("📖 Reading LOG_0002 script...")
    script_content = None
    
    for encoding in ['utf-8', 'utf-8-sig', 'windows-1252', 'latin1']:
        try:
            with open(script_file, "r", encoding=encoding) as f:
                script_content = f.read()
            print(f"✅ Read script with {encoding} encoding")
            break
        except Exception as e:
            print(f"⚠️ Failed with {encoding}: {e}")
            continue
    
    if not script_content:
        print("❌ Failed to read LOG_0002 script")
        return
    
    # Generate test job ID
    job_id = str(uuid.uuid4())
    
    # Test settings
    settings = {
        "voice_type": "male_calm",
        "style": "techwear", 
        "quality": "high",
        "priority": 5,
        "project_name": "LOG_0002 Direct Test",
        "webhook_url": None
    }
    
    print(f"🎬 Testing script parsing with job ID: {job_id}")
    print(f"📝 Script length: {len(script_content)} characters")
    
    try:
        # Call the task directly 
        result = process_video_generation(job_id, script_content, settings)
        
        print("✅ Task completed successfully!")
        print(f"📊 Result: {result}")
        
    except Exception as e:
        print(f"❌ Task failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_direct_celery()