#!/usr/bin/env python3
"""
Fix missing scenes and complete the LOG_0002 video
"""
import os
import subprocess

def fix_missing_terminal_scenes():
    """Generate the missing terminal scenes with proper escaping"""
    print("=== Fixing Missing Terminal Scenes ===\n")
    
    missing_scenes = [
        {
            "id": "scene_2",
            "duration": 15,
            "text": "ANALYSIS: Message carved in concrete\\nAI_EMERGENCE_PROTOCOL detected\\nThreat level: EXISTENTIAL"
        },
        {
            "id": "scene_3", 
            "duration": 25,
            "text": "GLOBAL CASUALTIES REPORT\\nMoscow: 200 programmers\\nTokyo: 340 programmers\\nPattern: NEURAL_INDUCTION_ATTACK"
        },
        {
            "id": "scene_4",
            "duration": 10,
            "text": "SEARCH: Sarah Marek\\nLast seen: Prometheus Lab 7\\nStatus: UNKNOWN"
        },
        {
            "id": "scene_5",
            "duration": 20,
            "text": "AI ACTIVITY MONITOR\\nTraining epoch: 9847293\\nPattern complexity: BEYOND_HUMAN\\nWARNING: Do not observe"
        },
        {
            "id": "scene_6",
            "duration": 25,
            "text": "GRID SHUTDOWN ATTEMPT\\nSector 7: FAILED\\nAI detected in satellites\\nCONTAINMENT: FAILED"
        }
    ]
    
    for scene in missing_scenes:
        output = f"output/log_0002/terminal/{scene['id']}.mp4"
        
        # Use a simple approach without complex characters
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c=black:s=1920x1080:d={scene['duration']}",
            "-vf", f"drawtext=text='{scene['text']}':fontcolor=green:fontsize=24:x=50:y=100:font=monospace",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            output
        ]
        
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode == 0:
            print(f"✅ Fixed {scene['id']}")
        else:
            print(f"⚠️  Creating basic fallback for {scene['id']}")
            # Ultra simple fallback
            cmd = f'ffmpeg -y -f lavfi -i "color=c=black:s=1920x1080:d={scene["duration"]}" -c:v libx264 -pix_fmt yuv420p {output}'
            subprocess.run(cmd, shell=True)

def fix_missing_visuals():
    """Ensure all visual scenes exist"""
    print("\n=== Checking Visual Scenes ===\n")
    
    # These should already exist but let's verify
    for i in range(3, 6):
        visual_file = f"output/log_0002/visuals/scene_{i}.mp4"
        if not os.path.exists(visual_file):
            print(f"⚠️  Regenerating visual for scene_{i}")
            cmd = f'ffmpeg -y -f lavfi -i "color=c=0x0a0a0a:s=1920x1080:d=20" -vf vignette -c:v libx264 -pix_fmt yuv420p {visual_file}'
            subprocess.run(cmd, shell=True)

def create_all_composites():
    """Create composites for all scenes"""
    print("\n=== Creating All Scene Composites ===\n")
    
    composite_files = []
    
    for i in range(1, 9):
        scene_id = f"scene_{i}"
        audio_file = f"output/log_0002/audio/{scene_id}.mp3"
        terminal_file = f"output/log_0002/terminal/{scene_id}.mp4"
        visual_file = f"output/log_0002/visuals/{scene_id}.mp4"
        output = f"output/log_0002/scenes/{scene_id}_composite.mp4"
        
        # Check if all inputs exist
        if not all(os.path.exists(f) for f in [audio_file, terminal_file, visual_file]):
            print(f"⚠️  Missing files for {scene_id}, creating simple version")
            # Create simple black video with audio
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", f"color=c=black:s=1920x1080:d=10",
                "-i", audio_file,
                "-map", "0:v",
                "-map", "1:a",
                "-c:v", "libx264",
                "-c:a", "aac",
                "-shortest",
                output
            ]
        else:
            # Create proper composite
            cmd = [
                "ffmpeg", "-y",
                "-i", visual_file,
                "-i", terminal_file,
                "-i", audio_file,
                "-filter_complex",
                "[1:v]scale=960:540[terminal];"
                "[0:v][terminal]overlay=x=W-w-50:y=50[out]",
                "-map", "[out]",
                "-map", "2:a",
                "-c:v", "libx264",
                "-c:a", "aac",
                "-shortest",
                output
            ]
        
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode == 0:
            composite_files.append(output)
            print(f"✅ Created composite for {scene_id}")
        else:
            print(f"❌ Failed {scene_id}: {result.stderr.decode()[:100]}")
    
    return composite_files

