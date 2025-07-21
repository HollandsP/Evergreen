#!/usr/bin/env python3
"""
Test the complete video generation pipeline with real media files
"""
import os
import sys
import json
import asyncio
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test script with timestamps
TEST_SCRIPT = """SCRIPT: TEST VIDEO - The Terminal
 
[0:00 - Opening Scene]
Visual: Black screen fading to a terminal window
Narration: "Welcome to the world of command line interfaces."
ON-SCREEN TEXT: $ echo "Hello, World!"
Hello, World!

[0:03 - Basic Commands]
Visual: Terminal showing file operations
Narration: "Let's explore some basic terminal commands."
ON-SCREEN TEXT: $ ls -la
total 24
drwxr-xr-x  3 user  staff   96 Jan 21 10:00 .
drwxr-xr-x  5 user  staff  160 Jan 21 09:00 ..
-rw-r--r--  1 user  staff  512 Jan 21 10:00 README.md

[0:05 - Advanced Operations]
Visual: Terminal showing git operations
Narration: "Now let's look at version control with git."
ON-SCREEN TEXT: $ git status
On branch main
Your branch is up to date with 'origin/main'.

[0:07 - Closing]
Visual: Terminal window slowly fading to black
Narration: "The terminal: where productivity meets power."
ON-SCREEN TEXT: $ exit
"""

def test_via_api():
    """Test the video generation through the API"""
    print("=== Testing Complete Pipeline via API ===\n")
    
    base_url = "http://localhost:8000/api/v1"
    
    # 1. Create a project
    print("1. Creating project...")
    project_data = {
        "title": "Test Terminal Video",
        "description": "Testing complete video generation pipeline",
        "duration": 10,
        "settings": {
            "resolution": "1920x1080",
            "fps": 30,
            "style": "cyberpunk",
            "voice_settings": {
                "narrator": "male_calm",
                "characters": {}
            }
        }
    }
    
    response = requests.post(f"{base_url}/projects/", json=project_data)
    if response.status_code != 200:
        print(f"❌ Failed to create project: {response.status_code} - {response.text}")
        return
    
    project = response.json()
    project_id = project["id"]
    print(f"✅ Created project: {project_id}")
    
    # 2. Upload script
    print("\n2. Uploading script...")
    script_data = {
        "content": TEST_SCRIPT,
        "script_type": "narrative"
    }
    
    response = requests.post(f"{base_url}/scripts/{project_id}", json=script_data)
    if response.status_code != 200:
        print(f"❌ Failed to upload script: {response.status_code} - {response.text}")
        return
    
    print("✅ Script uploaded successfully")
    
    # 3. Generate video
    print("\n3. Starting video generation...")
    response = requests.post(f"{base_url}/generate/{project_id}")
    if response.status_code != 200:
        print(f"❌ Failed to start generation: {response.status_code} - {response.text}")
        return
    
    job_info = response.json()
    job_id = job_info["job_id"]
    print(f"✅ Generation started: {job_id}")
    
    # 4. Monitor job status
    print("\n4. Monitoring job status...")
    for i in range(60):  # Check for up to 5 minutes
        response = requests.get(f"{base_url}/projects/{project_id}")
        if response.status_code == 200:
            project = response.json()
            status = project.get("status", "unknown")
            print(f"   Status: {status}", end="\r")
            
            if status == "completed":
                print(f"\n✅ Video generation completed!")
                
                # Check if output file exists
                output_path = f"output/exports/{project_id}_final.mp4"
                if os.path.exists(output_path):
                    size = os.path.getsize(output_path)
                    print(f"✅ Output file created: {output_path} ({size:,} bytes)")
                else:
                    print(f"❌ Output file not found: {output_path}")
                
                return
            elif status == "failed":
                print(f"\n❌ Video generation failed!")
                return
        
        asyncio.run(asyncio.sleep(5))
    
    print("\n⚠️ Timeout waiting for video generation")

def test_direct_assembly():
    """Test the video assembly directly using existing media files"""
    print("\n=== Testing Direct Video Assembly ===\n")
    
    # Check if test media files exist
    media_dirs = {
        "audio": "output/test_media/audio",
        "terminal": "output/test_media/terminal", 
        "visuals": "output/test_media/visuals"
    }
    
    for media_type, directory in media_dirs.items():
        if not os.path.exists(directory):
            print(f"❌ {media_type} directory not found: {directory}")
            return
        
        files = os.listdir(directory)
        print(f"✅ {media_type}: {len(files)} files found")
    
    # Run video assembly in worker container
    print("\nRunning video assembly in worker container...")
    
    cmd = """docker exec evergreen-worker-1 python -c "
import sys
sys.path.insert(0, '/app')
from workers.tasks.video_generation import VideoComposer
import json

# Define scene data with real file paths
scenes = [
    {
        'scene_id': 'scene_0',
        'start_time': 0.0,
        'end_time': 3.0,
        'duration': 3.0,
        'voice_file': '/app/output/test_media/audio/scene_0.mp3',
        'terminal_file': '/app/output/test_media/terminal/scene_0.mp4',
        'visual_file': '/app/output/test_media/visuals/scene_0.mp4'
    },
    {
        'scene_id': 'scene_1',
        'start_time': 3.0,
        'end_time': 5.0,
        'duration': 2.0,
        'voice_file': '/app/output/test_media/audio/scene_1.mp3',
        'terminal_file': '/app/output/test_media/terminal/scene_1.mp4',
        'visual_file': '/app/output/test_media/visuals/scene_1.mp4'
    },
    {
        'scene_id': 'scene_2',
        'start_time': 5.0,
        'end_time': 7.0,
        'duration': 2.0,
        'voice_file': '/app/output/test_media/audio/scene_2.mp3',
        'terminal_file': '/app/output/test_media/terminal/scene_2.mp4',
        'visual_file': '/app/output/test_media/visuals/scene_2.mp4'
    },
    {
        'scene_id': 'scene_3',
        'start_time': 7.0,
        'end_time': 10.0,
        'duration': 3.0,
        'voice_file': '/app/output/test_media/audio/scene_3.mp3',
        'terminal_file': '/app/output/test_media/terminal/scene_3.mp4',
        'visual_file': '/app/output/test_media/visuals/scene_3.mp4'
    }
]

# Create composer and assemble video
composer = VideoComposer()
output_path = '/app/output/test_media/final/test_complete_video.mp4'

print('Assembling video...')
success = composer.assemble_video(scenes, output_path)

if success:
    import os
    size = os.path.getsize(output_path)
    print(f'✅ Video assembled successfully: {size:,} bytes')
else:
    print('❌ Video assembly failed')
"
"""
    
    result = os.system(cmd)
    if result == 0:
        # Check if output exists
        output_path = "output/test_media/final/test_complete_video.mp4"
        if os.path.exists(output_path):
            size = os.path.getsize(output_path)
            print(f"\n✅ Final video created: {output_path} ({size:,} bytes)")
            
            # Get video info
            cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{output_path}"'
            import subprocess
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                duration = float(result.stdout.strip())
                print(f"✅ Video duration: {duration:.1f} seconds")
        else:
            print(f"\n❌ Output file not found: {output_path}")
    else:
        print("\n❌ Video assembly command failed")

def main():
    print("=== Complete Pipeline Test ===\n")
    
    # Test 1: Direct assembly with existing media files
    test_direct_assembly()
    
    # Test 2: Full pipeline via API
    # print("\n" + "="*50 + "\n")
    # test_via_api()
    
    print("\n✅ Pipeline testing complete!")

if __name__ == "__main__":
    main()