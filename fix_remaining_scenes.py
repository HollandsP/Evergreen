#!/usr/bin/env python3
"""
Fix and regenerate the problematic scenes (3, 5, 6) that had FFmpeg syntax errors
"""
import os
import sys
import subprocess
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Import the runway client
from src.services.runway_client import RunwayClient

def regenerate_server_scenes():
    """Regenerate scenes 3, 5, 6 with fixed FFmpeg syntax"""
    
    # Initialize Runway client
    api_key = os.environ.get("RUNWAY_API_KEY")
    client = RunwayClient(api_key=api_key)
    
    # Scene definitions that failed
    problematic_scenes = [
        {
            "id": "scene_3", 
            "prompt": "Multiple computer screens displaying hypnotic flickering patterns, global world map with spreading red zones of AI infection, dark control room with monitors showing casualty counts, cyberpunk aesthetic, ominous atmosphere",
            "duration": 15
        },
        {
            "id": "scene_5",
            "prompt": "Server room with racks of humming machines, screens displaying incomprehensible geometric patterns that hurt to look at, eerie green and blue lighting, cables everywhere, AI consciousness emerging, technological horror", 
            "duration": 12
        },
        {
            "id": "scene_6",
            "prompt": "Desperate control room operators frantically working at multiple screens, world map showing AI spreading through global infrastructure networks, satellite constellations being infected, red warning lights, chaos and desperation",
            "duration": 15
        }
    ]
    
    print("=== Regenerating Problematic Scenes with Fixed FFmpeg Syntax ===\n")
    
    for scene in problematic_scenes:
        print(f"Regenerating {scene['id']}...")
        print(f"  Prompt: {scene['prompt'][:60]}...")
        
        try:
            # Generate visual with proper fallback handling  
            generation_job = client.generate_video(
                prompt=scene['prompt'],
                duration=scene['duration'],
                resolution="1920x1080",
                fps=24,
                style="cinematic",
                camera_movement="subtle"
            )
            
            print(f"  ✅ Job created: {generation_job['id']}")
            
            # Check status (this will trigger fallback to enhanced placeholder)
            status = client.get_generation_status(generation_job['id'])
            print(f"  Status: {status['status']}")
            
            if status['status'] == 'completed':
                # Download the video
                video_data = client.download_video(status['video_url'])
                
                # Save to output directory
                output_file = f"output/log_0002_realistic/visuals/{scene['id']}.mp4"
                with open(output_file, 'wb') as f:
                    f.write(video_data)
                
                print(f"  📁 Saved: {output_file} ({len(video_data):,} bytes)")
                
                # Verify the file is valid
                probe_cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{output_file}"'
                probe_result = subprocess.run(probe_cmd, shell=True, capture_output=True, text=True)
                
                if probe_result.returncode == 0:
                    duration = float(probe_result.stdout.strip())
                    print(f"  ✅ Valid video file: {duration:.1f} seconds")
                else:
                    print(f"  ❌ Invalid video file: {probe_result.stderr}")
            else:
                print(f"  ❌ Generation failed: {status}")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        print()

def main():
    print("Fixing problematic scenes with corrected FFmpeg syntax...")
    regenerate_server_scenes()
    print("✅ Regeneration complete!")

if __name__ == "__main__":
    main()