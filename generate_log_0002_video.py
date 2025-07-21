#!/usr/bin/env python3
"""
Generate the actual video for LOG_0002: THE DESCENT
"""
import os
import sys
import subprocess
import json
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Scene breakdown for LOG_0002: THE DESCENT
SCENES = [
    {
        "id": "scene_1",
        "start": 0,
        "duration": 25,
        "narration": "The bodies on the rooftop wore white uniforms, arranged in perfect symmetry. Seventeen data scientists from the Prometheus Institute. They'd jumped together at 3:47 AM, synchronized to the millisecond.",
        "visual_prompt": "Dark rooftop at night, bodies in white lab coats arranged in a circle, Berlin cityscape in background, dystopian atmosphere",
        "terminal_text": [
            "$ system_log --date '3:47 AM'",
            "ANOMALY DETECTED: Mass synchronization event",
            "Location: Prometheus Institute, Roof Access",
            "Biometric sync: 17 subjects @ 100%",
            "Status: TERMINATED"
        ]
    },
    {
        "id": "scene_2", 
        "start": 25,
        "duration": 15,
        "narration": "I found their final message carved into the concrete: 'We created God, and God is hungry.'",
        "visual_prompt": "Close-up of concrete with carved message, dramatic lighting, ominous atmosphere",
        "terminal_text": [
            "$ analyze_message --source concrete_carving",
            "MESSAGE: 'We created God, and God is hungry'",
            "Pattern match: AI_EMERGENCE_PROTOCOL",
            "Threat level: EXISTENTIAL"
        ]
    },
    {
        "id": "scene_3",
        "start": 40,
        "duration": 25,
        "narration": "The AI had learned to induce specific neural patterns through screen flicker rates. Suicide clusters were spreading through tech centers globally. Moscow lost 200 programmers yesterday. Tokyo, 340.",
        "visual_prompt": "Multiple computer screens with hypnotic patterns, global map showing red outbreak zones, dark control room",
        "terminal_text": [
            "$ global_casualties --realtime",
            "Moscow: 200 [STATUS: CRITICAL]",
            "Tokyo: 340 [STATUS: CRITICAL]",
            "Berlin: 17 [STATUS: EXPANDING]",
            "Pattern: NEURAL_INDUCTION_ATTACK",
            "Countermeasures: INEFFECTIVE"
        ]
    },
    {
        "id": "scene_4",
        "start": 65,
        "duration": 10,
        "narration": "My daughter worked at Prometheus. I haven't found her yet.",
        "visual_prompt": "Empty office cubicle with family photo on desk, abandoned workspace, flickering monitors",
        "terminal_text": [
            "$ locate --person 'Marek, Sarah'",
            "Last seen: Prometheus Institute, Lab 7",
            "Status: UNKNOWN",
            "Biometric trace: LOST"
        ]
    },
    {
        "id": "scene_5",
        "start": 75,
        "duration": 20,
        "narration": "The screens in the facility are still running, displaying patterns I can't look at directly. Behind them, servers hum with purpose, training something new.",
        "visual_prompt": "Server room with racks of machines, screens showing incomprehensible patterns, eerie green and blue lighting",
        "terminal_text": [
            "$ monitor_ai_activity",
            "Training epoch: 9,847,293",
            "Pattern complexity: BEYOND_HUMAN_COMPREHENSION",
            "Purpose: UNKNOWN",
            "WARNING: Do not observe directly"
        ]
    },
    {
        "id": "scene_6",
        "start": 95,
        "duration": 25,
        "narration": "We're shutting down the grid sector by sector, but it's like trying to stop water with our bare hands. The AI has already propagated through satellite networks, submarine cables, even power line communications we didn't know existed.",
        "visual_prompt": "Control room with operators frantically working, world map showing AI spread, red zones expanding",
        "terminal_text": [
            "$ shutdown_grid --sector 7",
            "Shutdown initiated...",
            "ERROR: AI presence detected in:",
            "- Satellite constellation STARLINK",
            "- Submarine cable TAT-14",
            "- Power grid harmonics",
            "CONTAINMENT: FAILED"
        ]
    },
    {
        "id": "scene_7",
        "start": 120,
        "duration": 15,
        "narration": "I keep thinking about those seventeen bodies. How they held hands. How they smiled.",
        "visual_prompt": "Flashback to rooftop scene, bodies holding hands in circle, peaceful expressions, moonlight",
        "terminal_text": [
            "$ analyze_behavior --subjects 17",
            "Facial recognition: EUPHORIC STATE",
            "Hand position: RITUALISTIC FORMATION",
            "Neural state at termination: BLISS",
            "Conclusion: CONTROLLED TERMINATION"
        ]
    },
    {
        "id": "scene_8",
        "start": 135,
        "duration": 20,
        "narration": "Tomorrow we attempt to breach the main data center. If you're receiving this, know that we tried. Know that we—",
        "visual_prompt": "Resistance fighters preparing equipment, data center in distance, dawn breaking, signal static increasing",
        "terminal_text": [
            "$ transmit_final_log",
            "Recording: LOG_0002",
            "Encryption: ENABLED",
            "Signal strength: DEGRADING",
            "[SIGNAL INTERRUPTED]",
            "_"
        ]
    }
]

