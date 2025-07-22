#!/usr/bin/env python3
"""
Generate video from LOG_0002 script
"""
import asyncio
import json
import os
from pathlib import Path
from dotenv import load_dotenv
import httpx
from datetime import datetime

# Load environment variables
load_dotenv()

# Configuration
API_BASE_URL = "http://localhost:8000"
SCRIPT_PATH = Path("scripts/ScriptLog0002TheDescent.txt")
OUTPUT_DIR = Path("output/exports")

async def create_project():
    """Create a new project for the video"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/api/v1/projects/",
            json={
                "name": "LOG_0002 - The Descent",
                "description": "AI Incident Log - Solstice Tower Integration Team",
                "metadata": {
                    "theme": "AI Apocalypse",
                    "style": "Terminal UI / Found Footage",
                    "duration_estimate": "5:00"
                }
            }
        )
        response.raise_for_status()
        return response.json()

async def process_script(project_id: str, script_content: str):
    """Submit script for processing"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/api/v1/scripts/parse",
            json={
                "project_id": project_id,
                "content": script_content,
                "format": "screenplay",
                "metadata": {
                    "title": "LOG_0002 - THE DESCENT",
                    "author": "AI Incident Recovery",
                    "date": "August 5, 2027"
                }
            }
        )
        response.raise_for_status()
        return response.json()

async def generate_voice(project_id: str, script_id: str):
    """Generate voice narration"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/api/v1/voice/generate",
            json={
                "project_id": project_id,
                "script_id": script_id,
                "voice_settings": {
                    "voice_id": "winston_marek",  # Will use default if not available
                    "style": "distorted_low",
                    "emotion": "haunted",
                    "pace": 0.9
                }
            }
        )
        response.raise_for_status()
        return response.json()

async def generate_visuals(project_id: str, script_id: str):
    """Generate visual scenes"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/api/v1/video/generate",
            json={
                "project_id": project_id,
                "script_id": script_id,
                "style_settings": {
                    "theme": "terminal_ui",
                    "effects": ["glitch", "static", "crt_scan"],
                    "color_scheme": "amber_monochrome",
                    "overlay_opacity": 0.8
                }
            }
        )
        response.raise_for_status()
        return response.json()

async def assemble_video(project_id: str):
    """Assemble final video"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/api/v1/assembly/create",
            json={
                "project_id": project_id,
                "output_settings": {
                    "resolution": "1920x1080",
                    "fps": 30,
                    "codec": "h264",
                    "quality": "high"
                }
            }
        )
        response.raise_for_status()
        return response.json()

async def check_task_status(task_id: str):
    """Check status of a Celery task"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/api/v1/tasks/{task_id}")
        response.raise_for_status()
        return response.json()

async def wait_for_task(task_id: str, task_name: str):
    """Wait for a task to complete"""
    print(f"⏳ Waiting for {task_name}...")
    while True:
        status = await check_task_status(task_id)
        if status["state"] == "SUCCESS":
            print(f"✅ {task_name} completed!")
            return status["result"]
        elif status["state"] == "FAILURE":
            print(f"❌ {task_name} failed: {status.get('error', 'Unknown error')}")
            raise Exception(f"Task failed: {status.get('error', 'Unknown error')}")
        else:
            print(f"   Status: {status['state']} - {status.get('progress', 0)}%")
            await asyncio.sleep(2)

async def main():
    """Main execution function"""
    print("🎬 AI Content Pipeline - Video Generation")
    print("=" * 50)
    
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
        # Create project
        print("\n📁 Creating project...")
        project = await create_project()
        project_id = project["id"]
        print(f"   Project ID: {project_id}")
        
        # Process script
        print("\n📝 Processing script...")
        script_result = await process_script(project_id, script_content)
        script_id = script_result["script_id"]
        print(f"   Script ID: {script_id}")
        print(f"   Scenes detected: {script_result.get('scene_count', 'N/A')}")
        
        # Generate voice narration
        print("\n🎙️ Generating voice narration...")
        voice_task = await generate_voice(project_id, script_id)
        voice_result = await wait_for_task(voice_task["task_id"], "Voice Generation")
        
        # Generate visuals
        print("\n🎨 Generating visual scenes...")
        visual_task = await generate_visuals(project_id, script_id)
        visual_result = await wait_for_task(visual_task["task_id"], "Visual Generation")
        
        # Assemble final video
        print("\n🎞️ Assembling final video...")
        assembly_task = await assemble_video(project_id)
        assembly_result = await wait_for_task(assembly_task["task_id"], "Video Assembly")
        
        # Results
        print("\n✨ Video generation complete!")
        print(f"   Output: {assembly_result.get('output_path', 'N/A')}")
        print(f"   S3 URL: {assembly_result.get('s3_url', 'N/A')}")
        print(f"   Duration: {assembly_result.get('duration', 'N/A')} seconds")
        
        # Save metadata
        metadata_path = OUTPUT_DIR / f"log_0002_metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        with open(metadata_path, "w") as f:
            json.dump({
                "project": project,
                "script": script_result,
                "voice": voice_result,
                "visuals": visual_result,
                "assembly": assembly_result
            }, f, indent=2)
        print(f"\n📊 Metadata saved: {metadata_path}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        raise

if __name__ == "__main__":
    print("🚀 Starting video generation...\n")
    asyncio.run(main())