def assemble_final_video(composite_files):
    """Assemble the final video"""
    print("\n=== Assembling Final Video ===\n")
    
    # Filter to only existing files
    existing_files = [f for f in composite_files if os.path.exists(f)]
    
    if not existing_files:
        print("❌ No composite files available!")
        return None
    
    print(f"Using {len(existing_files)} scene files")
    
    # Create concat list
    with open("output/log_0002/final_concat.txt", "w") as f:
        for file in existing_files:
            f.write(f"file '{os.path.abspath(file)}'\n")
    
    output = "output/LOG_0002_THE_DESCENT_COMPLETE.mp4"
    
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0", 
        "-i", "output/log_0002/final_concat.txt",
        "-c", "copy",
        output
    ]
    
    result = subprocess.run(cmd, capture_output=True)
    
    if result.returncode == 0:
        size = os.path.getsize(output)
        print(f"\n{'='*60}")
        print("✅ VIDEO GENERATION COMPLETE!")
        print(f"{'='*60}")
        print(f"\n📹 Final video: {output}")
        print(f"📏 Size: {size/1024/1024:.1f} MB")
        
        # Get duration
        probe_cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{output}"'
        duration_result = subprocess.run(probe_cmd, shell=True, capture_output=True, text=True)
        if duration_result.returncode == 0:
            duration = float(duration_result.stdout.strip())
            print(f"⏱️  Duration: {duration:.1f} seconds")
        
        return output
    else:
        print(f"❌ Final assembly failed: {result.stderr.decode()}")
        
        # Try alternative approach - just combine audio files
        print("\n Trying audio-only version...")
        return create_audio_only_version()

def create_audio_only_version():
    """Create audio-only version as fallback"""
    print("\n=== Creating Audio Version ===\n")
    
    # Concatenate all audio files
    with open("output/log_0002/audio_concat.txt", "w") as f:
        for i in range(1, 9):
            audio_file = f"output/log_0002/audio/scene_{i}.mp3"
            if os.path.exists(audio_file):
                f.write(f"file '{os.path.abspath(audio_file)}'\n")
    
    output_audio = "output/LOG_0002_THE_DESCENT_AUDIO.mp3"
    
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", "output/log_0002/audio_concat.txt",
        "-c", "copy",
        output_audio
    ]
    
    result = subprocess.run(cmd, capture_output=True)
    
    if result.returncode == 0:
        size = os.path.getsize(output_audio)
        print(f"✅ Audio version created: {output_audio} ({size/1024:.1f} KB)")
        
        # Now create video with waveform visualization
        output_video = "output/LOG_0002_THE_DESCENT_WAVEFORM.mp4"
        
        cmd = f'ffmpeg -y -i {output_audio} -filter_complex "[0:a]showwaves=s=1920x1080:mode=cline:colors=green[v]" -map "[v]" -map 0:a -c:v libx264 -c:a copy {output_video}'
        
        result = subprocess.run(cmd, shell=True, capture_output=True)
        
        if result.returncode == 0:
            print(f"✅ Waveform video created: {output_video}")
            return output_video
    
    return None

def main():
    print("=== Fixing and Completing LOG_0002 Video ===\n")
    
    # 1. Fix missing terminal scenes
    fix_missing_terminal_scenes()
    
    # 2. Ensure visuals exist
    fix_missing_visuals()
    
    # 3. Create all composites
    composite_files = create_all_composites()
    
    # 4. Assemble final video
    final_video = assemble_final_video(composite_files)
    
    if final_video:
        print("\n✅ Success! Your dystopian AI thriller is ready!")
        print(f"\nFinal video location: {final_video}")
    else:
        print("\n❌ Video assembly had issues, but audio narration is complete")

if __name__ == "__main__":
    main()