#!/usr/bin/env python3
"""
Generate real test media files for video pipeline testing
"""
import os
import sys
import subprocess
import asyncio
import json
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Test script content
TEST_SCRIPT = """SCRIPT: TEST VIDEO - The Terminal
 
[0:00 - Opening Scene]
Visual: Black screen fading to a terminal window
Narration: "Welcome to the world of command line interfaces."
ON-SCREEN TEXT: $ echo "Hello, World!"
Hello, World!

[0:10 - Basic Commands]
Visual: Terminal showing file operations
Narration: "Let's explore some basic terminal commands."
ON-SCREEN TEXT: $ ls -la
total 24
drwxr-xr-x  3 user  staff   96 Jan 21 10:00 .
drwxr-xr-x  5 user  staff  160 Jan 21 09:00 ..
-rw-r--r--  1 user  staff  512 Jan 21 10:00 README.md

[0:20 - Advanced Operations]
Visual: Terminal showing git operations
Narration: "Now let's look at version control with git."
ON-SCREEN TEXT: $ git status
On branch main
Your branch is up to date with 'origin/main'.

[0:30 - Closing]
Visual: Terminal window slowly fading to black
Narration: "The terminal: where productivity meets power."
ON-SCREEN TEXT: $ exit
"""

def ensure_directories():
    """Create necessary directories"""
    dirs = [
        "output/test_media/audio",
        "output/test_media/terminal",
        "output/test_media/visuals",
        "output/test_media/final"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def generate_voice_audio():
    """Generate real voice audio using ElevenLabs"""
    print("Generating voice audio with ElevenLabs...")
    
    from src.services.elevenlabs_client import ElevenLabsClient
    
    client = ElevenLabsClient()
    
    # Get available voices first
    voices = client.get_voices()
    
    # Try to find a suitable male voice
    male_voice_id = None
    for voice in voices:
        if 'male' in voice.get('labels', {}).get('gender', '').lower():
            male_voice_id = voice['voice_id']
            print(f"  Using voice: {voice['name']} ({voice['voice_id']})")
            break
    
    # Fallback to first available voice
    if not male_voice_id and voices:
        male_voice_id = voices[0]['voice_id']
        print(f"  Using fallback voice: {voices[0]['name']}")
    
    if not male_voice_id:
        raise Exception("No voices available")
    
    # Generate audio for each narration
    narrations = [
        ("scene_0", "Welcome to the world of command line interfaces."),
        ("scene_1", "Let's explore some basic terminal commands."),
        ("scene_2", "Now let's look at version control with git."),
        ("scene_3", "The terminal: where productivity meets power.")
    ]
    
    audio_files = []
    for scene_id, text in narrations:
        print(f"  Generating audio for {scene_id}...")
        audio_data = client.text_to_speech(
            text=text,
            voice_id=male_voice_id
        )
        
        filename = f"output/test_media/audio/{scene_id}.mp3"
        with open(filename, 'wb') as f:
            f.write(audio_data)
        audio_files.append(filename)
        print(f"  ✅ Generated {filename}")
    
    return audio_files

def generate_terminal_animations():
    """Generate terminal UI animations"""
    print("\nGenerating terminal animations...")
    
    # Import within Docker container context
    cmd = """docker exec evergreen-worker-1 python -c "
import sys
sys.path.insert(0, '/app')
from workers.effects.terminal_effects import TerminalRenderer, AnimationSequence, TerminalTheme

# Create renderer
renderer = TerminalRenderer(
    width=1920,
    height=1080,
    theme=TerminalTheme.DARK,
    font_size=24
)

# Define animation sequences
sequences = [
    {
        'name': 'scene_0',
        'commands': ['$ echo \\"Hello, World!\\"', 'Hello, World!'],
        'duration': 5.0
    },
    {
        'name': 'scene_1', 
        'commands': [
            '$ ls -la',
            'total 24',
            'drwxr-xr-x  3 user  staff   96 Jan 21 10:00 .',
            'drwxr-xr-x  5 user  staff  160 Jan 21 09:00 ..',
            '-rw-r--r--  1 user  staff  512 Jan 21 10:00 README.md'
        ],
        'duration': 6.0
    },
    {
        'name': 'scene_2',
        'commands': [
            '$ git status',
            'On branch main',
            'Your branch is up to date with \\'origin/main\\'.'
        ],
        'duration': 5.0
    },
    {
        'name': 'scene_3',
        'commands': ['$ exit'],
        'duration': 3.0
    }
]

# Generate videos
for seq in sequences:
    animation = AnimationSequence(
        lines=seq['commands'],
        typing_speed=0.05,
        line_delay=0.5
    )
    
    frames = renderer.render_animation(animation)
    video_path = f'/app/output/test_media/terminal/{seq[\\"name\\"]}.mp4'
    renderer.export_video(frames, video_path, duration=seq['duration'])
    print(f'Generated {video_path}')
"
"""
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print("  ✅ Terminal animations generated")
    else:
        print(f"  ❌ Error: {result.stderr}")
        # Fallback: create test patterns
        print("  Creating fallback test patterns...")
        for i in range(4):
            output = f"output/test_media/terminal/scene_{i}.mp4"
            cmd = f'ffmpeg -y -f lavfi -i "color=c=black:s=1920x1080:d=5,drawtext=text=\'Terminal Scene {i}\':fontsize=60:fontcolor=green:x=(w-text_w)/2:y=(h-text_h)/2" -c:v libx264 -pix_fmt yuv420p {output}'
            subprocess.run(cmd, shell=True)
            print(f"  ✅ Created fallback {output}")

def generate_visual_scenes():
    """Generate visual scenes using FFmpeg test patterns"""
    print("\nGenerating visual scenes with FFmpeg...")
    
    # Create test video patterns for each scene
    scenes = [
        ("scene_0", "testsrc2=s=1920x1080:d=5,fade=in:0:30", "Fade in pattern"),
        ("scene_1", "color=c=0x1a1a2e:s=1920x1080:d=6,drawtext=text='File Operations':fontsize=80:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2", "Dark blue with text"),
        ("scene_2", "color=c=0x16213e:s=1920x1080:d=5,drawtext=text='Git Status':fontsize=80:fontcolor=0x00ff00:x=(w-text_w)/2:y=(h-text_h)/2", "Dark with green text"),
        ("scene_3", "testsrc2=s=1920x1080:d=3,fade=out:60:30", "Fade out pattern")
    ]
    
    visual_files = []
    for scene_id, filter_complex, description in scenes:
        output = f"output/test_media/visuals/{scene_id}.mp4"
        cmd = f'ffmpeg -y -f lavfi -i "{filter_complex}" -c:v libx264 -pix_fmt yuv420p -preset fast {output}'
        
        print(f"  Generating {scene_id} ({description})...")
        result = subprocess.run(cmd, shell=True, capture_output=True)
        
        if result.returncode == 0:
            visual_files.append(output)
            print(f"  ✅ Generated {output}")
        else:
            print(f"  ❌ Error generating {scene_id}: {result.stderr.decode()}")
    
    return visual_files

def verify_media_files():
    """Verify all generated media files"""
    print("\nVerifying generated media files...")
    
    directories = {
        "Audio": "output/test_media/audio",
        "Terminal": "output/test_media/terminal",
        "Visuals": "output/test_media/visuals"
    }
    
    all_valid = True
    
    for media_type, directory in directories.items():
        print(f"\n{media_type} files:")
        if os.path.exists(directory):
            for file in sorted(os.listdir(directory)):
                filepath = os.path.join(directory, file)
                size = os.path.getsize(filepath)
                
                # Use ffprobe to get duration
                cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{filepath}"'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                
                if result.returncode == 0 and size > 1000:  # At least 1KB
                    duration = float(result.stdout.strip() or 0)
                    print(f"  ✅ {file}: {size:,} bytes, {duration:.1f}s")
                else:
                    print(f"  ❌ {file}: Invalid or too small ({size} bytes)")
                    all_valid = False
        else:
            print(f"  ❌ Directory not found!")
            all_valid = False
    
    return all_valid

def main():
    print("=== Generating Test Media Files ===\n")
    
    # Ensure directories exist
    ensure_directories()
    
    # Generate all media types
    try:
        # 1. Generate voice audio
        audio_files = generate_voice_audio()
        
        # 2. Generate terminal animations
        generate_terminal_animations()
        
        # 3. Generate visual scenes
        visual_files = generate_visual_scenes()
        
        # 4. Verify all files
        if verify_media_files():
            print("\n✅ All test media files generated successfully!")
            print("\nYou can now test the video assembly pipeline with these files.")
            return 0
        else:
            print("\n⚠️ Some media files may be invalid. Check the output above.")
            return 1
            
    except Exception as e:
        print(f"\n❌ Error generating media files: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())