"""
Example usage of the unified DALL-E 3 and RunwayML pipeline.
"""

import asyncio
import os
from datetime import datetime
from unified_pipeline import create_unified_pipeline, GenerationProvider


async def basic_example():
    """Basic example of generating a video from text."""
    # Create pipeline manager
    pipeline = create_unified_pipeline()
    
    # Generate a single video clip
    result = await pipeline.generate_video_clip(
        prompt="A majestic eagle soaring through mountain peaks at sunset",
        duration=10,
        style="cinematic",
        camera_movement="slow zoom out",
        lighting="golden hour",
        mood="inspiring",
        output_path=f"output/eagle_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    )
    
    if result["success"]:
        print(f"✅ Video generated successfully!")
        print(f"   Image URL: {result['image_url']}")
        print(f"   Video URL: {result['video_url']}")
        print(f"   Local path: {result['video_path']}")
        print(f"   Total cost: ${result['cost']:.3f}")
        print(f"   Duration: {result['total_duration']:.1f} seconds")
    else:
        print(f"❌ Generation failed: {result['error']}")
    
    return result


async def batch_example():
    """Example of generating multiple videos in batch."""
    pipeline = create_unified_pipeline()
    
    # Multiple prompts for different scenes
    prompts = [
        "A serene Japanese garden with cherry blossoms falling gently",
        "A futuristic city skyline with flying cars at night",
        "An underwater coral reef teeming with colorful fish",
    ]
    
    # Generate batch
    results = await pipeline.generate_batch_clips(
        prompts=prompts,
        duration=5,  # Shorter duration for batch
        style="cinematic",
        image_quality="standard",  # Lower quality for faster generation
        enhance_prompt=True
    )
    
    # Print results
    for i, result in enumerate(results):
        print(f"\nClip {i+1}: {prompts[i][:50]}...")
        if result["success"]:
            print(f"  ✅ Success - Video URL: {result['video_url']}")
        else:
            print(f"  ❌ Failed - Error: {result['error']}")
    
    # Get statistics
    stats = pipeline.get_pipeline_stats()
    print(f"\nPipeline Statistics:")
    print(f"  Total runs: {stats['total_runs']}")
    print(f"  Success rate: {stats['success_rate']}%")
    print(f"  Total cost: ${stats['total_cost']:.2f}")
    
    return results


async def style_examples():
    """Example showcasing different visual styles."""
    pipeline = create_unified_pipeline()
    
    base_prompt = "A mysterious figure walking through a foggy forest"
    
    styles = [
        ("noir", "high contrast", "dramatic spotlight", "mysterious"),
        ("cyberpunk", "neon", "neon glow", "dystopian"),
        ("horror", "dim", "flickering light", "terrifying"),
        ("documentary", "natural", "soft daylight", "contemplative"),
    ]
    
    for style, lighting, light_desc, mood in styles:
        print(f"\nGenerating {style} style video...")
        
        result = await pipeline.generate_video_clip(
            prompt=base_prompt,
            duration=5,
            style=style,
            lighting=lighting,
            mood=mood,
            image_size="1024x1024",  # Smaller for examples
            image_quality="standard"
        )
        
        if result["success"]:
            print(f"  ✅ {style} video generated: {result['video_url']}")
        else:
            print(f"  ❌ {style} failed: {result['error']}")


async def test_pipeline():
    """Test the pipeline setup and availability."""
    pipeline = create_unified_pipeline()
    
    print("Testing pipeline components...")
    test_results = await pipeline.test_pipeline()
    
    print(f"\nDALL-E 3 available: {'✅' if test_results['dalle3_available'] else '❌'}")
    print(f"RunwayML available: {'✅' if test_results['runway_available'] else '❌'}")
    
    if test_results.get('runway_org_info'):
        print(f"RunwayML credits: {test_results['runway_org_info']}")
    
    if test_results.get('pipeline_test'):
        test = test_results['pipeline_test']
        if test['success']:
            print(f"\n✅ Full pipeline test successful!")
            print(f"   Duration: {test['duration']:.1f} seconds")
            print(f"   Cost: ${test['cost']:.3f}")
        else:
            print(f"\n❌ Pipeline test failed: {test['error']}")
    
    return test_results


async def custom_provider_example():
    """Example using specific providers."""
    # Force DALL-E 3 for image generation
    pipeline = create_unified_pipeline(default_provider=GenerationProvider.DALLE3)
    
    result = await pipeline.generate_video_clip(
        prompt="A steampunk airship floating above Victorian London",
        duration=10,
        image_provider=GenerationProvider.DALLE3,  # Explicitly use DALL-E 3
        style="retro",
        camera_movement="slow pan right",
        lighting="foggy atmosphere",
        mood="adventurous"
    )
    
    return result


async def main():
    """Run examples based on command line argument."""
    import sys
    
    if len(sys.argv) > 1:
        example = sys.argv[1]
        
        if example == "basic":
            await basic_example()
        elif example == "batch":
            await batch_example()
        elif example == "styles":
            await style_examples()
        elif example == "test":
            await test_pipeline()
        elif example == "custom":
            await custom_provider_example()
        else:
            print(f"Unknown example: {example}")
            print("Available examples: basic, batch, styles, test, custom")
    else:
        # Run test by default
        await test_pipeline()


if __name__ == "__main__":
    # Ensure output directory exists
    os.makedirs("output", exist_ok=True)
    
    # Run the examples
    asyncio.run(main())