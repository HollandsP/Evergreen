#!/usr/bin/env python3
"""
Simple test for terminal UI generation
"""
import os
import requests
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Simple test script
TEST_SCRIPT = """SCRIPT: SIMPLE TERMINAL TEST

[0:00 - Terminal Demo]
Visual: Simple terminal window
Narration: "Testing terminal UI generation."
ON-SCREEN TEXT: $ echo "Hello Terminal UI"
Hello Terminal UI

END TEST
"""

def test_simple_terminal():
    """Test basic terminal UI generation"""
    
    print("🔐 Logging in...")
    
    # Register and login
    register_data = {
        "email": "simple.terminal.test@example.com",
        "password": "password123",
        "full_name": "Simple Terminal Test"
    }
    
    requests.post("http://localhost:8000/api/v1/auth/register", json=register_data)
    
    login_data = {"username": "simple.terminal.test@example.com", "password": "password123"}
    response = requests.post("http://localhost:8000/api/v1/auth/token", data=login_data)
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        return
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("✅ Login successful!")
    
    # Create test project
    project_data = {
        "name": "Simple Terminal UI Test",
        "description": "Testing basic terminal UI generation",
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
    print(f"\n💻 Check if terminal UI files were created:")
    print(f"docker exec evergreen-worker ls -la /app/output/ui/")

if __name__ == "__main__":
    test_simple_terminal()