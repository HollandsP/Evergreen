#!/usr/bin/env python3
"""
Integrated workflow example showing how to use the prompt optimization system
with the existing DALL-E 3 and RunwayML services.

This demonstrates the complete pipeline from prompt optimization to content generation.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.prompts import PromptOptimizer, OptimizationConfig
from src.services.dalle3_client import OpenAIImageGenerator
from src.services.runway_client import RunwayClient


async def demonstrate_integrated_workflow():
    """
    Demonstrate complete workflow using prompt optimization with AI services.
    """
    print("🎬 INTEGRATED AI CONTENT GENERATION WORKFLOW")
    print("Using optimized prompts with DALL-E 3 → RunwayML pipeline")
    print("=" * 60)
    
    # Step 1: Configure prompt optimizer for "The Descent" style
    print("\n📝 Step 1: Configuring Prompt Optimizer")
    
    config = OptimizationConfig(
        target_style="cinematic",
        camera_movement_preference="smooth",
        duration_range=(4.0, 6.0),
        resolution="1792x1024",  # HD landscape for DALL-E 3
        consistency_mode=True,
        ensure_moderation_safe=True,
        add_technical_specs=True,
        enhance_lighting=True
    )
    
    optimizer = PromptOptimizer(config)
    print(f"✅ Optimizer configured for {config.target_style} style")
    
    # Step 2: Create narrative sequence
    print("\n📚 Step 2: Creating Narrative Sequence")
    
    story_prompts = [
        "Modern tech company office with employees at workstations",
        "Same office space after hours, empty and dark", 
        "Hidden access panel behind server equipment",
        "Underground data center with AI server infrastructure"
    ]
    
    print(f"📖 Optimizing {len(story_prompts)} story beats...")
    
    # Optimize all prompts for consistency
    sequence_results = optimizer.create_prompt_sequence(
        story_prompts, 
        narrative_flow=True
    )
    
    print(f"✅ Generated {len(sequence_results)} optimized prompt pairs")
    
    # Step 3: Initialize AI services
    print("\n🤖 Step 3: Initializing AI Services")
    
    try:
        # Initialize DALL-E 3 client
        dalle3_client = OpenAIImageGenerator()
        dalle3_available = await dalle3_client.test_connection()
        print(f"🎨 DALL-E 3: {'✅ Connected' if dalle3_available else '❌ Unavailable (using stub)'}")
        
    except Exception as e:
        print(f"🎨 DALL-E 3: ❌ Failed to initialize ({e})")
        dalle3_client = None
        dalle3_available = False
    
    try:
        # Initialize RunwayML client
        runway_client = RunwayClient()
        runway_available = runway_client.validate_api_key()
        print(f"🎥 RunwayML: {'✅ Connected' if runway_available else '❌ Using simulation mode'}")
        
    except Exception as e:
        print(f"🎥 RunwayML: ❌ Failed to initialize ({e})")
        runway_client = None
        runway_available = False
    
    # Step 4: Generate content for each scene
    print("\n🎬 Step 4: Generating Content")
    
    generated_content = []
    
    for i, result in enumerate(sequence_results):
        scene_num = i + 1
        print(f"\n--- Scene {scene_num}/{len(sequence_results)} ---")
        print(f"Original: {story_prompts[i]}")
        print(f"Duration: {result.estimated_duration:.1f}s")
        
        scene_data = {
            "scene_id": scene_num,
            "original_prompt": story_prompts[i],
            "optimized_image_prompt": result.optimized_image_prompt,
            "optimized_video_prompt": result.optimized_video_prompt,
            "duration": result.estimated_duration,
            "camera_movement": result.camera_movement,
            "style": result.style_applied
        }
        
        # Generate image with DALL-E 3
        if dalle3_client:
            print(f"🎨 Generating image with DALL-E 3...")
            
            image_result = await dalle3_client.generate_image(
                prompt=result.optimized_image_prompt,
                size=config.resolution,
                quality="hd",
                style="vivid",
                enhance_for_video=False  # Already optimized by our system
            )
            
            if image_result["success"]:
                scene_data["image_generation"] = {
                    "status": "success",
                    "url": image_result["original_url"],
                    "resized_path": image_result["resized_path"],
                    "revised_prompt": image_result["revised_prompt"],
                    "cost": image_result["cost"],
                    "generation_time": image_result["generation_time"]
                }
                print(f"  ✅ Image generated (${image_result['cost']:.3f}, {image_result['generation_time']:.1f}s)")
                print(f"  📁 Saved to: {image_result['resized_path']}")
                
                # Generate video with RunwayML using the generated image
                if runway_client:
                    print(f"🎥 Generating video with RunwayML...")
                    
                    video_job = runway_client.generate_video(
                        prompt=result.optimized_video_prompt,
                        duration=result.estimated_duration,
                        resolution="1920x1080",
                        fps=24,
                        style=result.style_applied,
                        camera_movement=result.camera_movement
                    )
                    
                    if video_job:
                        scene_data["video_generation"] = {
                            "status": video_job["status"],
                            "job_id": video_job["id"],
                            "prompt": video_job["prompt"],
                            "duration": video_job["duration"],
                            "camera_movement": video_job.get("camera_movement"),
                            "estimated_time": video_job.get("estimated_time", 0)
                        }
                        print(f"  ✅ Video job submitted (ID: {video_job['id']})")
                        print(f"  ⏱️  Estimated completion: {video_job.get('estimated_time', 'unknown')}s")
                    else:
                        scene_data["video_generation"] = {"status": "failed", "error": "Job submission failed"}
                        print(f"  ❌ Video generation failed")
                        
            else:
                scene_data["image_generation"] = {
                    "status": "failed", 
                    "error": image_result.get("error", "Unknown error")
                }
                print(f"  ❌ Image generation failed: {image_result.get('error', 'Unknown error')}")
        
        generated_content.append(scene_data)
    
    # Step 5: Monitor video generation progress
    print("\n⏳ Step 5: Monitoring Video Generation")
    
    video_jobs = [
        scene for scene in generated_content 
        if scene.get("video_generation", {}).get("status") == "processing"
    ]
    
    if video_jobs and runway_client:
        print(f"📊 Monitoring {len(video_jobs)} video generation jobs...")
        
        for scene in video_jobs:
            job_id = scene["video_generation"]["job_id"]
            print(f"🎥 Checking Scene {scene['scene_id']} (Job {job_id})...")
            
            try:
                status = runway_client.get_generation_status(job_id)
                scene["video_generation"].update(status)
                
                if status["status"] == "completed":
                    print(f"  ✅ Video completed: {status.get('video_url', 'No URL')}")
                elif status["status"] == "failed":
                    print(f"  ❌ Video failed: {status.get('error', 'Unknown error')}")
                else:
                    progress = status.get("progress", 0)
                    print(f"  🔄 Progress: {progress}%")
                    
            except Exception as e:
                print(f"  ❌ Status check failed: {e}")
    
    # Step 6: Generate summary report
    print("\n📊 Step 6: Generation Summary")
    
    # Calculate costs and timing
    total_image_cost = sum(
        scene.get("image_generation", {}).get("cost", 0) 
        for scene in generated_content
    )
    
    total_image_time = sum(
        scene.get("image_generation", {}).get("generation_time", 0) 
        for scene in generated_content
    )
    
    total_video_duration = sum(scene["duration"] for scene in generated_content)
    
    successful_images = sum(
        1 for scene in generated_content 
        if scene.get("image_generation", {}).get("status") == "success"
    )
    
    successful_videos = sum(
        1 for scene in generated_content 
        if scene.get("video_generation", {}).get("status") == "completed"
    )
    
    print(f"🎬 Content Generation Complete!")
    print(f"📈 Success Rate:")
    print(f"  Images: {successful_images}/{len(generated_content)} ({successful_images/len(generated_content)*100:.1f}%)")
    print(f"  Videos: {successful_videos}/{len(generated_content)} ({successful_videos/len(generated_content)*100:.1f}%)")
    
    print(f"💰 Costs:")
    print(f"  DALL-E 3: ${total_image_cost:.3f}")
    print(f"  RunwayML: Estimated based on duration")
    
    print(f"⏱️  Timing:")
    print(f"  Image Generation: {total_image_time:.1f}s total")
    print(f"  Video Duration: {total_video_duration:.1f}s total")
    
    print(f"🎯 Quality:")
    print(f"  Moderation Safe: {all(r.moderation_safe for r in sequence_results)}")
    print(f"  Style Consistency: {config.target_style}")
    print(f"  Camera Movements: Optimized for RunwayML")
    
    # Step 7: Export production data
    print("\n💾 Step 7: Exporting Production Data")
    
    # Export API format
    api_export = optimizer.export_prompts_for_api(sequence_results)
    
    # Add generation results
    production_package = {
        "metadata": api_export["metadata"],
        "optimization_config": config.__dict__,
        "dalle3_prompts": api_export["dalle3_prompts"],
        "runway_prompts": api_export["runway_prompts"],
        "generation_results": generated_content,
        "summary": {
            "total_scenes": len(generated_content),
            "successful_images": successful_images,
            "successful_videos": successful_videos,
            "total_image_cost": total_image_cost,
            "total_image_time": total_image_time,
            "total_video_duration": total_video_duration,
            "moderation_safe": all(r.moderation_safe for r in sequence_results)
        }
    }
    
    # Save production package
    output_file = Path(__file__).parent / "production_package.json"
    
    with open(output_file, 'w') as f:
        json.dump(production_package, f, indent=2)
    
    print(f"📦 Production package saved to: {output_file}")
    print(f"🎉 Workflow complete! Ready for post-production assembly.")
    
    return production_package


async def demonstrate_single_scene_workflow():
    """
    Demonstrate workflow for a single scene (faster testing).
    """
    print("\n" + "="*60)
    print("🎬 SINGLE SCENE WORKFLOW (Quick Test)")
    print("="*60)
    
    # Simple single scene test
    optimizer = PromptOptimizer(OptimizationConfig(target_style="cinematic"))
    
    test_prompt = "Corporate boardroom with executives discussing AI strategy"
    print(f"📝 Original: {test_prompt}")
    
    # Optimize prompt
    result = optimizer.optimize_prompt(test_prompt)
    
    print(f"\n🎨 DALL-E 3 Prompt:")
    print(f"  {result.optimized_image_prompt}")
    
    print(f"\n🎥 RunwayML Prompt:")
    print(f"  {result.optimized_video_prompt}")
    
    print(f"\n📊 Metadata:")
    print(f"  Style: {result.style_applied}")
    print(f"  Camera: {result.camera_movement}")
    print(f"  Duration: {result.estimated_duration:.1f}s")
    print(f"  Moderation Safe: {result.moderation_safe}")
    
    # Test with services (if available)
    try:
        dalle3_client = OpenAIImageGenerator()
        
        print(f"\n🤖 Testing with DALL-E 3 service...")
        image_result = await dalle3_client.generate_image(
            prompt=result.optimized_image_prompt,
            size="1792x1024",
            quality="hd"
        )
        
        if image_result["success"]:
            print(f"✅ Image generated successfully!")
            print(f"   Cost: ${image_result['cost']:.3f}")
            print(f"   Time: {image_result['generation_time']:.1f}s")
            print(f"   Path: {image_result['resized_path']}")
            
            # Test RunwayML
            runway_client = RunwayClient()
            print(f"\n🎬 Testing with RunwayML service...")
            
            video_job = runway_client.generate_video(
                prompt=result.optimized_video_prompt,
                duration=result.estimated_duration,
                camera_movement=result.camera_movement
            )
            
            if video_job:
                print(f"✅ Video job submitted!")
                print(f"   Job ID: {video_job['id']}")
                print(f"   Status: {video_job['status']}")
            else:
                print(f"❌ Video job failed")
                
        else:
            print(f"❌ Image generation failed: {image_result.get('error')}")
            
    except Exception as e:
        print(f"❌ Service test failed: {e}")
        print(f"ℹ️  This is expected if API keys are not configured")
    
    print(f"\n🎉 Single scene test complete!")


async def main():
    """Run the integrated workflow demonstrations."""
    try:
        # Run single scene test first (faster)
        await demonstrate_single_scene_workflow()
        
        # Ask user if they want to run full workflow
        print(f"\n" + "="*60)
        response = input("Run full workflow with multiple scenes? (y/N): ")
        
        if response.lower() in ['y', 'yes']:
            await demonstrate_integrated_workflow()
        else:
            print("Skipping full workflow. Use the single scene results above.")
            
    except KeyboardInterrupt:
        print(f"\n⏹️  Workflow interrupted by user")
    except Exception as e:
        print(f"\n❌ Workflow failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🚀 Starting Integrated AI Content Generation Workflow")
    print("This demonstrates the complete pipeline with optimized prompts")
    
    asyncio.run(main())