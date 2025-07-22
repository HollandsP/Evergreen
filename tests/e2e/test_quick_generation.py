#!/usr/bin/env python3
"""
Quick test to trigger video generation and see parsing logs
"""
import requests
import time

# Simplified script for quick testing
SIMPLE_SCRIPT = """SCRIPT: LOG_TEST - Quick Test

[0:00 - Scene 1]
Visual: Terminal screen with code scrolling
Narration (Winston): "This is a test of the script parsing system."
ON-SCREEN TEXT: TESTING SCRIPT PARSER v2.0

[0:30 - Scene 2] 
Visual: City skyline at night
Narration: "The parsing engine extracts visual descriptions, narration, and on-screen text."

END LOG_TEST
"""

def quick_test():
    """Quick test of video generation pipeline"""
    
    print("🔐 Logging in...")
    
    # Register and login
    register_data = {
        "email": "test.parser@example.com",
        "password": "password123",
        "full_name": "Parser Test"
    }
    
    requests.post("http://localhost:8000/api/v1/auth/register", json=register_data)
    
    login_data = {"username": "test.parser@example.com", "password": "password123"}
    response = requests.post("http://localhost:8000/api/v1/auth/token", data=login_data)
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        return
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("✅ Login successful!")
    
    # Create simple test project
    print("📝 Creating test project...")
    project_data = {
        "name": "Script Parser Test",
        "description": "Testing the new script parsing functionality",
        "script_content": SIMPLE_SCRIPT,
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
        "priority": 8
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
    
    print("\n🔍 Check worker logs for parsing details:")
    print("docker-compose logs worker --tail=30")
    
    return job_id

if __name__ == "__main__":
    quick_test()