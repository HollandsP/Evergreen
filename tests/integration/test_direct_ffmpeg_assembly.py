#!/usr/bin/env python3
"""
Direct test of FFmpeg assembly without API
Tests the video generation pipeline components directly
"""
import os
import time
import subprocess
import uuid
from datetime import datetime

# 2-minute showcase script (simplified)
SHOWCASE_SCRIPT = """SCRIPT: AI VIDEO GENERATION - 2 MINUTE SHOWCASE

[0:00 - Opening]
Visual: A futuristic AI laboratory
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

def test_direct_ffmpeg():
    """Test FFmpeg assembly directly in the worker container"""
    print("🎬 Direct FFmpeg Assembly Test")
    print("=" * 60)
    
    # Generate a unique job ID
    job_id = str(uuid.uuid4())
    print(f"📝 Job ID: {job_id}")
    
    # Test command that directly calls the video generation in the worker
    test_cmd = f"""
import sys
sys.path.append('/app')
from workers.tasks.video_generation import process_video_generation

# Test data
job_id = '{job_id}'
script_content = '''{SHOWCASE_SCRIPT}'''
settings = {{
    'voice_type': 'male_calm',
    'style': 'techwear',
    'quality': 'high'
}}

# Direct function calls instead of Celery task
from workers.tasks.video_generation import _parse_script, _generate_voice, _generate_terminal_ui, _generate_visuals, _assemble_video

try:
    # Parse the script
    print("\\n1. Parsing script...")
    parsed_script = _parse_script(script_content)
    print(f"✓ Parsed {{len(parsed_script.get('scenes', []))}} scenes")

    # Generate voice
    print("\\n2. Generating voice...")
    audio_files = []
    for scene in parsed_script['scenes']:
        try:
            audio_file = _generate_voice(scene, settings, job_id)
            if audio_file:
                audio_files.append(audio_file)
        except Exception as e:
            print(f"Voice generation error: {{e}}")

    print(f"✓ Generated {{len(audio_files)}} audio files")

    # Generate terminal UI
    print("\\n3. Generating terminal UI...")
    ui_files = []
    for scene in parsed_script['scenes']:
        try:
            ui_file = _generate_terminal_ui(scene, settings, job_id)
            if ui_file:
                ui_files.append(ui_file)
        except Exception as e:
            print(f"UI generation error: {{e}}")

    print(f"✓ Generated {{len(ui_files)}} UI files")

    # Generate visuals
    print("\\n4. Generating visuals...")
    visual_files = []
    for scene in parsed_script['scenes']:
        try:
            visual_file = _generate_visuals(scene, settings, job_id)
            if visual_file:
                visual_files.append(visual_file)
        except Exception as e:
            print(f"Visual generation error: {{e}}")

    print(f"✓ Generated {{len(visual_files)}} visual files")

    # Assemble video
    print("\\n5. Assembling final video...")
    final_video = _assemble_video(job_id, parsed_script, settings, audio_files, ui_files, visual_files)
    print(f"\\n✅ Video generation completed!")
    print(f"Final video: {{final_video}}")
except Exception as e:
    print(f"\\n❌ Error: {{e}}")
    import traceback
    traceback.print_exc()
"""
    
    print("\n🚀 Starting video generation in worker container...")
    print("This will test all components:")
    print("  - Script parsing")
    print("  - Voice synthesis (ElevenLabs)")
    print("  - Terminal UI animations")
    print("  - Visual generation (Runway stub)")
    print("  - FFmpeg assembly")
    print("\n" + "-" * 60)
    
    # Execute in worker container
    cmd = ["docker", "exec", "-t", "evergreen-worker-1", "python3", "-c", test_cmd]
    
    # Start the process
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    # Monitor output in real-time
    start_time = time.time()
    assembly_detected = False
    composer_detected = False
    
    print("\n📊 Monitoring generation progress...")
    print("-" * 60)
    
    for line in iter(process.stdout.readline, ''):
        if line:
            line = line.strip()
            
            # Print progress updates
            if any(keyword in line for keyword in ["Starting", "Generating", "Creating", "Assembling"]):
                print(f"  {line}")
            
            # Look for key indicators
            if "Starting video assembly" in line:
                print("\n🎯 NEW FFmpeg assembly code detected!")
                assembly_detected = True
            elif "Video assembly planned" in line:
                print("\n⚠️ OLD placeholder code still in use")
                assembly_detected = False
            elif "VideoComposer" in line:
                print("✓ VideoComposer class instantiated")
                composer_detected = True
            elif "error" in line.lower() or "failed" in line.lower():
                print(f"❌ Error: {line}")
            elif "completed" in line.lower() and "successfully" in line:
                print(f"✅ {line}")
    
    # Wait for completion
    process.wait()
    elapsed = time.time() - start_time
    
    print("\n" + "=" * 60)
    print(f"⏱️ Total time: {elapsed:.1f} seconds")
    
    # Check output files
    print("\n🔍 Checking output files...")
    
    # Check for generated files
    check_files = [
        f"/app/output/audio/{job_id}_*.mp3",
        f"/app/output/ui/{job_id}_*.mp4",
        f"/app/output/visuals/{job_id}_*.mp4",
        f"/app/output/exports/{job_id}.mp4"
    ]
    
    for pattern in check_files:
        cmd = ["docker", "exec", "evergreen-worker-1", "bash", "-c", f"ls -la {pattern} 2>/dev/null || echo 'No files found'"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(f"\n{pattern}:")
        print(result.stdout.strip())
    
    # Final validation
    print("\n" + "=" * 60)
    print("📑 TEST SUMMARY")
    print("=" * 60)
    
    if assembly_detected and composer_detected:
        print("✅ SUCCESS - New FFmpeg assembly code is working!")
        
        # Check if final video exists
        final_check = ["docker", "exec", "evergreen-worker-1", "ls", "-la", f"/app/output/exports/{job_id}.mp4"]
        result = subprocess.run(final_check, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Final video created: {result.stdout.strip()}")
            
            # Get video info
            probe_cmd = ["docker", "exec", "evergreen-worker-1", "ffprobe", "-v", "error", 
                        "-show_entries", "format=duration,size", "-of", "default=noprint_wrappers=1:nokey=1",
                        f"/app/output/exports/{job_id}.mp4"]
            probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
            
            if probe_result.returncode == 0:
                lines = probe_result.stdout.strip().split('\n')
                if len(lines) >= 2:
                    size_mb = float(lines[0]) / (1024 * 1024)
                    duration = float(lines[1])
                    print(f"  Duration: {duration:.1f} seconds")
                    print(f"  Size: {size_mb:.1f} MB")
        else:
            print("⚠️ Final video not found - assembly may have failed")
    else:
        print("❌ FAILED - FFmpeg assembly not working properly")
        if not assembly_detected:
            print("  - Still using old placeholder code")
        if not composer_detected:
            print("  - VideoComposer not instantiated")
    
    print("=" * 60)

if __name__ == "__main__":
    test_direct_ffmpeg()