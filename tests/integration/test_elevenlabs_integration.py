#!/usr/bin/env python3
"""
Test ElevenLabs voice synthesis integration
"""
import os
import requests
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test script with narration
TEST_SCRIPT = """SCRIPT: ELEVENLABS TEST

[0:00 - Introduction]
Visual: Terminal screen showing ElevenLabs logo
Narration (Winston): "This is a test of the ElevenLabs voice synthesis integration. The system converts script narration into natural-sounding speech."
ON-SCREEN TEXT: ELEVENLABS VOICE TEST

[0:15 - Technical Details]
Visual: Code scrolling showing API integration
Narration: "Each narration segment is processed separately, allowing for different voices and emotional tones throughout the video."

[0:30 - Conclusion]
Visual: Success message on terminal
Narration: "Voice synthesis complete. The AI-generated narration brings the script to life."

END TEST
"""

def test_elevenlabs():
    """Test ElevenLabs integration through the API"""
    
    print("🔐 Logging in...")
    
    # Register and login
    register_data = {
        "email": "elevenlabs.test@example.com",
        "password": "password123",
        "full_name": "ElevenLabs Test"
    }
    
    requests.post("http://localhost:8000/api/v1/auth/register", json=register_data)
    
    login_data = {"username": "elevenlabs.test@example.com", "password": "password123"}
    response = requests.post("http://localhost:8000/api/v1/auth/token", data=login_data)
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        return
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("✅ Login successful!")
    
    # Check if ElevenLabs API key is configured
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        print("⚠️ ELEVENLABS_API_KEY not set in environment")
        print("   To test voice synthesis, set your API key:")
        print("   export ELEVENLABS_API_KEY='your-api-key-here'")
    else:
        print(f"✅ ElevenLabs API key configured (ending in ...{api_key[-4:]})")
    
    # Create test project
    print("📝 Creating test project with narration...")
    project_data = {
        "name": "ElevenLabs Voice Test",
        "description": "Testing voice synthesis integration",
        "script_content": TEST_SCRIPT,
        "style": "techwear",
        "voice_type": "male_calm"
    }
    
    response = requests.post("http://localhost:8000/api/v1/projects/", json=project_data, headers=headers)
    if response.status_code not in [200, 201]:
        print(f"❌ Project creation failed: {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    project = response.json()
    print(f"✅ Project created: {project['name']} ({project['id']})")
    
    # Start video generation
    print("🎬 Starting video generation with voice synthesis...")
    generation_data = {
        "project_id": project["id"],
        "quality": "high",
        "priority": 9
    }
    
    response = requests.post("http://localhost:8000/api/v1/generation/", json=generation_data, headers=headers)
    if response.status_code != 202:
        print(f"❌ Generation failed: {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    result = response.json()
    job_id = result["job_id"]
    
    print(f"✅ Video generation started!")
    print(f"📝 Job ID: {job_id}")
    
    # Monitor progress
    print("\n📈 Monitoring progress...")
    for i in range(20):  # Wait up to 20 seconds
        time.sleep(1)
        
        response = requests.get(f"http://localhost:8000/api/v1/generation/{job_id}/status", headers=headers)
        if response.status_code == 200:
            status = response.json()
            print(f"⏳ Progress: {status['progress']:.1f}% - {status.get('current_step', 'Processing')}")
            
            if status["status"] in ["completed", "failed"]:
                print(f"\n🎯 Final Status: {status['status']}")
                if status.get("error"):
                    print(f"❌ Error: {status['error']}")
                else:
                    print(f"✅ Video generation completed!")
                break
    
    print("\n🔍 Check worker logs for voice synthesis details:")
    print("docker-compose logs worker --tail=50 | grep -i 'voice\\|elevenlabs'")
    
    if api_key:
        print("\n🎤 Voice files should be generated in:")
        print(f"   /app/output/audio/{job_id}_scene_*.mp3")

if __name__ == "__main__":
    test_elevenlabs()