#!/usr/bin/env python3
"""
Complete video generation test with mocked APIs
"""
import subprocess
import uuid
import time

# 2-minute showcase script
SHOWCASE_SCRIPT = """SCRIPT: AI VIDEO GENERATION - 2 MINUTE SHOWCASE

[0:00 - Opening]
Visual: A futuristic AI laboratory with holographic displays
Narration (Male): "Welcome to the AI video generation pipeline showcase."
ON-SCREEN TEXT: $ echo "AI Video Generation Pipeline"

[0:30 - Components Demo]
Visual: Split screen showing all components
Narration (Female): "Watch as voice synthesis, terminal animations, and visuals combine."
ON-SCREEN TEXT: $ ffmpeg -version

[1:00 - Integration Test]
Visual: The complete pipeline in action
Narration (Male): "Our FFmpeg assembly creates professional videos from simple scripts."
ON-SCREEN TEXT: $ ls -la output/

[1:30 - Final Result]
Visual: Showcase of the final video
Narration (Female): "From script to screen in minutes."
ON-SCREEN TEXT: $ echo "Success!"

END SHOWCASE
"""

def test_complete_generation():
    """Test complete video generation with all components"""
    job_id = str(uuid.uuid4())
    print(f"🎬 Complete Video Generation Test")
    print(f"📝 Job ID: {job_id}")
    print("=" * 60)
    
    # Create test script that mocks missing services
    test_script = f'''
import os
import sys
import json
sys.path.append('/app')

# Set environment variables
os.environ['OPENAI_API_KEY'] = 'test-key'
os.environ['ELEVENLABS_API_KEY'] = 'test-key'

# Mock the external services
import unittest.mock as mock

# Mock ElevenLabs
mock_elevenlabs = mock.MagicMock()
mock_elevenlabs.generate.return_value = b'mock audio data'
sys.modules['elevenlabs'] = mock_elevenlabs

# Import after mocking
from workers.tasks.video_generation import process_video_generation

job_id = '{job_id}'
script_content = """{SHOWCASE_SCRIPT}"""
settings = {{
    'voice_type': 'male_calm',
    'style': 'techwear', 
    'quality': 'high'
}}

print("\\n🚀 Starting complete video generation...")

# Create a mock task context
class MockTask:
    def __init__(self):
        self.request = type('obj', (object,), {{'retries': 0, 'id': job_id}})()
        
    def update_state(self, state=None, meta=None):
        print(f"   Task state: {{state}} - {{meta.get('message', '') if meta else ''}}")

try:
    # Call the function directly (it's a Celery task, so no self parameter)
    result = process_video_generation(job_id, script_content, settings)
    
    print(f"\\n✅ Video generation completed!")
    print(f"Result: {{result}}")
    
    # Check if output file exists
    if os.path.exists(result):
        size_mb = os.path.getsize(result) / (1024 * 1024)
        print(f"\\n🎥 Output video created: {{result}}")
        print(f"   Size: {{size_mb:.2f}} MB")
    else:
        print(f"\\n⚠️ Output file not found: {{result}}")
        
except Exception as e:
    print(f"\\n❌ Error during generation: {{e}}")
    import traceback
    traceback.print_exc()

# Check what files were created
print("\\n📁 Files created during generation:")
for subdir in ['audio', 'ui', 'visuals', 'exports']:
    path = f'/app/output/{{subdir}}'
    if os.path.exists(path):
        files = [f for f in os.listdir(path) if job_id in f]
        if files:
            print(f"\\n   {{subdir}}:")
            for f in files:
                full_path = os.path.join(path, f)
                size_kb = os.path.getsize(full_path) / 1024
                print(f"      - {{f}} ({{size_kb:.1f}} KB)")
'''

    # Write script
    script_path = f"/tmp/test_complete_{job_id}.py"
    with open(script_path, 'w') as f:
        f.write(test_script)
    
    # Copy to worker
    subprocess.run(['docker', 'cp', script_path, f'evergreen-worker-1:{script_path}'])
    
    print("\n🚀 Running complete generation test...")
    print("-" * 60)
    
    # Run test and capture output
    process = subprocess.Popen(
        ['docker', 'exec', '-t', 'evergreen-worker-1', 'python3', script_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    # Monitor output
    assembly_started = False
    composer_created = False
    
    for line in iter(process.stdout.readline, ''):
        if line:
            print(line.strip())
            
            # Look for key indicators
            if "VideoComposer" in line or "composer = VideoComposer" in line:
                composer_created = True
            if "Starting video assembly" in line:
                assembly_started = True
            elif "Video assembly planned" in line:
                assembly_started = False  # Old code
    
    process.wait()
    
    # Final check
    print("\n" + "=" * 60)
    print("📑 TEST SUMMARY")
    print("=" * 60)
    
    result = subprocess.run(
        ['docker', 'exec', 'evergreen-worker-1', 'ls', '-la', f'/app/output/exports/{job_id}.mp4'],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ SUCCESS - Video file created!")
        print(f"   {result.stdout.strip()}")
        
        if assembly_started and composer_created:
            print("✅ NEW FFmpeg assembly code is working!")
        else:
            print("⚠️ Video created but assembly process unclear")
    else:
        print("❌ FAILED - No video file created")
        
        if not assembly_started:
            print("   - Video assembly not started")
        if not composer_created:
            print("   - VideoComposer not detected")

if __name__ == "__main__":
    test_complete_generation()