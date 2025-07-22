#!/usr/bin/env python3
"""
Test Runway visual scene generation integration
"""
import os
import requests
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test script with visual descriptions
TEST_SCRIPT = """SCRIPT: RUNWAY VISUAL TEST

[0:00 - Opening Scene]
Visual: A futuristic cityscape at night with neon lights reflecting on wet streets, flying vehicles in the distance
Narration: "Welcome to the future of AI-generated video content."
ON-SCREEN TEXT: RUNWAY VISUAL GENERATION TEST

[0:15 - Tech Demo]
Visual: Close-up of a high-tech terminal screen with cascading code, holographic displays floating in the air
Narration: "Watch as AI transforms text descriptions into stunning visuals."

[0:30 - Action Sequence]
Visual: A sleek robotic figure walking through a cyberpunk alley, sparks flying from welding robots, steam rising from vents
Narration: "Every scene is generated from simple text prompts."

[0:45 - Finale]
Visual: Wide shot of the city skyline with aurora-like lights in the sky, a massive holographic display showing "AI POWERED"
Narration: "The future of content creation is here."

END TEST
"""

def test_runway_integration():
    """Test Runway visual scene generation"""
    
    print("🔐 Logging in...")
    
    # Register and login
    register_data = {
        "email": "runway.test@example.com",
        "password": "password123",
        "full_name": "Runway Test"
    }
    
    requests.post("http://localhost:8000/api/v1/auth/register", json=register_data)
    
    login_data = {"username": "runway.test@example.com", "password": "password123"}
    response = requests.post("http://localhost:8000/api/v1/auth/token", data=login_data)
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        return
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("✅ Login successful!")
    
    # Check if Runway API key is configured
    api_key = os.getenv("RUNWAY_API_KEY")
    if not api_key:
        print("⚠️ RUNWAY_API_KEY not set in environment")
        print("   To test visual generation, set your API key:")
        print("   export RUNWAY_API_KEY='your-api-key-here'")
        print("   Note: Will use stub implementation for testing")
    else:
        print(f"✅ Runway API key configured (ending in ...{api_key[-4:]})")
    
    # Test different visual styles
    styles = ["techwear", "minimalist", "futuristic"]
    
    for style in styles:
        print(f"\n🎨 Testing {style} style visuals...")
        
        # Create test project
        project_data = {
            "name": f"Runway Visual Test - {style.upper()}",
            "description": f"Testing visual generation with {style} style",
            "script_content": TEST_SCRIPT,
            "style": style,
            "voice_type": "male_calm"
        }
        
        response = requests.post("http://localhost:8000/api/v1/projects/", json=project_data, headers=headers)
        if response.status_code not in [200, 201]:
            print(f"❌ Project creation failed: {response.status_code}")
            print(f"Response: {response.text}")
            continue
        
        project = response.json()
        print(f"✅ Project created: {project['name']} ({project['id']})")
        
        # Start video generation
        print("🎬 Starting video generation with visual scenes...")
        generation_data = {
            "project_id": project["id"],
            "quality": "high",
            "priority": 9
        }
        
        response = requests.post("http://localhost:8000/api/v1/generation/", json=generation_data, headers=headers)
        if response.status_code != 202:
            print(f"❌ Generation failed: {response.status_code}")
            print(f"Response: {response.text}")
            continue
        
        result = response.json()
        job_id = result["job_id"]
        
        print(f"✅ Video generation started!")
        print(f"📝 Job ID: {job_id}")
        
        # Monitor progress
        print("\n📈 Monitoring visual generation progress...")
        visual_generated = False
        
        for i in range(30):  # Wait up to 30 seconds
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
                        visual_generated = True
                    break
        
        if visual_generated:
            break  # Only test one style if successful
    
    print("\n🔍 Check worker logs for visual generation details:")
    print("docker-compose logs worker --tail=100 | grep -i 'visual\\|runway\\|generation'")
    
    if api_key:
        print("\n🎥 Visual scene files should be generated in:")
        print(f"   /app/output/visuals/{job_id}_visual_*.mp4")
    else:
        print("\n📝 Note: Using stub implementation - placeholder files created")

def test_local_runway_client():
    """Test Runway client locally"""
    print("\n🧪 Testing local Runway client...")
    
    try:
        from src.services.runway_client import RunwayClient
        
        # Test with dummy API key
        client = RunwayClient(api_key="test_key")
        
        # Test video generation
        print("📹 Testing video generation submission...")
        job = client.generate_video(
            prompt="A futuristic city with flying cars",
            duration=5.0,
            style="techwear"
        )
        
        print(f"✅ Generation job created: {job['id']}")
        print(f"   Status: {job['status']}")
        print(f"   Duration: {job['duration']}s")
        
        # Test status polling
        print("\n📊 Testing status polling...")
        for i in range(5):
            status = client.get_generation_status(job['id'])
            print(f"   Progress: {status['progress']}% - Status: {status['status']}")
            
            if status['status'] == 'completed':
                print(f"✅ Generation completed!")
                print(f"   Video URL: {status.get('video_url', 'N/A')}")
                break
            
            time.sleep(0.5)
        
        # Test model listing
        print("\n📋 Available models:")
        models = client.list_models()
        for model in models:
            print(f"   - {model['name']}: {model['description']}")
            print(f"     Max duration: {model['max_duration']}s")
        
    except Exception as e:
        print(f"❌ Local client test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Test local client first
    test_local_runway_client()
    
    # Then test full pipeline
    print("\n" + "="*50)
    test_runway_integration()