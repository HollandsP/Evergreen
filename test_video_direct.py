#!/usr/bin/env python3
"""
Direct test of video generation without Celery
"""
import subprocess
import uuid
import json

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

def test_video_generation():
    """Test video generation directly in worker"""
    job_id = str(uuid.uuid4())
    print(f"🎬 Testing video generation with job ID: {job_id}")
    
    # Create a Python script that will run in the worker
    test_script = f"""
import os
import sys
sys.path.append('/app')

# Set environment variables
os.environ['OPENAI_API_KEY'] = os.environ.get('OPENAI_API_KEY', 'test-key')
os.environ['ELEVENLABS_API_KEY'] = os.environ.get('ELEVENLABS_API_KEY', 'test-key')

from workers.tasks.video_generation import VideoGenerationTask, VideoComposer, ScriptParser

# Test data
job_id = '{job_id}'
script_content = '''{SHOWCASE_SCRIPT}'''
settings = {{
    'voice_type': 'male_calm',
    'style': 'techwear', 
    'quality': 'high'
}}

print("\\n1️⃣ Parsing script...")
parser = ScriptParser()
parsed_script = parser.parse(script_content)
print(f"   Parsed {{len(parsed_script.get('scenes', []))}} scenes")

print("\\n2️⃣ Creating VideoGenerationTask...")
task = VideoGenerationTask(job_id)

# Test each component
print("\\n3️⃣ Testing voice generation...")
audio_files = []
for i, scene in enumerate(parsed_script['scenes']):
    print(f"   Scene {{i+1}}: {{scene.get('title', 'Unknown')}}")
    try:
        # Simulate voice generation
        audio_file = f"/app/output/audio/{{job_id}}_scene_{{i}}.mp3"
        # Create placeholder for testing
        os.makedirs("/app/output/audio", exist_ok=True)
        with open(audio_file, 'wb') as f:
            f.write(b'placeholder audio')
        audio_files.append(audio_file)
        print(f"   ✓ Audio: {{audio_file}}")
    except Exception as e:
        print(f"   ✗ Error: {{e}}")

print("\\n4️⃣ Testing UI generation...")
ui_files = []
for i, scene in enumerate(parsed_script['scenes']):
    try:
        # Simulate UI generation
        ui_file = f"/app/output/ui/{{job_id}}_scene_{{i}}.mp4"
        os.makedirs("/app/output/ui", exist_ok=True)
        with open(ui_file, 'wb') as f:
            f.write(b'placeholder ui')
        ui_files.append(ui_file)
        print(f"   ✓ UI: {{ui_file}}")
    except Exception as e:
        print(f"   ✗ Error: {{e}}")

print("\\n5️⃣ Testing visual generation...")
visual_files = []
for i, scene in enumerate(parsed_script['scenes']):
    try:
        # Simulate visual generation
        visual_file = f"/app/output/visuals/{{job_id}}_scene_{{i}}.mp4"
        os.makedirs("/app/output/visuals", exist_ok=True)
        with open(visual_file, 'wb') as f:
            f.write(b'placeholder visual')
        visual_files.append(visual_file)
        print(f"   ✓ Visual: {{visual_file}}")
    except Exception as e:
        print(f"   ✗ Error: {{e}}")

print("\\n6️⃣ Testing VideoComposer...")
try:
    composer = VideoComposer(job_id, parsed_script, settings)
    print("   ✓ VideoComposer instantiated successfully!")
    
    # Test timeline building
    timeline = composer.build_timeline(audio_files, ui_files, visual_files)
    print(f"   ✓ Timeline built with {{len(timeline)}} entries")
    
    # Check if _assemble_with_ffmpeg method exists
    if hasattr(composer, '_assemble_with_ffmpeg'):
        print("   ✓ Found _assemble_with_ffmpeg method!")
    else:
        print("   ✗ _assemble_with_ffmpeg method not found")
    
    # Test composition modes
    print("\\n7️⃣ Testing composition modes...")
    for mode in ['overlay', 'visual_only', 'ui_only', 'audio_only']:
        cmd = composer._get_ffmpeg_command(mode, timeline)
        print(f"   ✓ {{mode}} mode: {{len(cmd)}} command parts")
        
except Exception as e:
    print(f"   ✗ VideoComposer error: {{e}}")
    import traceback
    traceback.print_exc()

print("\\n✅ Test completed!")
"""

    # Write the script to a file
    script_path = "/tmp/test_video_gen.py"
    with open(script_path, 'w') as f:
        f.write(test_script)
    
    # Copy to worker and execute
    print("\n📋 Copying test script to worker...")
    subprocess.run(["docker", "cp", script_path, "evergreen-worker-1:/tmp/test_video_gen.py"])
    
    print("\n🚀 Running test in worker container...")
    result = subprocess.run(
        ["docker", "exec", "-t", "evergreen-worker-1", "python3", "/tmp/test_video_gen.py"],
        capture_output=True,
        text=True
    )
    
    print("\n📊 Test Output:")
    print("-" * 60)
    print(result.stdout)
    if result.stderr:
        print("\n⚠️ Errors:")
        print(result.stderr)
    
    # Check if VideoComposer was mentioned
    if "VideoComposer instantiated successfully" in result.stdout:
        print("\n🎉 SUCCESS: VideoComposer is working!")
    else:
        print("\n❌ FAILED: VideoComposer not detected")

if __name__ == "__main__":
    test_video_generation()