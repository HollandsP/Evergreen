#!/usr/bin/env python3
"""
Quick test for FFmpeg assembly
"""
import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

# Minimal test script
TEST_SCRIPT = """SCRIPT: QUICK FFMPEG TEST

[0:00 - Test Scene]
Visual: A test pattern
Narration (Male): "Testing FFmpeg assembly."
ON-SCREEN TEXT: FFmpeg Test

END TEST
"""

def quick_test():
    """Quick FFmpeg assembly test"""
    
    # Quick login
    register_data = {"email": "quick.test@example.com", "password": "pass123", "full_name": "Quick Test"}
    requests.post("http://localhost:8000/api/v1/auth/register", json=register_data)
    
    login_data = {"username": "quick.test@example.com", "password": "pass123"}
    response = requests.post("http://localhost:8000/api/v1/auth/token", data=login_data)
    
    if response.status_code != 200:
        print(f"Login failed: {response.status_code}")
        return
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create project
    project_data = {
        "name": "Quick FFmpeg Test",
        "description": "Testing FFmpeg assembly",
        "script_content": TEST_SCRIPT,
        "style": "techwear",
        "voice_type": "male_calm"
    }
    
    response = requests.post("http://localhost:8000/api/v1/projects/", json=project_data, headers=headers)
    if response.status_code not in [200, 201]:
        print(f"Project creation failed: {response.status_code}")
        return
    
    project = response.json()
    project_id = project['id']
    
    # Start generation
    generation_data = {
        "project_id": project_id,
        "quality": "high",
        "priority": 9
    }
    
    response = requests.post("http://localhost:8000/api/v1/generation/", json=generation_data, headers=headers)
    if response.status_code != 202:
        print(f"Generation failed: {response.status_code}")
        return
    
    job_id = response.json()["job_id"]
    print(f"Job started: {job_id}")
    
    # Wait a bit
    time.sleep(10)
    
    # Check logs
    print("\nChecking worker logs...")
    import subprocess
    result = subprocess.run(
        ["docker-compose", "logs", "worker", "--tail=100"],
        capture_output=True, text=True
    )
    
    # Look for assembly messages
    for line in result.stdout.split('\n'):
        if any(word in line for word in ['VideoComposer', 'timeline', 'assembly', 'FFmpeg']):
            print(line)

if __name__ == "__main__":
    quick_test()