#!/usr/bin/env python3
"""
Simple test for FFmpeg assembly functionality
"""
import os
import sys
import subprocess

# Add app directory to path
sys.path.append('/app')

def test_ffmpeg_basic():
    """Test basic FFmpeg functionality"""
    print("🎬 Testing basic FFmpeg commands...")
    
    # Test 1: Check FFmpeg version
    print("\n1. Checking FFmpeg version:")
    try:
        result = subprocess.run(
            ["docker", "exec", "evergreen-worker", "ffmpeg", "-version"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print("✅ FFmpeg is installed")
            print(f"   Version: {result.stdout.split()[2]}")
        else:
            print("❌ FFmpeg not found")
            return
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Test 2: Create a test video
    print("\n2. Creating test video:")
    try:
        cmd = [
            "docker", "exec", "evergreen-worker", "ffmpeg",
            "-f", "lavfi", "-i", "testsrc=duration=2:size=640x480:rate=30",
            "-f", "lavfi", "-i", "sine=frequency=1000:duration=2",
            "-c:v", "libx264", "-preset", "ultrafast",
            "-c:a", "aac",
            "-y", "/tmp/test_video.mp4"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Test video created successfully")
        else:
            print(f"❌ Failed to create test video: {result.stderr}")
            return
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Test 3: Check video info
    print("\n3. Checking video info:")
    try:
        cmd = [
            "docker", "exec", "evergreen-worker", "ffprobe",
            "-v", "error", "-show_entries", "format=duration,size",
            "-of", "default=noprint_wrappers=1", "/tmp/test_video.mp4"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Video info retrieved:")
            print(f"   {result.stdout.strip()}")
        else:
            print(f"❌ Failed to get video info")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Test overlay filter
    print("\n4. Testing overlay filter:")
    try:
        # Create background
        cmd1 = [
            "docker", "exec", "evergreen-worker", "ffmpeg",
            "-f", "lavfi", "-i", "color=c=blue:s=1920x1080:d=2",
            "-c:v", "libx264", "-preset", "ultrafast",
            "-y", "/tmp/background.mp4"
        ]
        subprocess.run(cmd1, capture_output=True)
        
        # Create overlay
        cmd2 = [
            "docker", "exec", "evergreen-worker", "ffmpeg",
            "-f", "lavfi", "-i", "color=c=red:s=640x360:d=2",
            "-c:v", "libx264", "-preset", "ultrafast",
            "-y", "/tmp/overlay.mp4"
        ]
        subprocess.run(cmd2, capture_output=True)
        
        # Test overlay
        cmd3 = [
            "docker", "exec", "evergreen-worker", "ffmpeg",
            "-i", "/tmp/background.mp4", "-i", "/tmp/overlay.mp4",
            "-filter_complex", "[1:v]scale=640:360[pip];[0:v][pip]overlay=x=W-w-50:y=H-h-50",
            "-c:v", "libx264", "-preset", "ultrafast",
            "-y", "/tmp/overlay_test.mp4"
        ]
        
        result = subprocess.run(cmd3, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Overlay filter works correctly")
        else:
            print(f"❌ Overlay filter failed: {result.stderr[:200]}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n✅ Basic FFmpeg tests completed!")

def test_video_composer():
    """Test VideoComposer class directly"""
    print("\n\n🎥 Testing VideoComposer class...")
    
    try:
        # Import the VideoComposer
        cmd = ["docker", "exec", "evergreen-worker", "python3", "-c", """
import sys
sys.path.append('/app')
from workers.tasks.video_generation import VideoComposer

# Create test data
parsed_script = {
    'title': 'Test Video',
    'total_duration': 10,
    'scenes': [
        {
            'timestamp': '0:00',
            'timestamp_seconds': 0,
            'title': 'Scene 1',
            'visual_descriptions': ['Test visual'],
            'narration': ['Test narration'],
            'onscreen_text': ['Test text']
        }
    ]
}

# Create composer
composer = VideoComposer('test_job', parsed_script, {})
print("✅ VideoComposer created successfully")

# Test timeline building
timeline = composer.build_timeline([], [], [])
print(f"✅ Timeline built with {len(timeline)} entries")
"""]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(result.stdout)
        else:
            print(f"❌ VideoComposer test failed: {result.stderr}")
    except Exception as e:
        print(f"❌ Error testing VideoComposer: {e}")

if __name__ == "__main__":
    test_ffmpeg_basic()
    test_video_composer()