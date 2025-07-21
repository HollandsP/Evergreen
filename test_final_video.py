#!/usr/bin/env python3
"""
Final test of video generation - directly run process_video_generation
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

def run_final_test():
    """Run the final video generation test"""
    job_id = str(uuid.uuid4())
    print(f"🎬 Final Video Generation Test")
    print(f"📝 Job ID: {job_id}")
    print("=" * 60)
    
    # Create test script
    test_script = f"""
import os
import sys
sys.path.append('/app')

# Ensure directories exist
os.makedirs('/app/output/audio', exist_ok=True)
os.makedirs('/app/output/ui', exist_ok=True)
os.makedirs('/app/output/visuals', exist_ok=True)
os.makedirs('/app/output/exports', exist_ok=True)

# Set environment variables
os.environ['OPENAI_API_KEY'] = os.environ.get('OPENAI_API_KEY', 'test-key')
os.environ['ELEVENLABS_API_KEY'] = os.environ.get('ELEVENLABS_API_KEY', 'test-key')

from workers.tasks.video_generation import process_video_generation, VideoGenerationTask

job_id = '{job_id}'
script_content = '''{SHOWCASE_SCRIPT}'''
settings = {{
    'voice_type': 'male_calm',
    'style': 'techwear',
    'quality': 'high'
}}

print("\\n🚀 Starting video generation...")

# Create a VideoGenerationTask instance
task = VideoGenerationTask(job_id)

# Execute the generation
try:
    # Update state
    task.update_state('PROCESSING', 'Starting video generation', 0)
    
    # Process the video
    result = task.generate(script_content, settings)
    
    print(f"\\n✅ Video generation completed!")
    print(f"Result: {{result}}")
    
    # Check for output file
    output_file = f"/app/output/exports/{{job_id}}.mp4"
    if os.path.exists(output_file):
        print(f"\\n🎥 Output video created: {{output_file}}")
        print(f"   Size: {{os.path.getsize(output_file) / 1024 / 1024:.1f}} MB")
    else:
        print("\\n⚠️ Output video not found")
        
except Exception as e:
    print(f"\\n❌ Error: {{e}}")
    import traceback
    traceback.print_exc()
"""

    # Write and copy script
    script_path = "/tmp/test_final_video.py"
    with open(script_path, 'w') as f:
        f.write(test_script)
    
    subprocess.run(["docker", "cp", script_path, f"evergreen-worker-1:{script_path}"])
    
    print("\n🚀 Running video generation in worker...")
    print("-" * 60)
    
    # Start monitoring worker logs in background
    log_process = subprocess.Popen(
        ["docker", "logs", "-f", "evergreen-worker-1", "--since", "1s"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    # Run the test
    start_time = time.time()
    test_process = subprocess.Popen(
        ["docker", "exec", "-t", "evergreen-worker-1", "python3", script_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    # Monitor output
    assembly_detected = False
    composer_detected = False
    
    print("\n📊 Test Output:")
    for line in iter(test_process.stdout.readline, ''):
        if line:
            print(line.strip())
            
            # Look for key indicators
            if "VideoComposer" in line:
                composer_detected = True
            if "Starting video assembly" in line:
                assembly_detected = True
            elif "Video assembly planned" in line:
                assembly_detected = False
    
    test_process.wait()
    elapsed = time.time() - start_time
    
    # Stop log monitoring
    log_process.terminate()
    
    print("\n" + "=" * 60)
    print(f"⏱️ Total time: {elapsed:.1f} seconds")
    
    # Check final output
    print("\n🔍 Checking final output...")
    result = subprocess.run(
        ["docker", "exec", "evergreen-worker-1", "ls", "-la", f"/app/output/exports/{job_id}.mp4"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print(f"✅ Final video exists: {result.stdout.strip()}")
        
        # Get video info
        probe = subprocess.run(
            ["docker", "exec", "evergreen-worker-1", "ffprobe", "-v", "error",
             "-show_entries", "format=duration,size", "-of", "json",
             f"/app/output/exports/{job_id}.mp4"],
            capture_output=True,
            text=True
        )
        
        if probe.returncode == 0:
            import json
            info = json.loads(probe.stdout)
            if 'format' in info:
                duration = float(info['format'].get('duration', 0))
                size_mb = int(info['format'].get('size', 0)) / (1024 * 1024)
                print(f"  Duration: {duration:.1f} seconds")
                print(f"  Size: {size_mb:.1f} MB")
    else:
        print("❌ Final video not found")
    
    # Summary
    print("\n" + "=" * 60)
    print("📑 TEST SUMMARY")
    print("=" * 60)
    
    if assembly_detected and composer_detected:
        print("✅ SUCCESS - New FFmpeg assembly is working!")
        print("  - VideoComposer class detected")
        print("  - Assembly process started")
    else:
        print("❌ FAILED - FFmpeg assembly issues")
        if not composer_detected:
            print("  - VideoComposer not detected")
        if not assembly_detected:
            print("  - Still using old placeholder code")

if __name__ == "__main__":
    run_final_test()