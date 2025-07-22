#!/usr/bin/env python3
"""
Simple video generation script using the actual API
"""
import asyncio
import httpx
import time
import os

# Configuration
API_BASE_URL = "http://localhost:8000"
SCRIPT_PATH = "scripts/ScriptLog0002TheDescent.txt"

# Load environment variables
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
RUNWAY_API_KEY = os.getenv("RUNWAY_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

async def check_api_health():
    """Check if API is running"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/health")
        response.raise_for_status()
        return response.json()

async def create_user():
    """Create a test user"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{API_BASE_URL}/api/v1/auth/register",
                json={
                    "email": "test@example.com",
                    "password": "testpass123",
                    "full_name": "Test User"
                }
            )
            if response.status_code == 201:
                return response.json()
        except:
            pass  # User might already exist
    
    # Try to login instead
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/api/v1/auth/token",
            data={
                "username": "test@example.com",
                "password": "testpass123"
            }
        )
        if response.status_code == 200:
            return response.json()
    
    raise Exception("Could not create or login user")

async def create_project(token: str, script_content: str):
    """Create a new project"""
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/api/v1/projects/",
            headers=headers,
            json={
                "name": "LOG_0002 - The Descent",
                "description": "AI Incident Log - Solstice Tower Integration Team",
                "script_content": script_content,
                "style": "techwear",
                "voice_type": "male_calm"
            }
        )
        response.raise_for_status()
        return response.json()

async def start_generation(token: str, project_id: str):
    """Start video generation"""
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/api/v1/generation/",
            headers=headers,
            json={
                "project_id": project_id,
                "quality": "high",
                "priority": 5
            }
        )
        response.raise_for_status()
        return response.json()

async def check_status(token: str, job_id: str):
    """Check generation status"""
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/api/v1/generation/{job_id}/status",
            headers=headers
        )
        response.raise_for_status()
        return response.json()

async def main():
    """Main execution function"""
    print("🎬 AI Content Pipeline - Video Generation")
    print("=" * 50)
    
    # Check API health
    print("🏥 Checking API health...")
    health = await check_api_health()
    print(f"   API Status: {health.get('status', 'unknown')}")
    
    # Read script with encoding handling
    print(f"📄 Reading script: {SCRIPT_PATH}")
    try:
        with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
            script_content = f.read()
    except UnicodeDecodeError:
        print("   UTF-8 decode failed, trying with error handling...")
        with open(SCRIPT_PATH, "r", encoding="utf-8", errors="replace") as f:
            script_content = f.read()
    except Exception:
        print("   UTF-8 failed, trying Windows-1252 encoding...")
        with open(SCRIPT_PATH, "r", encoding="windows-1252") as f:
            script_content = f.read()
    
    print(f"   Script length: {len(script_content)} characters")
    
    try:
        # Create/login user
        print("\n👤 Setting up user authentication...")
        auth_result = await create_user()
        token = auth_result.get("access_token")
        if not token:
            raise Exception("No access token received")
        print("   ✅ User authenticated")
        
        # Create project
        print("\n📁 Creating project...")
        project = await create_project(token, script_content)
        project_id = project.get("id")
        print(f"   ✅ Project created: {project_id}")
        print(f"   Project name: {project.get('name', 'Unknown')}")
        
        # Start generation
        print("\n🚀 Starting video generation...")
        generation = await start_generation(token, project_id)
        job_id = generation.get("job_id")
        print(f"   ✅ Generation started: {job_id}")
        print(f"   Status: {generation.get('status', 'unknown')}")
        
        print(f"\n🌸 Monitor progress at: http://localhost:5556 (admin/admin)")
        print(f"📊 Job ID: {job_id}")
        
        # Monitor progress
        print("\n⏳ Monitoring progress...")
        while True:
            try:
                status = await check_status(token, job_id)
                current_status = status.get("status", "unknown")
                progress = status.get("progress", 0)
                current_step = status.get("current_step", "")
                
                print(f"   Status: {current_status} | Progress: {progress:.1f}% | Step: {current_step}")
                
                if current_status == "completed":
                    video_url = status.get("video_url")
                    print(f"\n🎉 Video generation completed!")
                    print(f"   Video URL: {video_url}")
                    break
                elif current_status == "failed":
                    error = status.get("error", "Unknown error")
                    print(f"\n❌ Video generation failed: {error}")
                    break
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except KeyboardInterrupt:
                print("\n⏹️ Monitoring interrupted by user")
                print(f"   Job {job_id} is still running in background")
                print(f"   Check progress at: http://localhost:5556")
                break
            except Exception as e:
                print(f"   Error checking status: {e}")
                await asyncio.sleep(5)
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n🔧 Troubleshooting:")
        print("   • Check if all services are running: docker-compose ps")
        print("   • Check API logs: docker-compose logs api")
        print("   • Monitor tasks: http://localhost:5556 (admin/admin)")

if __name__ == "__main__":
    print("🚀 Starting video generation...")
    asyncio.run(main())