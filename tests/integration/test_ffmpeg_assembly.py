#!/usr/bin/env python3
"""
Test FFmpeg video assembly with real media files
"""
import os
import sys
import subprocess

def test_ffmpeg_direct():
    """Test FFmpeg assembly directly without the VideoComposer class"""
    print("=== Testing Direct FFmpeg Assembly ===\n")
    
    # Check if media files exist
    audio_files = [
        "output/test_media/audio/scene_0.mp3",
        "output/test_media/audio/scene_1.mp3",
        "output/test_media/audio/scene_2.mp3",
        "output/test_media/audio/scene_3.mp3"
    ]
    
    video_files = [
        "output/test_media/visuals/scene_0.mp4",
        "output/test_media/visuals/scene_1.mp4",
        "output/test_media/visuals/scene_2.mp4",
        "output/test_media/visuals/scene_3.mp4"
    ]
    
    terminal_files = [
        "output/test_media/terminal/scene_0.mp4",
        "output/test_media/terminal/scene_1.mp4",
        "output/test_media/terminal/scene_2.mp4",
        "output/test_media/terminal/scene_3.mp4"
    ]
    
    # Verify all files exist
    all_files_exist = True
    for f in audio_files + video_files + terminal_files:
        if not os.path.exists(f):
            print(f"❌ Missing file: {f}")
            all_files_exist = False
        else:
            size = os.path.getsize(f)
            print(f"✅ Found: {f} ({size:,} bytes)")
    
    if not all_files_exist:
        return
    
    print("\n1. Concatenating audio files...")
    # Create concat list for audio
    with open("output/test_media/audio_concat.txt", "w") as f:
        for audio_file in audio_files:
            f.write(f"file '{os.path.abspath(audio_file)}'\n")
    
    # Concatenate audio files
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", "output/test_media/audio_concat.txt",
        "-c", "copy",
        "output/test_media/combined_audio.mp3"
    ]
    
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode == 0:
        print("✅ Audio concatenated successfully")
    else:
        print(f"❌ Audio concatenation failed: {result.stderr.decode()}")
        return
    
    print("\n2. Creating video with terminal overlay...")
    # Create a simple composite: visual background + terminal overlay
    output_path = "output/test_media/final/simple_composite.mp4"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # First, let's just try combining one scene
    cmd = [
        "ffmpeg", "-y",
        "-i", video_files[0],  # Background video
        "-i", terminal_files[0],  # Terminal overlay
        "-i", audio_files[0],  # Audio
        "-filter_complex",
        "[1:v]scale=960:540[terminal];"  # Scale terminal to half size
        "[0:v][terminal]overlay=x=(W-w)/2:y=(H-h)/2[out]",  # Center overlay
        "-map", "[out]",
        "-map", "2:a",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-shortest",
        output_path
    ]
    
    print("Running FFmpeg composite command...")
    result = subprocess.run(cmd, capture_output=True)
    
    if result.returncode == 0:
        size = os.path.getsize(output_path)
        print(f"✅ Video composite created: {output_path} ({size:,} bytes)")
        
        # Get duration
        cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{output_path}"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            duration = float(result.stdout.strip())
            print(f"✅ Video duration: {duration:.1f} seconds")
    else:
        print(f"❌ FFmpeg composite failed: {result.stderr.decode()}")
        
    print("\n3. Creating full multi-scene video...")
    # Create a more complex video with all scenes
    
    # First, create individual scene composites
    scene_composites = []
    for i in range(4):
        scene_output = f"output/test_media/scene_{i}_composite.mp4"
        
        cmd = [
            "ffmpeg", "-y",
            "-i", video_files[i],
            "-i", terminal_files[i],
            "-i", audio_files[i],
            "-filter_complex",
            "[1:v]scale=960:540[terminal];"
            "[0:v][terminal]overlay=x=(W-w)/2:y=(H-h)/2[out]",
            "-map", "[out]",
            "-map", "2:a",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-shortest",
            scene_output
        ]
        
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode == 0:
            scene_composites.append(scene_output)
            print(f"✅ Created scene {i} composite")
        else:
            print(f"❌ Failed to create scene {i}: {result.stderr.decode()}")
    
    if len(scene_composites) == 4:
        print("\n4. Concatenating all scenes...")
        
        # Create concat list
        with open("output/test_media/scenes_concat.txt", "w") as f:
            for scene_file in scene_composites:
                f.write(f"file '{os.path.abspath(scene_file)}'\n")
        
        final_output = "output/test_media/final/complete_video.mp4"
        
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", "output/test_media/scenes_concat.txt",
            "-c", "copy",
            final_output
        ]
        
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode == 0:
            size = os.path.getsize(final_output)
            print(f"✅ Final video created: {final_output} ({size:,} bytes)")
            
            # Get duration
            cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{final_output}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                duration = float(result.stdout.strip())
                print(f"✅ Total duration: {duration:.1f} seconds")
        else:
            print(f"❌ Final concatenation failed: {result.stderr.decode()}")

def test_simple_overlay():
    """Test a very simple overlay first"""
    print("\n=== Testing Simple Overlay ===\n")
    
    # Create a simple test pattern + text overlay
    output = "output/test_media/final/test_overlay.mp4"
    os.makedirs(os.path.dirname(output), exist_ok=True)
    
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "testsrc=duration=5:size=1920x1080:rate=30",
        "-f", "lavfi", "-i", "color=black:s=960x540:d=5,drawtext=text='Terminal Overlay':fontsize=40:fontcolor=green:x=(w-text_w)/2:y=(h-text_h)/2",
        "-filter_complex", "[0:v][1:v]overlay=x=(W-w)/2:y=(H-h)/2[out]",
        "-map", "[out]",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        output
    ]
    
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode == 0:
        size = os.path.getsize(output)
        print(f"✅ Test overlay created: {output} ({size:,} bytes)")
    else:
        print(f"❌ Test overlay failed: {result.stderr.decode()}")

if __name__ == "__main__":
    # Test simple overlay first
    test_simple_overlay()
    
    # Then test full assembly
    test_ffmpeg_direct()