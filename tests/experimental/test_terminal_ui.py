#!/usr/bin/env python3
"""
Test terminal UI animation generation
"""
import os
import sys
import requests
import time
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Test script with terminal UI elements
TEST_SCRIPT = """SCRIPT: TERMINAL UI TEST

[0:00 - Command Line Demo]
Visual: Terminal window opening with green text on black
Narration: "Let's explore the power of command line interfaces."
ON-SCREEN TEXT: $ echo "Welcome to the Terminal UI Demo"
Welcome to the Terminal UI Demo
$ ls -la
total 48
drwxr-xr-x  6 user  staff   192 Jan 21 10:00 .
drwxr-xr-x  8 user  staff   256 Jan 21 09:00 ..
-rw-r--r--  1 user  staff  1024 Jan 21 10:00 README.md
-rwxr-xr-x  1 user  staff  2048 Jan 21 10:00 script.py

[0:20 - Code Execution]
Visual: Python code being typed and executed
Narration: "Watch as we execute Python code in real-time."
ON-SCREEN TEXT: $ python3 script.py
>>> Initializing AI pipeline...
>>> Loading models... [################] 100%
>>> Processing data...
✓ Data validation complete
✓ Models loaded successfully
>>> Generating output...

[0:40 - Matrix Effect]
Visual: Matrix-style cascading text
Narration: "Experience the iconic matrix terminal effect."
ON-SCREEN TEXT: 
01101000 01100101 01101100 01101100 01101111
SYSTEM INITIALIZED
ACCESS GRANTED
> run matrix.exe
[Matrix rain effect...]

END TEST
"""

def test_terminal_ui():
    """Test terminal UI animation generation"""
    
    print("🔐 Logging in...")
    
    # Register and login
    register_data = {
        "email": "terminal.ui.test@example.com",
        "password": "password123",
        "full_name": "Terminal UI Test"
    }
    
    requests.post("http://localhost:8000/api/v1/auth/register", json=register_data)
    
    login_data = {"username": "terminal.ui.test@example.com", "password": "password123"}
    response = requests.post("http://localhost:8000/api/v1/auth/token", data=login_data)
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        return
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("✅ Login successful!")
    
    # Test different terminal themes
    themes = ["dark", "matrix", "hacker", "vscode"]
    
    for theme in themes:
        print(f"\n🎨 Testing {theme} theme...")
        
        # Create test project
        project_data = {
            "name": f"Terminal UI Test - {theme.upper()}",
            "description": f"Testing terminal animations with {theme} theme",
            "script_content": TEST_SCRIPT,
            "style": "techwear",
            "voice_type": "male_calm",
            "terminal_theme": theme  # Specify terminal theme
        }
        
        response = requests.post("http://localhost:8000/api/v1/projects/", json=project_data, headers=headers)
        if response.status_code not in [200, 201]:
            print(f"❌ Project creation failed: {response.status_code}")
            print(f"Response: {response.text}")
            continue
        
        project = response.json()
        print(f"✅ Project created: {project['name']} ({project['id']})")
        
        # Start video generation
        print("🎬 Starting video generation with terminal UI...")
        generation_data = {
            "project_id": project["id"],
            "quality": "high",
            "priority": 9,
            "terminal_theme": theme
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
        
        # Monitor progress briefly
        print("📈 Monitoring progress...")
        for i in range(10):  # Wait up to 10 seconds
            time.sleep(1)
            
            response = requests.get(f"http://localhost:8000/api/v1/generation/{job_id}/status", headers=headers)
            if response.status_code == 200:
                status = response.json()
                print(f"⏳ Progress: {status['progress']:.1f}% - {status.get('current_step', 'Processing')}")
                
                if status["status"] in ["completed", "failed"]:
                    print(f"🎯 Final Status: {status['status']}")
                    if status.get("error"):
                        print(f"❌ Error: {status['error']}")
                    break
    
    print("\n🔍 Check worker logs for terminal UI generation details:")
    print("docker-compose logs worker --tail=100 | grep -i 'terminal\\|ui\\|animation'")
    
    print("\n💻 Terminal UI files should be generated in:")
    print("   /app/output/ui/{job_id}_ui_*.mp4")

def test_local_terminal_rendering():
    """Test terminal rendering locally without Docker"""
    print("\n🧪 Testing local terminal rendering...")
    
    try:
        from workers.effects import TerminalRenderer, TerminalTheme, parse_terminal_commands
        
        # Test basic rendering
        renderer = TerminalRenderer(
            width=1920,
            height=1080,
            cols=80,
            rows=24,
            theme=TerminalTheme.MATRIX,
            font_size=20
        )
        
        # Test typing animation
        test_text = "$ echo 'Hello, Terminal UI!'\nHello, Terminal UI!"
        frames = renderer.create_typing_animation(test_text, duration=3.0, fps=30)
        
        print(f"✅ Generated {len(frames)} frames")
        print(f"   Duration: {len(frames) / 30.0:.2f} seconds")
        
        # Save first and last frame as preview
        if frames:
            frames[0].save("terminal_preview_first.png")
            frames[-1].save("terminal_preview_last.png")
            print("✅ Preview frames saved:")
            print("   - terminal_preview_first.png")
            print("   - terminal_preview_last.png")
        
    except Exception as e:
        print(f"❌ Local rendering test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Test local rendering first
    test_local_terminal_rendering()
    
    # Then test full pipeline
    print("\n" + "="*50)
    test_terminal_ui()