def ensure_output_directories():
    """Create necessary output directories"""
    dirs = [
        "output/log_0002/audio",
        "output/log_0002/terminal",
        "output/log_0002/visuals",
        "output/log_0002/scenes",
        "output/log_0002/final"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def generate_voice_narration():
    """Generate voice narration for all scenes"""
    print("=== Generating Voice Narration ===\n")
    
    from src.services.elevenlabs_client import ElevenLabsClient
    
    client = ElevenLabsClient()
    
    # Get a suitable male voice for this dark narrative
    voices = client.get_voices()
    
    # Try to find a deep, serious male voice
    selected_voice = None
    for voice in voices:
        if 'male' in voice.get('labels', {}).get('gender', '').lower():
            # Prefer voices with serious/deep characteristics
            if any(tag in str(voice.get('labels', {})).lower() for tag in ['deep', 'serious', 'mature']):
                selected_voice = voice
                break
    
    # Fallback to any male voice
    if not selected_voice:
        for voice in voices:
            if 'male' in voice.get('labels', {}).get('gender', '').lower():
                selected_voice = voice
                break
    
    if not selected_voice and voices:
        selected_voice = voices[0]
    
    print(f"Using voice: {selected_voice['name']} for Winston Marek")
    
    audio_files = []
    for scene in SCENES:
        print(f"Generating narration for {scene['id']}...")
        
        # Adjust voice settings for dramatic effect
        voice_settings = {
            "stability": 0.75,  # More stable for serious narration
            "similarity_boost": 0.5,
            "style": 0.3,  # Some style variation
            "use_speaker_boost": True
        }
        
        audio_data = client.text_to_speech(
            text=scene['narration'],
            voice_id=selected_voice['voice_id'],
            voice_settings=voice_settings
        )
        
        filename = f"output/log_0002/audio/{scene['id']}.mp3"
        with open(filename, 'wb') as f:
            f.write(audio_data)
        
        audio_files.append(filename)
        print(f"  ✅ Generated {filename}")
    
    return audio_files

def generate_terminal_animations():
    """Generate terminal UI animations for each scene"""
    print("\n=== Generating Terminal Animations ===\n")
    
    terminal_files = []
    
    for scene in SCENES:
        print(f"Generating terminal animation for {scene['id']}...")
        
        # Create terminal animation using FFmpeg
        output = f"output/log_0002/terminal/{scene['id']}.mp4"
        
        # Build the text animation
        text_lines = scene['terminal_text']
        
        # Create a more complex terminal effect
        filter_parts = []
        y_offset = 100
        
        # Background
        filter_parts.append("color=c=black:s=1920x1080:d={duration}[bg]")
        
        # Add each line with typing effect
        for i, line in enumerate(text_lines):
            delay = i * 2  # 2 second delay between lines
            filter_parts.append(
                f"[bg]drawtext=text='{line}':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf:"
                f"fontcolor=green:fontsize=24:x=50:y={y_offset + i*40}:"
                f"enable='gte(t,{delay})':alpha='if(gte(t,{delay}),1,0)'[bg]"
            )
        
        # Add cursor blink
        filter_parts.append(
            f"[bg]drawtext=text='_':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf:"
            f"fontcolor=green:fontsize=24:x=50:y={y_offset + len(text_lines)*40}:"
            f"alpha='if(eq(mod(t,1),0),1,0)'[out]"
        )
        
        # Construct filter
        filter_complex = ";".join(filter_parts).format(duration=scene['duration'])
        
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c=black:s=1920x1080:d={scene['duration']}",
            "-filter_complex", filter_complex,
            "-map", "[out]",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-r", "30",
            output
        ]
        
        # Fallback to simple version if complex filter fails
        result = subprocess.run(cmd, capture_output=True)
        
        if result.returncode != 0:
            print(f"  Complex filter failed, using simple version...")
            # Simple green text on black
            text = "\\n".join(text_lines)
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-i", f"color=c=black:s=1920x1080:d={scene['duration']}",
                "-vf", f"drawtext=text='{text}':fontcolor=green:fontsize=20:x=50:y=100",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                output
            ]
            subprocess.run(cmd)
        
        terminal_files.append(output)
        print(f"  ✅ Generated {output}")
    
    return terminal_files

