#!/usr/bin/env python3
"""
Test script to generate sample videos with cinematic visual effects.
"""
import os
import sys
import subprocess
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Enable cinematic mode
os.environ['RUNWAY_CINEMATIC_MODE'] = 'true'

from src.services.runway_client import RunwayClient

def test_cinematic_generation():
    """Test the cinematic visual generation for different scene types."""
    
    # Initialize client
    client = RunwayClient()
    
    # Create output directory
    os.makedirs('output/cinematic_test', exist_ok=True)
    
    # Test scenes
    test_scenes = [
        {
            'name': 'rooftop',
            'prompt': 'Dark Berlin rooftop at night with bodies in white lab coats',
            'duration': 5.0
        },
        {
            'name': 'concrete',
            'prompt': 'Weathered concrete wall with carved message',
            'duration': 5.0
        },
        {
            'name': 'server',
            'prompt': 'Server room with racks of humming machines and screens',
            'duration': 5.0
        },
        {
            'name': 'control',
            'prompt': 'Control room with operators at multiple screens',
            'duration': 5.0
        }
    ]
    
    print("=== Testing Cinematic Visual Generation ===\n")
    
    for scene in test_scenes:
        print(f"Generating {scene['name']} scene...")
        print(f"  Prompt: {scene['prompt']}")
        
        try:
            # Generate video
            job = client.generate_video(
                prompt=scene['prompt'],
                duration=scene['duration'],
                style='cinematic'
            )
            
            print(f"  Job created: {job['id']}")
            
            # Get status (will trigger placeholder generation)
            status = client.get_generation_status(job['id'])
            
            if status['status'] == 'completed':
                # Download video
                video_data = client.download_video(status['video_url'])
                
                # Save to file
                output_path = f"output/cinematic_test/{scene['name']}_cinematic.mp4"
                with open(output_path, 'wb') as f:
                    f.write(video_data)
                
                print(f"  ✅ Saved: {output_path} ({len(video_data):,} bytes)")
                
                # Extract a frame for preview
                frame_path = f"output/cinematic_test/{scene['name']}_frame.jpg"
                cmd = [
                    'ffmpeg', '-y',
                    '-i', output_path,
                    '-vframes', '1',
                    '-ss', '2',
                    frame_path
                ]
                subprocess.run(cmd, capture_output=True)
                print(f"  📸 Frame: {frame_path}")
                
            else:
                print(f"  ❌ Generation failed")
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print()
    
    print("\n=== Comparison Test ===")
    print("\nNow generating basic versions for comparison...\n")
    
    # Disable cinematic mode
    os.environ['RUNWAY_CINEMATIC_MODE'] = 'false'
    
    # Reinitialize client
    client = RunwayClient()
    
    for scene in test_scenes[:1]:  # Just test one scene for comparison
        print(f"Generating basic {scene['name']} scene...")
        
        try:
            job = client.generate_video(
                prompt=scene['prompt'],
                duration=scene['duration'],
                style='cinematic'
            )
            
            status = client.get_generation_status(job['id'])
            
            if status['status'] == 'completed':
                video_data = client.download_video(status['video_url'])
                
                output_path = f"output/cinematic_test/{scene['name']}_basic.mp4"
                with open(output_path, 'wb') as f:
                    f.write(video_data)
                
                print(f"  ✅ Saved: {output_path}")
                
                # Extract frame
                frame_path = f"output/cinematic_test/{scene['name']}_basic_frame.jpg"
                cmd = [
                    'ffmpeg', '-y',
                    '-i', output_path,
                    '-vframes', '1',
                    '-ss', '2',
                    frame_path
                ]
                subprocess.run(cmd, capture_output=True)
                print(f"  📸 Frame: {frame_path}")
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
    
    print("\n✅ Test complete! Check output/cinematic_test/ for results.")
    print("\nCompare:")
    print("  - *_cinematic.mp4 - New cinematic quality visuals")
    print("  - *_basic.mp4 - Original basic visuals")
    print("  - *_frame.jpg - Preview frames")

if __name__ == "__main__":
    test_cinematic_generation()