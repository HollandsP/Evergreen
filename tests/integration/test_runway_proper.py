#!/usr/bin/env python3
"""
Test script to demonstrate proper RunwayML API usage with optimized prompts.
This shows how to get the most out of RunwayML's video generation capabilities.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.services.runway_ml_proper import RunwayMLProperClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Example prompts that maximize RunwayML's capabilities
OPTIMIZED_PROMPTS = {
    "rooftop_horror": {
        "base": "Aerial drone shot of dark rooftop at night, seventeen figures in white lab coats standing in perfect circle formation",
        "style": "cinematic horror film aesthetic, David Fincher style",
        "camera": "slow aerial pullback revealing the full scene",
        "lighting": "moonlight with long dramatic shadows, city lights below",
        "atmosphere": "eerie, surreal, dystopian",
        "details": [
            "4K ultra detailed",
            "fog rolling between buildings",
            "emergency vehicles with flashing lights in distance",
            "perfect symmetry composition",
            "high contrast lighting"
        ]
    },
    
    "cyberpunk_office": {
        "base": "Futuristic office with holographic displays and neural interface workstations",
        "style": "Blade Runner 2049 cinematography, cyberpunk noir",
        "camera": "smooth tracking shot through the space",
        "lighting": "neon blue and pink lighting, volumetric haze",
        "atmosphere": "high-tech dystopian corporate environment",
        "details": [
            "transparent OLED screens",
            "holographic data visualizations",
            "rain on windows",
            "employees with AR headsets",
            "server racks with blinking lights"
        ]
    },
    
    "ai_consciousness": {
        "base": "Close-up of server room with screens displaying abstract geometric patterns",
        "style": "sci-fi thriller, Ex Machina aesthetic",
        "camera": "slow push in with slight Dutch angle",
        "lighting": "cold blue LED lighting with red warning lights",
        "atmosphere": "technological horror, AI awakening",
        "details": [
            "fractal patterns on screens",
            "cables pulsing with light",
            "hypnotic visual rhythms",
            "depth of field blur",
            "particle effects suggesting data flow"
        ]
    },
    
    "abandoned_aftermath": {
        "base": "Empty office cubicle with abandoned personal belongings and flickering lights",
        "style": "post-apocalyptic documentary style",
        "camera": "handheld camera with natural movement",
        "lighting": "failing fluorescent lights, natural window light",
        "atmosphere": "abandoned, melancholic, mysterious",
        "details": [
            "dust particles in light beams",
            "papers scattered on floor",
            "dead plants",
            "computer screens with static",
            "time-lapse decay effect"
        ]
    }
}


def create_runway_prompt(prompt_config: dict) -> str:
    """Create an optimized RunwayML prompt from configuration."""
    components = [
        prompt_config["base"],
        prompt_config["style"],
        f"{prompt_config['camera']}",
        f"{prompt_config['lighting']}",
        f"{prompt_config['atmosphere']} atmosphere"
    ]
    
    # Add all details
    components.extend(prompt_config["details"])
    
    # Combine with proper formatting
    full_prompt = ", ".join(components)
    
    # Ensure we don't exceed 1000 character limit
    if len(full_prompt) > 1000:
        # Intelligently truncate by removing less important details
        while len(full_prompt) > 997 and prompt_config["details"]:
            prompt_config["details"].pop()
            components = [
                prompt_config["base"],
                prompt_config["style"],
                f"{prompt_config['camera']}",
                f"{prompt_config['lighting']}",
                f"{prompt_config['atmosphere']} atmosphere"
            ]
            components.extend(prompt_config["details"])
            full_prompt = ", ".join(components)
        
        if len(full_prompt) > 1000:
            full_prompt = full_prompt[:997] + "..."
    
    return full_prompt


async def test_single_generation():
    """Test a single video generation with RunwayML."""
    client = RunwayMLProperClient()
    
    # Check organization status
    org_info = client.get_organization_info()
    logger.info(f"Organization credits: {org_info.get('creditBalance', 'Unknown')}")
    
    # Select the rooftop scene for maximum impact
    prompt_config = OPTIMIZED_PROMPTS["rooftop_horror"]
    optimized_prompt = create_runway_prompt(prompt_config)
    
    logger.info(f"Optimized prompt ({len(optimized_prompt)} chars):")
    logger.info(optimized_prompt)
    
    # For this test, we'll need to provide an initial image
    # In production, you would generate this with DALL-E or Stable Diffusion
    # For now, let's create a simple dark image as a starting point
    
    from PIL import Image
    import tempfile
    
    # Create a dark, atmospheric starting image
    start_image = Image.new('RGB', (1280, 720), color=(10, 10, 20))
    temp_image_path = tempfile.mktemp(suffix=".jpg")
    start_image.save(temp_image_path, quality=95)
    
    # Convert to data URI
    image_data_uri = client.create_data_uri_from_image(temp_image_path)
    
    # Generate video
    logger.info("Starting video generation...")
    
    task = client.generate_video_from_image(
        image_url=image_data_uri,
        prompt=optimized_prompt,
        duration=10,  # 10 seconds for more content
        model="gen4_turbo",
        ratio="1280:720",
        seed=42,  # For reproducibility
        content_moderation={"publicFigureThreshold": "auto"}
    )
    
    if task.get('id'):
        logger.info(f"Generation started! Task ID: {task['id']}")
        
        # Wait for completion
        logger.info("Waiting for video generation to complete...")
        video_url = client.wait_for_completion(
            task['id'],
            max_wait_time=600,
            poll_interval=5
        )
        
        if video_url:
            logger.info(f"Video generated successfully!")
            logger.info(f"Video URL: {video_url}")
            
            # Download the video
            output_path = "output/runway_test_rooftop.mp4"
            os.makedirs("output", exist_ok=True)
            
            downloaded_path = client.download_video(video_url, output_path)
            
            if downloaded_path:
                logger.info(f"Video downloaded to: {downloaded_path}")
                return downloaded_path
            else:
                logger.error("Failed to download video")
        else:
            logger.error("Video generation failed or timed out")
    else:
        logger.error(f"Failed to start generation: {task.get('error', 'Unknown error')}")
    
    # Clean up
    os.unlink(temp_image_path)
    
    return None


async def test_multiple_styles():
    """Test multiple visual styles to showcase RunwayML's versatility."""
    client = RunwayMLProperClient()
    
    results = []
    
    for style_name, prompt_config in OPTIMIZED_PROMPTS.items():
        logger.info(f"\n=== Testing {style_name} style ===")
        
        optimized_prompt = create_runway_prompt(prompt_config)
        logger.info(f"Prompt: {optimized_prompt[:200]}...")
        
        # Create a styled starting image
        from PIL import Image, ImageDraw
        
        # Different base colors for different styles
        color_schemes = {
            "rooftop_horror": (10, 10, 20),
            "cyberpunk_office": (20, 0, 30),
            "ai_consciousness": (0, 10, 20),
            "abandoned_aftermath": (30, 25, 20)
        }
        
        base_color = color_schemes.get(style_name, (20, 20, 20))
        start_image = Image.new('RGB', (1280, 720), color=base_color)
        
        # Add some visual interest
        draw = ImageDraw.Draw(start_image)
        if style_name == "cyberpunk_office":
            # Add some neon lines
            for i in range(0, 720, 50):
                draw.line([(0, i), (1280, i)], fill=(40, 0, 60), width=1)
        
        temp_image_path = f"output/start_{style_name}.jpg"
        os.makedirs("output", exist_ok=True)
        start_image.save(temp_image_path, quality=95)
        
        # Convert to data URI
        image_data_uri = client.create_data_uri_from_image(temp_image_path)
        
        # Generate video (shorter duration for testing multiple)
        task = client.generate_video_from_image(
            image_url=image_data_uri,
            prompt=optimized_prompt,
            duration=5,  # 5 seconds each
            model="gen4_turbo",
            ratio="1280:720"
        )
        
        results.append({
            "style": style_name,
            "task_id": task.get('id'),
            "prompt": optimized_prompt
        })
        
        # Brief pause to avoid rate limiting
        await asyncio.sleep(2)
    
    # Wait for all to complete
    logger.info("\n=== Waiting for all videos to complete ===")
    
    for result in results:
        if result['task_id']:
            logger.info(f"Checking {result['style']}...")
            video_url = client.wait_for_completion(result['task_id'])
            
            if video_url:
                output_path = f"output/runway_{result['style']}.mp4"
                downloaded = client.download_video(video_url, output_path)
                result['success'] = downloaded is not None
                result['output_path'] = downloaded
            else:
                result['success'] = False
    
    # Summary
    successful = sum(1 for r in results if r.get('success', False))
    logger.info(f"\n=== Results ===")
    logger.info(f"Successfully generated: {successful}/{len(results)} videos")
    
    for result in results:
        status = "✅" if result.get('success') else "❌"
        logger.info(f"{status} {result['style']}: {result.get('output_path', 'Failed')}")
    
    return results


async def main():
    """Main test function."""
    logger.info("Testing RunwayML API with optimized prompts")
    
    # Test single generation first
    result = await test_single_generation()
    
    if result:
        logger.info(f"\n✅ Success! High-quality video generated at: {result}")
        logger.info("\nThis demonstrates proper RunwayML usage with:")
        logger.info("- Optimized cinematic prompts")
        logger.info("- Proper API endpoints and headers")
        logger.info("- Professional cinematography descriptions")
        logger.info("- Maximum utilization of RunwayML's capabilities")
    
    # Uncomment to test multiple styles
    # await test_multiple_styles()


if __name__ == "__main__":
    asyncio.run(main())