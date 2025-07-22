#!/usr/bin/env python3
"""
Simple test for Runway visual generation
"""
import os
import requests
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Simple test script
TEST_SCRIPT = """SCRIPT: SIMPLE RUNWAY TEST

[0:00 - Visual Test]
Visual: A futuristic city at night with neon lights
Narration: "Testing visual generation."
ON-SCREEN TEXT: RUNWAY TEST

END TEST
"""

def test_simple_runway():
    """Test basic Runway visual generation"""
    
    print("🔐 Logging in...")
    
    # Register and login
    register_data = {
        "email": "simple.runway.test@example.com",
        "password": "password123",
        "full_name": "Simple Runway Test"
    }
    
    requests.post("http://localhost:8000/api/v1/auth/register", json=register_data)
    
    login_data = {"username": "simple.runway.test@example.com", "password": "password123"}
    response = requests.post("http://localhost:8000/api/v1/auth/token", data=login_data)
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        return
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("✅ Login successful!")
    
    # Check if Runway API key is configured
    api_key = os.getenv("RUNWAY_API_KEY")
    if api_key:
        print(f"✅ Runway API key configured (stub implementation will be used)")
    else:
        print("⚠️ RUNWAY_API_KEY not set - will use placeholder files")
    
    # Create test project
    project_data = {
        "name": "Simple Runway Visual Test",
        "description": "Testing basic visual generation",
        "script_content": TEST_SCRIPT,
        "style": "techwear",  # Use valid style
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
    print("🎬 Starting video generation...")
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
    
    # Wait a moment then check logs
    time.sleep(5)
    
    print("\n🔍 Check worker logs:")
    print(f"docker-compose logs worker --tail=100 | grep '{job_id}'")
    print(f"\n🎥 Check if visual files were created:")
    print(f"docker exec evergreen-worker ls -la /app/output/visuals/")

if __name__ == "__main__":
    test_simple_runway()