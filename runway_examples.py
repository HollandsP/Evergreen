#!/usr/bin/env python3
"""
Examples of how to use the improved RunwayML integration for different types of content.
Shows best practices for prompt engineering and video generation.
"""

import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from src.services.runway_ml_proper import RunwayMLProperClient


# Example 1: Horror/Thriller Scene
def generate_horror_scene():
    client = RunwayMLProperClient()
    
    prompt = client.generate_cinematic_prompt(
        base_description="Abandoned hospital corridor with flickering lights and shadows moving",
        style="horror",
        camera_movement="slow tracking shot forward",
        lighting="intermittent fluorescent lighting with deep shadows",
        mood="terrifying and suspenseful",
        details=[
            "peeling paint on walls",
            "medical equipment scattered",
            "fog creeping along floor",
            "something moving in the shadows",
            "handheld camera shake",
            "desaturated color palette"
        ]
    )
    
    return prompt


# Example 2: Sci-Fi Action Scene
def generate_scifi_action():
    client = RunwayMLProperClient()
    
    prompt = client.generate_cinematic_prompt(
        base_description="Futuristic chase scene through neon-lit cyberpunk city streets",
        style="cyberpunk",
        camera_movement="dynamic tracking shot following the action",
        lighting="neon blues and pinks with volumetric fog",
        mood="high-energy and intense",
        details=[
            "flying vehicles weaving between buildings",
            "holographic advertisements",
            "rain-slicked streets reflecting lights",
            "laser weapons firing",
            "motion blur effects",
            "Blade Runner aesthetic"
        ]
    )
    
    return prompt


# Example 3: Nature Documentary
def generate_nature_doc():
    client = RunwayMLProperClient()
    
    prompt = client.generate_cinematic_prompt(
        base_description="Time-lapse of storm clouds forming over mountain range at sunset",
        style="documentary",
        camera_movement="static wide shot with subtle zoom",
        lighting="golden hour transitioning to dramatic storm lighting",
        mood="majestic and awe-inspiring",
        details=[
            "8K ultra high definition",
            "rays of sunlight breaking through clouds",
            "lightning flashes in distance",
            "birds flying in formation",
            "snow-capped peaks",
            "BBC Planet Earth style"
        ]
    )
    
    return prompt


# Example 4: Historical Drama
def generate_historical_drama():
    client = RunwayMLProperClient()
    
    prompt = client.generate_cinematic_prompt(
        base_description="Victorian-era London street scene with horse carriages and gas lamps",
        style="cinematic",
        camera_movement="crane shot descending to street level",
        lighting="gaslight ambiance with fog",
        mood="atmospheric period drama",
        details=[
            "cobblestone streets",
            "people in period clothing",
            "smoke from chimneys",
            "Merchant Ivory production style",
            "muted color grading",
            "authentic historical details"
        ]
    )
    
    return prompt


# Example 5: Abstract/Artistic
def generate_abstract_art():
    client = RunwayMLProperClient()
    
    prompt = client.generate_cinematic_prompt(
        base_description="Abstract visualization of music with flowing colors and geometric shapes",
        style="artistic",
        camera_movement="fluid camera movement through 3D space",
        lighting="luminescent colors emanating from shapes",
        mood="mesmerizing and transcendent",
        details=[
            "particle effects synchronized to rhythm",
            "fractal patterns evolving",
            "iridescent color shifts",
            "depth of field effects",
            "Terrence Malick style abstraction",
            "4K resolution"
        ]
    )
    
    return prompt


# Best Practices for RunwayML Prompts
def print_best_practices():
    print("""
    RunwayML Prompt Engineering Best Practices:
    
    1. **Be Specific About Style**:
       - Reference specific films/directors: "Christopher Nolan style", "Wes Anderson aesthetic"
       - Use cinematography terms: "anamorphic lens", "shallow depth of field"
    
    2. **Describe Camera Movement**:
       - "slow dolly in"
       - "aerial tracking shot"
       - "handheld documentary style"
       - "smooth gimbal movement"
    
    3. **Detail the Lighting**:
       - "golden hour lighting"
       - "film noir high contrast"
       - "soft diffused light"
       - "neon cyberpunk glow"
    
    4. **Include Technical Specs**:
       - "4K ultra detailed"
       - "35mm film aesthetic"
       - "high frame rate slow motion"
       - "anamorphic lens flares"
    
    5. **Set the Mood/Atmosphere**:
       - Use emotional descriptors
       - Describe the feeling you want
       - Reference similar films/scenes
    
    6. **Add Production Value Details**:
       - "professional cinematography"
       - "Hollywood production quality"
       - "award-winning visuals"
       - "cinematic color grading"
    
    7. **Optimize Prompt Length**:
       - Use all 1000 characters wisely
       - Prioritize most important details
       - Remove redundant words
    """)


# Example of using the API
def example_api_usage():
    """Complete example of generating a video with RunwayML."""
    
    client = RunwayMLProperClient()
    
    # 1. Check credits
    org_info = client.get_organization_info()
    credits = org_info.get('creditBalance', 0)
    print(f"Available credits: {credits}")
    
    if credits < 50:
        print("Warning: Low credits! Need at least 50 for a 10-second video")
        return
    
    # 2. Create optimized prompt
    prompt = client.generate_cinematic_prompt(
        base_description="Dystopian city at dawn with resistance fighters on rooftop",
        style="cinematic",
        camera_movement="drone shot circling the fighters",
        lighting="dawn light breaking through smog",
        mood="hopeful yet dangerous",
        details=[
            "post-apocalyptic architecture",
            "makeshift weapons and gear",
            "destroyed buildings in background",
            "atmospheric haze",
            "desaturated color palette",
            "Children of Men cinematography"
        ]
    )
    
    print(f"\nGenerated prompt ({len(prompt)} chars):")
    print(prompt)
    
    # 3. Generate video (need initial image)
    # In production, generate this with DALL-E or Stable Diffusion
    initial_image_url = "https://example.com/initial-frame.jpg"  # Replace with actual image
    
    task = client.generate_video_from_image(
        image_url=initial_image_url,
        prompt=prompt,
        duration=10,
        model="gen4_turbo",
        ratio="1280:720",
        seed=42  # For reproducibility
    )
    
    if task.get('id'):
        print(f"\nVideo generation started! Task ID: {task['id']}")
        
        # 4. Wait for completion
        video_url = client.wait_for_completion(task['id'])
        
        if video_url:
            print(f"\nVideo generated successfully!")
            
            # 5. Download video
            output_path = "output/dystopian_scene.mp4"
            downloaded = client.download_video(video_url, output_path)
            
            if downloaded:
                print(f"Video saved to: {downloaded}")
            else:
                print("Failed to download video")
        else:
            print("Video generation failed")
    else:
        print(f"Failed to start generation: {task.get('error')}")


if __name__ == "__main__":
    print("RunwayML Prompt Examples\n")
    
    examples = {
        "Horror/Thriller": generate_horror_scene(),
        "Sci-Fi Action": generate_scifi_action(),
        "Nature Documentary": generate_nature_doc(),
        "Historical Drama": generate_historical_drama(),
        "Abstract Art": generate_abstract_art()
    }
    
    for genre, prompt in examples.items():
        print(f"\n{genre} Example ({len(prompt)} chars):")
        print("-" * 50)
        print(prompt)
    
    print("\n" + "=" * 70)
    print_best_practices()
    
    # Uncomment to run actual generation (requires credits)
    # example_api_usage()