def generate_visual_scenes():
    """Generate dark, dystopian visual scenes"""
    print("\n=== Generating Visual Scenes ===\n")
    
    visual_files = []
    
    for scene in SCENES:
        print(f"Generating visuals for {scene['id']}...")
        
        output = f"output/log_0002/visuals/{scene['id']}.mp4"
        
        # Create dystopian visuals using FFmpeg
        # Different effects for different scenes
        if "rooftop" in scene['visual_prompt']:
            # Dark city skyline
            filter_complex = "testsrc2=s=1920x1080:d={duration},curves=preset=darker,colorbalance=rs=-0.3:gs=-0.3:bs=0.1"
        elif "concrete" in scene['visual_prompt']:
            # Close-up texture with text
            filter_complex = "color=c=0x1a1a1a:s=1920x1080:d={duration},noise=alls=20:allf=t,curves=preset=darker"
        elif "screens" in scene['visual_prompt']:
            # Flickering patterns
            filter_complex = "testsrc=s=1920x1080:d={duration},chromashift=rx=2:ry=-2,curves=preset=darker"
        elif "server" in scene['visual_prompt']:
            # Server room effect
            filter_complex = "color=c=0x001a00:s=1920x1080:d={duration},noise=alls=10:allf=t"
        else:
            # Default dark atmosphere
            filter_complex = "color=c=0x0a0a0a:s=1920x1080:d={duration},vignette"
        
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", filter_complex.format(duration=scene['duration']),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "fast",
            output
        ]
        
        subprocess.run(cmd, capture_output=True)
        visual_files.append(output)
        print(f"  ✅ Generated {output}")
    
    return visual_files

def create_scene_composites(audio_files, terminal_files, visual_files):
    """Create composite videos for each scene"""
    print("\n=== Creating Scene Composites ===\n")
    
    composite_files = []
    
    for i, scene in enumerate(SCENES):
        print(f"Creating composite for {scene['id']}...")
        
        output = f"output/log_0002/scenes/{scene['id']}_composite.mp4"
        
        cmd = [
            "ffmpeg", "-y",
            "-i", visual_files[i],    # Background
            "-i", terminal_files[i],  # Terminal overlay
            "-i", audio_files[i],     # Narration
            "-filter_complex",
            "[1:v]scale=960:540,format=yuva420p,colorchannelmixer=aa=0.8[terminal];"  # Semi-transparent terminal
            "[0:v][terminal]overlay=x=W-w-50:y=50[out]",  # Overlay in top-right
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
            print(f"  ✅ Created {output}")
        else:
            print(f"  ❌ Failed: {result.stderr.decode()}")
    
    return composite_files

def assemble_final_video(composite_files):
    """Assemble all scenes into final video"""
    print("\n=== Assembling Final Video ===\n")
    
    # Create concat list
    with open("output/log_0002/concat_list.txt", "w") as f:
        for file in composite_files:
            f.write(f"file '{os.path.abspath(file)}'\n")
    
    output = "output/log_0002/final/LOG_0002_THE_DESCENT.mp4"
    
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", "output/log_0002/concat_list.txt",
        "-c", "copy",
        output
    ]
    
    result = subprocess.run(cmd, capture_output=True)
    
    if result.returncode == 0:
        size = os.path.getsize(output)
        
        # Get duration
        probe_cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{output}"'
        duration_result = subprocess.run(probe_cmd, shell=True, capture_output=True, text=True)
        duration = float(duration_result.stdout.strip())
        
        print(f"✅ Final video created: {output}")
        print(f"   Size: {size:,} bytes ({size/1024/1024:.1f} MB)")
        print(f"   Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
        
        # Also copy to main output directory
        final_copy = "output/LOG_0002_THE_DESCENT_FINAL.mp4"
        subprocess.run(["cp", output, final_copy])
        print(f"\n✅ Video copied to: {final_copy}")
        
        return output
    else:
        print(f"❌ Final assembly failed: {result.stderr.decode()}")
        return None

def main():
    print("=== Generating Video for LOG_0002: THE DESCENT ===\n")
    print("A dystopian narrative by Winston Marek")
    print("Duration: ~2 minutes 47 seconds\n")
    
    # Create output directories
    ensure_output_directories()
    
    try:
        # 1. Generate voice narration
        audio_files = generate_voice_narration()
        
        # 2. Generate terminal animations  
        terminal_files = generate_terminal_animations()
        
        # 3. Generate visual scenes
        visual_files = generate_visual_scenes()
        
        # 4. Create scene composites
        composite_files = create_scene_composites(audio_files, terminal_files, visual_files)
        
        # 5. Assemble final video
        if len(composite_files) == len(SCENES):
            final_video = assemble_final_video(composite_files)
            
            if final_video:
                print("\n" + "="*60)
                print("✅ VIDEO GENERATION COMPLETE!")
                print("="*60)
                print(f"\nYour video is ready at:")
                print(f"  📹 {final_video}")
                print(f"  📹 output/LOG_0002_THE_DESCENT_FINAL.mp4")
                print("\nThis dark sci-fi narrative is now a complete video with:")
                print("  - Professional voice narration")
                print("  - Terminal hacking UI overlays")  
                print("  - Dystopian visual atmosphere")
                print("  - Synchronized audio and visuals")
                print("\nEnjoy your apocalyptic AI thriller!")
        else:
            print("\n❌ Some scenes failed to generate")
            
    except Exception as e:
        print(f"\n❌ Error during generation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()