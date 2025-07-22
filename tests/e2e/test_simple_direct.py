#!/usr/bin/env python3
"""
Simple direct test of video generation functions
"""
import subprocess
import uuid

# Simple test script  
TEST_SCRIPT = """SCRIPT: SIMPLE TEST

[0:00]
Visual: A test scene
Narration (Male): "Testing video generation."
ON-SCREEN TEXT: $ echo "test"

END TEST
"""

def test_simple():
    """Simple test of video generation"""
    job_id = str(uuid.uuid4())
    
    # Test script to run in worker
    test_code = f"""
import os
import sys
sys.path.append('/app')

# Create directories
for dir in ['/app/output/audio', '/app/output/ui', '/app/output/visuals', '/app/output/exports']:
    os.makedirs(dir, exist_ok=True)

from workers.tasks.video_generation import ScriptParser, VideoComposer

job_id = '{job_id}'
script_content = '''{TEST_SCRIPT}'''
settings = {{'voice_type': 'male_calm', 'style': 'techwear', 'quality': 'high'}}

# Test 1: Parse script
print("\\n1. Testing ScriptParser...")
parser = ScriptParser()
parsed = parser.parse_script(script_content)
print(f"   ✓ Parsed {{len(parsed.get('scenes', []))}} scenes")
print(f"   Title: {{parsed.get('title')}}")
print(f"   Duration: {{parsed.get('total_duration')}}s")

# Test 2: Create VideoComposer
print("\\n2. Testing VideoComposer...")
composer = VideoComposer(job_id, parsed, settings)
print("   ✓ VideoComposer created!")

# Test 3: Build timeline with empty arrays (simulating no assets yet)
print("\\n3. Testing timeline building...")
timeline = composer.build_timeline([], [], [])
print(f"   ✓ Timeline has {{len(timeline)}} entries")

# Test 4: Check FFmpeg command generation
print("\\n4. Testing FFmpeg command generation...")
for mode in ['overlay', 'visual_only', 'ui_only', 'audio_only']:
    cmd = composer._get_ffmpeg_command(mode, timeline)
    print(f"   ✓ {{mode}}: {{len(cmd)}} command parts")

# Test 5: Check if we can call the video generation process
print("\\n5. Testing video generation import...")
from workers.tasks.video_generation import process_video_generation
print("   ✓ process_video_generation imported successfully")

print("\\n✅ All tests passed!")
"""

    # Write to file
    with open('/tmp/test_simple.py', 'w') as f:
        f.write(test_code)
    
    # Copy to worker
    subprocess.run(['docker', 'cp', '/tmp/test_simple.py', 'evergreen-worker-1:/tmp/test_simple.py'])
    
    # Run test
    print(f"🧪 Running simple test (Job ID: {job_id})")
    print("=" * 60)
    
    result = subprocess.run(
        ['docker', 'exec', '-t', 'evergreen-worker-1', 'python3', '/tmp/test_simple.py'],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print("Errors:")
        print(result.stderr)
    
    # Check if VideoComposer was mentioned
    if "VideoComposer created!" in result.stdout:
        print("\n🎉 SUCCESS: VideoComposer is available and working!")
        return True
    else:
        print("\n❌ FAILED: VideoComposer not working")
        return False

if __name__ == "__main__":
    test_simple()