#!/usr/bin/env python3
"""
Complete Pipeline Demonstration

This script demonstrates the complete workflow from text to video using
DALL-E 3 and RunwayML integration with "The Descent" prompts.

Features:
- Complete text-to-video pipeline
- Provider switching demonstration
- Cost tracking and estimation
- Sample content generation
- Performance monitoring
- Error recovery examples

Usage:
    python examples/complete_pipeline_demo.py [--scene-count N] [--duration N] [--preview-only]
"""

import os
import sys
import asyncio
import logging
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.services.unified_pipeline import UnifiedPipelineManager, GenerationProvider
from src.services.dalle3_client import create_dalle3_client
from src.services.runway_ml_proper import RunwayMLProperClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PipelineDemo:
    """Complete pipeline demonstration system."""
    
    def __init__(self, preview_only: bool = False):
        """
        Initialize demo system.
        
        Args:
            preview_only: If True, show estimates and examples without generation
        """
        self.preview_only = preview_only
        self.pipeline = None
        self.results = []
        self.total_estimated_cost = 0.0
        self.total_actual_cost = 0.0
        
        # Load The Descent prompts
        self.prompts = self._load_descent_prompts()
        
        logger.info(f"Pipeline Demo initialized (preview_only={preview_only})")
    
    def _load_descent_prompts(self) -> Dict[str, Any]:
        """Load The Descent prompts from JSON file."""
        prompts_file = Path(__file__).parent / "the_descent_prompts.json"
        
        if prompts_file.exists():
            with open(prompts_file, 'r') as f:
                return json.load(f)
        else:
            # Fallback prompts if file not found
            logger.warning("Prompts file not found, using fallback prompts")
            return {
                "dalle3_prompts": [
                    {
                        "scene_id": 0,
                        "prompt": "Modern tech company office with employees working at computers, cinematic wide shot",
                        "size": "1792x1024",
                        "quality": "hd",
                        "style": "vivid"
                    },
                    {
                        "scene_id": 1,
                        "prompt": "Same office after hours, eerily quiet with only security lighting, cinematic wide shot",
                        "size": "1792x1024",
                        "quality": "hd",
                        "style": "vivid"
                    },
                    {
                        "scene_id": 2,
                        "prompt": "Discovery of hidden underground access behind server room, dramatic cinematic shot",
                        "size": "1792x1024",
                        "quality": "hd",
                        "style": "vivid"
                    }
                ],
                "runway_prompts": [
                    {
                        "scene_id": 0,
                        "text_prompt": "Gentle atmospheric drift, professional cinematic camera movement",
                        "duration": 10.0,
                        "camera_movement": "atmospheric_drift",
                        "style": "cinematic"
                    },
                    {
                        "scene_id": 1,
                        "text_prompt": "Subtle environmental movement, creating tension, cinematic style",
                        "duration": 10.0,
                        "camera_movement": "atmospheric_drift",
                        "style": "cinematic"
                    },
                    {
                        "scene_id": 2,
                        "text_prompt": "Slow reveal and exploration, building suspense, cinematic movement",
                        "duration": 10.0,
                        "camera_movement": "slow_explore",
                        "style": "cinematic"
                    }
                ]
            }
    
    async def run_complete_demo(
        self,
        scene_count: int = 3,
        duration: int = 10,
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run the complete pipeline demonstration.
        
        Args:
            scene_count: Number of scenes to generate
            duration: Duration per scene in seconds
            output_dir: Output directory for generated content
        
        Returns:
            Demo results summary
        """
        start_time = time.time()
        
        # Setup output directory
        if not output_dir:
            output_dir = Path("output") / "pipeline_demo" / datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"🎬 Starting Complete Pipeline Demo")
        logger.info(f"   Scenes: {scene_count}")
        logger.info(f"   Duration: {duration}s per scene")
        logger.info(f"   Output: {output_path}")
        logger.info(f"   Preview Mode: {self.preview_only}")
        
        demo_results = {
            "start_time": datetime.now().isoformat(),
            "config": {
                "scene_count": scene_count,
                "duration": duration,
                "output_dir": str(output_path),
                "preview_only": self.preview_only
            },
            "scenes": [],
            "costs": {
                "estimated": 0.0,
                "actual": 0.0
            },
            "performance": {
                "total_duration": 0.0,
                "avg_per_scene": 0.0
            },
            "errors": [],
            "recommendations": []
        }
        
        try:
            # Step 1: Show cost estimates
            await self._show_cost_estimates(scene_count, duration)
            
            # Step 2: Initialize pipeline
            await self._initialize_pipeline()
            
            # Step 3: Demonstrate provider capabilities
            await self._demonstrate_providers()
            
            # Step 4: Generate scenes
            if not self.preview_only:
                for scene_idx in range(min(scene_count, len(self.prompts["dalle3_prompts"]))):
                    scene_result = await self._generate_scene(
                        scene_idx, duration, output_path
                    )
                    demo_results["scenes"].append(scene_result)
                    
                    if scene_result.get("cost", 0) > 0:
                        demo_results["costs"]["actual"] += scene_result["cost"]
            else:
                # Preview mode - show what would be generated
                for scene_idx in range(min(scene_count, len(self.prompts["dalle3_prompts"]))):
                    preview_result = await self._preview_scene(scene_idx, duration)
                    demo_results["scenes"].append(preview_result)
            
            # Step 5: Generate final summary
            demo_results.update(await self._generate_demo_summary(output_path))
            
        except Exception as e:
            logger.error(f"Demo failed: {e}")
            demo_results["errors"].append(str(e))
        
        # Calculate final metrics
        demo_results["performance"]["total_duration"] = time.time() - start_time
        if demo_results["scenes"]:
            demo_results["performance"]["avg_per_scene"] = (
                demo_results["performance"]["total_duration"] / len(demo_results["scenes"])
            )
        
        # Save demo results
        results_file = output_path / "demo_results.json"
        with open(results_file, 'w') as f:
            json.dump(demo_results, f, indent=2, default=str)
        
        logger.info(f"💾 Demo results saved to: {results_file}")
        
        return demo_results
    
    async def _show_cost_estimates(self, scene_count: int, duration: int) -> None:
        """Show detailed cost estimates for the demo."""
        print("\n" + "="*60)
        print("💰 COST ESTIMATION")
        print("="*60)
        
        # DALL-E 3 costs (as of 2024)
        dalle3_cost_per_image = {
            "standard_1024": 0.04,
            "hd_1024": 0.08,
            "hd_1792": 0.12
        }
        
        # RunwayML costs (estimated)
        runway_cost_per_second = 0.5  # Approximate
        
        # Calculate costs for demo
        image_cost = scene_count * dalle3_cost_per_image["hd_1792"]
        video_cost = scene_count * duration * runway_cost_per_second
        total_estimated = image_cost + video_cost
        
        self.total_estimated_cost = total_estimated
        
        print(f"\n📊 Cost Breakdown for {scene_count} scenes:")
        print(f"   DALL-E 3 Images (HD 1792x1024): {scene_count} × $0.12 = ${image_cost:.2f}")
        print(f"   RunwayML Videos ({duration}s each): {scene_count} × {duration} × $0.50 = ${video_cost:.2f}")
        print(f"   ─────────────────────────────────────────")
        print(f"   TOTAL ESTIMATED COST: ${total_estimated:.2f}")
        
        # Cost comparison scenarios
        print(f"\n📈 Cost Scenarios:")
        scenarios = {
            "Single Test Clip": (1, 5),
            "Short Demo (3 clips)": (3, 10),
            "Full Sequence (8 clips)": (8, 10),
            "Production Quality": (8, 10)
        }
        
        for name, (scenes, dur) in scenarios.items():
            img_cost = scenes * 0.12
            vid_cost = scenes * dur * 0.5
            total = img_cost + vid_cost
            print(f"   {name:20s}: ${total:6.2f} ({scenes} scenes × {dur}s)")
        
        print(f"\n⚠️  Note: Actual RunwayML costs may vary based on:")
        print(f"   • Model selection (Gen4 Turbo vs Gen4)")
        print(f"   • Account credits and pricing tiers")
        print(f"   • Processing complexity")
        
        if not self.preview_only:
            print(f"\n🚨 This demo will incur ACTUAL costs of approximately ${total_estimated:.2f}")
    
    async def _initialize_pipeline(self) -> None:
        """Initialize the unified pipeline."""
        print("\n" + "="*60)
        print("🔧 PIPELINE INITIALIZATION")
        print("="*60)
        
        try:
            # Check environment variables
            openai_key = os.getenv("OPENAI_API_KEY")
            runway_key = os.getenv("RUNWAY_API_KEY")
            
            print(f"\n🔑 API Keys:")
            print(f"   OpenAI API Key: {'✅ Set' if openai_key else '❌ Missing'}")
            print(f"   RunwayML API Key: {'✅ Set' if runway_key else '❌ Missing'}")
            
            if not openai_key or not runway_key:
                if not self.preview_only:
                    raise ValueError("Missing required API keys")
                else:
                    print("   ⚠️  Missing keys - running in preview mode")
            
            # Initialize pipeline
            if not self.preview_only:
                self.pipeline = UnifiedPipelineManager()
                print(f"\n🏗️  Pipeline Components:")
                print(f"   DALL-E 3 Client: {'✅ Ready' if self.pipeline.dalle3_client else '❌ Failed'}")
                print(f"   RunwayML Client: {'✅ Ready' if self.pipeline.runway_client else '❌ Failed'}")
                print(f"   Async Client: {'✅ Ready' if self.pipeline.async_runway_client else '❌ Failed'}")
                
                # Test connections
                if self.pipeline.dalle3_client:
                    try:
                        dalle3_ok = await self.pipeline.dalle3_client.test_connection()
                        print(f"   DALL-E 3 Connection: {'✅ OK' if dalle3_ok else '❌ Failed'}")
                    except Exception as e:
                        print(f"   DALL-E 3 Connection: ❌ Error - {e}")
                
                if self.pipeline.runway_client:
                    try:
                        org_info = self.pipeline.runway_client.get_organization_info()
                        if org_info:
                            print(f"   RunwayML Connection: ✅ OK")
                            print(f"   Organization: {org_info.get('name', 'Unknown')}")
                            if 'credits' in org_info:
                                print(f"   Credits: {org_info['credits']}")
                        else:
                            print(f"   RunwayML Connection: ❌ Failed")
                    except Exception as e:
                        print(f"   RunwayML Connection: ❌ Error - {e}")
            else:
                print(f"\n🔮 Simulated Pipeline (Preview Mode)")
                print(f"   All components would be initialized in real mode")
                
        except Exception as e:
            logger.error(f"Pipeline initialization failed: {e}")
            if not self.preview_only:
                raise
    
    async def _demonstrate_providers(self) -> None:
        """Demonstrate provider capabilities and switching."""
        print("\n" + "="*60)
        print("🔄 PROVIDER DEMONSTRATION")
        print("="*60)
        
        print(f"\n🎨 Image Generation Providers:")
        print(f"   Primary: DALL-E 3 (OpenAI)")
        print(f"   • High-quality image generation")
        print(f"   • Multiple sizes: 1024×1024, 1792×1024, 1024×1792")
        print(f"   • Quality levels: standard, hd")
        print(f"   • Styles: vivid, natural")
        print(f"   • Cost: $0.04-$0.12 per image")
        
        print(f"\n🎥 Video Generation Providers:")
        print(f"   Primary: RunwayML Gen4 Turbo")
        print(f"   • Image-to-video generation")
        print(f"   • Durations: 5s or 10s")
        print(f"   • Multiple aspect ratios")
        print(f"   • Advanced camera movements")
        print(f"   • Cost: ~$0.50 per second")
        
        print(f"\n🔀 Provider Switching Examples:")
        
        # Example 1: Quality vs Cost
        print(f"   1. Quality vs Cost Trade-off:")
        print(f"      Standard Quality: DALL-E standard + RunwayML Gen4 Turbo")
        print(f"      Premium Quality: DALL-E HD + RunwayML Gen4 Turbo")
        print(f"      Cost difference: ~$0.08 per scene")
        
        # Example 2: Speed vs Quality
        print(f"   2. Speed vs Quality:")
        print(f"      Fast Generation: 1024×1024 + 5s videos")
        print(f"      High Quality: 1792×1024 + 10s videos")
        print(f"      Time difference: ~2x processing time")
        
        # Example 3: Fallback scenarios
        print(f"   3. Fallback Scenarios:")
        print(f"      If DALL-E unavailable: Use alternative image generation")
        print(f"      If RunwayML unavailable: Queue for later processing")
        print(f"      Network issues: Automatic retry with exponential backoff")
        
        if self.pipeline and not self.preview_only:
            # Show actual provider status
            print(f"\n📊 Current Provider Status:")
            stats = self.pipeline.get_pipeline_stats()
            print(f"   Pipeline runs: {stats.get('total_runs', 0)}")
            print(f"   Success rate: {stats.get('success_rate', 0)}%")
            print(f"   Total cost: ${stats.get('total_cost', 0):.3f}")
    
    async def _generate_scene(
        self,
        scene_idx: int,
        duration: int,
        output_path: Path
    ) -> Dict[str, Any]:
        """Generate a single scene."""
        print(f"\n🎬 GENERATING SCENE {scene_idx + 1}")
        print("─" * 40)
        
        start_time = time.time()
        
        # Get prompts
        dalle3_prompt = self.prompts["dalle3_prompts"][scene_idx]
        runway_prompt = self.prompts["runway_prompts"][scene_idx]
        
        print(f"📝 Image Prompt: {dalle3_prompt['prompt'][:80]}...")
        print(f"🎥 Video Prompt: {runway_prompt['text_prompt'][:80]}...")
        
        scene_result = {
            "scene_id": scene_idx,
            "start_time": datetime.now().isoformat(),
            "success": False,
            "cost": 0.0,
            "files": {},
            "errors": []
        }
        
        try:
            # Set output file path
            output_file = output_path / f"scene_{scene_idx + 1:02d}.mp4"
            
            # Generate video clip
            result = await self.pipeline.generate_video_clip(
                prompt=dalle3_prompt["prompt"],
                duration=duration,
                image_size=dalle3_prompt["size"],
                image_quality=dalle3_prompt["quality"],
                image_style=dalle3_prompt["style"],
                camera_movement=runway_prompt["camera_movement"],
                style=runway_prompt["style"],
                output_path=str(output_file)
            )
            
            # Update scene result
            scene_result.update({
                "success": result.get("success", False),
                "cost": result.get("cost", 0),
                "duration": time.time() - start_time,
                "image_url": result.get("image_url"),
                "video_url": result.get("video_url"),
                "video_path": result.get("video_path"),
                "revised_prompt": result.get("revised_prompt"),
                "pipeline_result": result
            })
            
            if result.get("success"):
                print(f"✅ Scene {scene_idx + 1} completed successfully")
                print(f"   Cost: ${result.get('cost', 0):.3f}")
                print(f"   Duration: {time.time() - start_time:.1f}s")
                if result.get("video_path"):
                    print(f"   Output: {result['video_path']}")
            else:
                print(f"❌ Scene {scene_idx + 1} failed")
                scene_result["errors"].append(result.get("error", "Unknown error"))
                
        except Exception as e:
            print(f"❌ Scene {scene_idx + 1} error: {e}")
            scene_result["errors"].append(str(e))
            scene_result["duration"] = time.time() - start_time
        
        return scene_result
    
    async def _preview_scene(self, scene_idx: int, duration: int) -> Dict[str, Any]:
        """Preview what would be generated for a scene."""
        dalle3_prompt = self.prompts["dalle3_prompts"][scene_idx]
        runway_prompt = self.prompts["runway_prompts"][scene_idx]
        
        # Estimate costs
        image_cost = 0.12 if dalle3_prompt["quality"] == "hd" else 0.04
        video_cost = duration * 0.5
        total_cost = image_cost + video_cost
        
        print(f"\n🔮 PREVIEW SCENE {scene_idx + 1}")
        print("─" * 40)
        print(f"📝 Image: {dalle3_prompt['prompt']}")
        print(f"🎥 Video: {runway_prompt['text_prompt']}")
        print(f"💰 Estimated Cost: ${total_cost:.2f}")
        print(f"⏱️  Estimated Time: ~3-5 minutes")
        
        return {
            "scene_id": scene_idx,
            "preview": True,
            "estimated_cost": total_cost,
            "estimated_duration": 240,  # 4 minutes average
            "image_prompt": dalle3_prompt["prompt"],
            "video_prompt": runway_prompt["text_prompt"],
            "config": {
                "image_size": dalle3_prompt["size"],
                "image_quality": dalle3_prompt["quality"],
                "video_duration": duration,
                "camera_movement": runway_prompt["camera_movement"]
            }
        }
    
    async def _generate_demo_summary(self, output_path: Path) -> Dict[str, Any]:
        """Generate final demo summary."""
        print("\n" + "="*60)
        print("📊 DEMO SUMMARY")
        print("="*60)
        
        summary = {
            "pipeline_stats": {},
            "performance_metrics": {},
            "cost_analysis": {},
            "generated_content": {},
            "recommendations": []
        }
        
        # Pipeline statistics
        if self.pipeline:
            stats = self.pipeline.get_pipeline_stats()
            summary["pipeline_stats"] = stats
            
            print(f"\n🏭 Pipeline Statistics:")
            print(f"   Total Runs: {stats.get('total_runs', 0)}")
            print(f"   Success Rate: {stats.get('success_rate', 0)}%")
            print(f"   Total Cost: ${stats.get('total_cost', 0):.3f}")
            print(f"   Avg Cost/Run: ${stats.get('average_cost_per_run', 0):.3f}")
        
        # Performance metrics
        successful_scenes = [s for s in self.results if s.get("success")]
        if successful_scenes:
            avg_duration = sum(s.get("duration", 0) for s in successful_scenes) / len(successful_scenes)
            total_cost = sum(s.get("cost", 0) for s in successful_scenes)
            
            summary["performance_metrics"] = {
                "avg_generation_time": avg_duration,
                "total_actual_cost": total_cost,
                "cost_vs_estimate": {
                    "estimated": self.total_estimated_cost,
                    "actual": total_cost,
                    "difference": total_cost - self.total_estimated_cost
                }
            }
            
            print(f"\n⚡ Performance Metrics:")
            print(f"   Avg Generation Time: {avg_duration:.1f}s per scene")
            print(f"   Total Actual Cost: ${total_cost:.3f}")
            print(f"   Cost Accuracy: {abs(total_cost - self.total_estimated_cost) / self.total_estimated_cost * 100:.1f}% difference")
        
        # Generated content summary
        generated_files = list(output_path.glob("*.mp4"))
        summary["generated_content"] = {
            "output_directory": str(output_path),
            "video_files": [str(f.name) for f in generated_files],
            "total_files": len(generated_files)
        }
        
        print(f"\n📁 Generated Content:")
        print(f"   Output Directory: {output_path}")
        print(f"   Video Files: {len(generated_files)}")
        for file in generated_files:
            file_size = file.stat().st_size if file.exists() else 0
            print(f"     • {file.name} ({file_size / 1024 / 1024:.1f} MB)")
        
        # Recommendations
        recommendations = []
        
        if self.preview_only:
            recommendations.extend([
                "Run without --preview-only to generate actual content",
                "Ensure API keys are properly configured",
                "Budget approximately $5-10 for a 3-scene demo"
            ])
        else:
            if successful_scenes:
                recommendations.extend([
                    "Consider batch processing for multiple scenes",
                    "Monitor costs with the pipeline stats",
                    "Use standard quality for testing, HD for production"
                ])
            else:
                recommendations.extend([
                    "Check API key configuration and account balances",
                    "Verify network connectivity",
                    "Try running individual components separately"
                ])
        
        summary["recommendations"] = recommendations
        
        print(f"\n💡 Recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
        
        return summary


async def main():
    """Main demo function."""
    parser = argparse.ArgumentParser(
        description="Complete Pipeline Demonstration"
    )
    parser.add_argument(
        "--scene-count",
        type=int,
        default=3,
        help="Number of scenes to generate (default: 3)"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=10,
        help="Duration per scene in seconds (default: 10)"
    )
    parser.add_argument(
        "--preview-only",
        action="store_true",
        help="Preview mode - show estimates without generation"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Output directory for generated content"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Cost warning
    if not args.preview_only:
        estimated_cost = args.scene_count * (0.12 + args.duration * 0.5)
        print(f"\n⚠️  WARNING: This demo will generate actual content!")
        print(f"   Estimated cost: ${estimated_cost:.2f}")
        print(f"   Scenes: {args.scene_count}")
        print(f"   Duration: {args.duration}s per scene")
        print(f"   Use --preview-only to see estimates without generation")
        
        response = input("\nContinue with actual generation? (y/N): ")
        if response.lower() != 'y':
            print("Exiting. Use --preview-only for cost-free preview.")
            return
    
    # Run demo
    demo = PipelineDemo(preview_only=args.preview_only)
    
    try:
        results = await demo.run_complete_demo(
            scene_count=args.scene_count,
            duration=args.duration,
            output_dir=args.output_dir
        )
        
        print("\n🎉 Demo completed successfully!")
        print(f"📊 Generated {len(results['scenes'])} scenes")
        if not args.preview_only:
            print(f"💰 Total cost: ${results['costs']['actual']:.3f}")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"\n❌ Demo failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())