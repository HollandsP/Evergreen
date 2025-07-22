#!/usr/bin/env python3
"""
Test script parsing implementation with LOG_0002 content
"""
import requests
import json
import time

# API endpoint
API_BASE = "http://localhost:8000/api/v1"

def test_script_parsing():
    """Test the updated script parsing implementation"""
    
    # First, register a new user
    print("👤 Registering test user...")
    register_data = {
        "email": "winston.test@example.com",
        "password": "password123",
        "full_name": "Winston Test"
    }
    
    response = requests.post(f"{API_BASE}/auth/register", json=register_data)
    if response.status_code not in [200, 201, 400]:  # 400 might mean user exists
        print(f"⚠️ Registration response: {response.status_code}")
        print(f"Response: {response.text}")
    else:
        print("✅ User registered or already exists!")
    
    # Now login to get a token
    print("🔐 Logging in...")
    login_data = {
        "username": "winston.test@example.com",
        "password": "password123"
    }
    
    response = requests.post(f"{API_BASE}/auth/token", data=login_data)
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("✅ Login successful!")
    
    # Get or create LOG_0002 project 
    print("📋 Getting existing projects...")
    response = requests.get(f"{API_BASE}/projects/", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Failed to get projects: {response.status_code}")
        return
    
    projects = response.json()["items"]
    log_project = None
    
    for project in projects:
        if "LOG_0002" in project["name"] or "Descent" in project["name"]:
            log_project = project
            break
    
    if not log_project:
        print("📝 Creating LOG_0002 project...")
        
        # Read LOG_0002 script content with encoding fallback
        script_content = None
        script_file = "/mnt/c/Users/holla/OneDrive/Desktop/CodeProjects/Evergreen/scripts/ScriptLog0002TheDescent.txt"
        
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
            print("❌ Failed to read LOG_0002 script with any encoding")
            return
        
        project_data = {
            "name": "LOG_0002 - The Descent (Test)",
            "description": "Test project for script parsing implementation",
            "script_content": script_content,
            "style": "techwear",
            "voice_type": "male_calm"
        }
        
        response = requests.post(f"{API_BASE}/projects/", json=project_data, headers=headers)
        if response.status_code not in [200, 201]:
            print(f"❌ Failed to create project: {response.status_code}")
            print(f"Response: {response.text}")
            return
        
        log_project = response.json()
        print(f"✅ Created project: {log_project['name']} ({log_project['id']})")
    else:
        print(f"✅ Found project: {log_project['name']} ({log_project['id']})")
    
    # Start video generation with new parser
    print("🎬 Starting video generation with script parsing...")
    generation_data = {
        "project_id": log_project["id"],
        "quality": "high",
        "priority": 5
    }
    
    response = requests.post(f"{API_BASE}/generation/", json=generation_data, headers=headers)
    
    if response.status_code != 202:
        print(f"❌ Generation failed to start: {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    result = response.json()
    job_id = result["job_id"]
    
    print(f"✅ Video generation started!")
    print(f"📝 Job ID: {job_id}")
    print(f"📊 Status: {result['status']}")
    
    # Monitor progress
    print("\n📈 Monitoring progress...")
    for i in range(30):  # Wait up to 30 seconds
        time.sleep(1)
        
        response = requests.get(f"{API_BASE}/generation/{job_id}/status", headers=headers)
        if response.status_code == 200:
            status = response.json()
            print(f"⏳ Progress: {status['progress']:.1f}% - {status.get('current_step', 'Processing')}")
            
            if status["status"] in ["completed", "failed"]:
                print(f"\n🎯 Final Status: {status['status']}")
                if status.get("error"):
                    print(f"❌ Error: {status['error']}")
                else:
                    print(f"✅ Video generation completed!")
                    if status.get("video_url"):
                        print(f"📹 Video URL: {status['video_url']}")
                break
        else:
            print(f"⚠️ Status check failed: {response.status_code}")
    
    print("\n🔍 Check worker logs for detailed parsing output:")
    print("docker-compose logs worker --tail=50")

if __name__ == "__main__":
    test_script_parsing()