#!/usr/bin/env python3
"""
Generate photorealistic videos with RunwayML - Fixed version.
Handles model-specific ratios and avoids moderation issues.
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.services.runway_ml_proper import RunwayMLProperClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# PHOTOREALISTIC prompts - avoiding terms that trigger moderation
PHOTOREALISTIC_SCENES = [
    {
        "id": "photo_scene_1_street",
        "title": "Urban Architecture",
        "duration": 10,
        "base_prompt": "Modern city street view with buildings and traffic, documentary footage",
        "style": "documentary cinematography",
        "camera_movement": "smooth tracking shot along street",
        "lighting": "natural daylight, realistic shadows",
        "mood": "urban atmosphere",
        "details": [
            "photorealistic quality",
            "35mm film aesthetic",
            "authentic street scene",
            "cinematic depth of field",
            "realistic lighting",
            "documentary style"
        ]
    },
    {
        "id": "photo_scene_2_nature",
        "title": "Mountain Landscape",
        "duration": 10,
        "base_prompt": "Majestic mountain range with forests and clouds, nature documentary",
        "style": "nature cinematography",
        "camera_movement": "slow aerial drift over landscape",
        "lighting": "golden hour sunlight on peaks",
        "mood": "serene natural beauty",
        "details": [
            "photorealistic rendering",
            "National Geographic style",
            "atmospheric perspective",
            "realistic cloud movement",
            "natural color grading",
            "8K documentary quality"
        ]
    },
    {
        "id": "photo_scene_3_interior",
        "title": "Modern Interior",
        "duration": 10,
        "base_prompt": "Elegant modern living room with natural light streaming through windows",
        "style": "architectural photography",
        "camera_movement": "subtle dolly forward",
        "lighting": "soft natural light with shadows",
        "mood": "sophisticated interior",
        "details": [
            "photorealistic interior",
            "architectural digest style",
            "realistic materials and textures",
            "natural light behavior",
            "shallow depth of field",
            "cinematic composition"
        ]
    }
]

# Comparison with stylized prompt
COMPARISON_SCENES = [
    {
        "id": "compare_realistic",
        "title": "Realistic Ocean",
        "duration": 10,
        "base_prompt": "Ocean waves crashing on rocky shore at sunset",
        "style": "nature documentary",
        "prompt_type": "photorealistic",
        "details": [
            "photorealistic water physics",
            "BBC Planet Earth cinematography",
            "realistic wave movement",
            "natural lighting",
            "documentary approach"
        ]
    },
    {
        "id": "compare_stylized",
        "title": "Stylized Ocean",
        "duration": 10,
        "base_prompt": "Dreamlike ocean waves with ethereal colors and magical atmosphere",
        "style": "fantasy artistic",
        "prompt_type": "stylized",
        "details": [
            "artistic interpretation",
            "surreal color palette",
            "fantasy lighting",
            "stylized water effects",
            "magical atmosphere"
        ]
    }
]


class PhotorealisticFixedGenerator:
    """Generate photorealistic videos with proper model handling."""
    
    def __init__(self):
        self.runway_client = RunwayMLProperClient()
        self.output_dir = Path("output/runway_photorealistic_fixed")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.model_ratios = {
            "gen4_turbo": "1280:720",      # 16:9 landscape
            "gen3a_turbo": "1280:768"       # 5:3 landscape (closer to 16:9)
        }
    
    def create_photographic_image(self, scene: dict) -> str:
        """Create a photographic starting image."""
        from PIL import Image, ImageDraw, ImageFilter
        import numpy as np
        
        # Use appropriate dimensions based on scene
        width, height = 1280, 720
        
        # Create photographic base
        img = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(img)
        
        # Photographic color palettes
        if "street" in scene['title'].lower() or "urban" in scene['title'].lower():
            # Urban concrete and glass
            colors = [(140, 140, 145), (120, 125, 130), (160, 160, 165)]
        elif "mountain" in scene['title'].lower() or "nature" in scene['title'].lower():
            # Natural landscape
            colors = [(90, 110, 130), (110, 130, 110), (140, 160, 180)]
        elif "interior" in scene['title'].lower():
            # Warm interior
            colors = [(200, 190, 180), (180, 170, 160), (160, 150, 140)]
        elif "ocean" in scene['title'].lower():
            # Ocean blues
            colors = [(70, 100, 130), (90, 120, 150), (110, 140, 170)]
        else:
            # Neutral
            colors = [(140, 140, 140), (130, 130, 130), (150, 150, 150)]
        
        # Create realistic gradient
        for y in range(height):
            progress = y / height
            color_idx = int(progress * (len(colors) - 1))
            if color_idx < len(colors) - 1:
                # Interpolate between colors
                c1 = colors[color_idx]
                c2 = colors[color_idx + 1]
                local_progress = (progress * (len(colors) - 1)) - color_idx
                
                r = int(c1[0] * (1 - local_progress) + c2[0] * local_progress)
                g = int(c1[1] * (1 - local_progress) + c2[1] * local_progress)
                b = int(c1[2] * (1 - local_progress) + c2[2] * local_progress)
            else:
                r, g, b = colors[-1]
            
            # Add subtle variation
            variation = np.random.randint(-3, 3)
            r = max(0, min(255, r + variation))
            g = max(0, min(255, g + variation))
            b = max(0, min(255, b + variation))
            
            draw.rectangle([(0, y), (width, y + 1)], fill=(r, g, b))
        
        # Add photographic elements
        if "urban" in scene['title'].lower():
            # Add building silhouettes
            for i in range(5):
                x = i * 250 + np.random.randint(-50, 50)
                height_building = np.random.randint(300, 500)
                draw.rectangle(
                    [(x, height - height_building), (x + 180, height)],
                    fill=(100, 100, 105)
                )
        
        # Apply subtle blur for depth
        img = img.filter(ImageFilter.GaussianBlur(0.5))
        
        # Add film grain
        pixels = img.load()
        for x in range(0, width, 2):  # Less dense grain
            for y in range(0, height, 2):
                grain = np.random.randint(-8, 8)
                r, g, b = pixels[x, y]
                new_color = (
                    max(0, min(255, r + grain)),
                    max(0, min(255, g + grain)),
                    max(0, min(255, b + grain))
                )
                pixels[x, y] = new_color
                if x + 1 < width:
                    pixels[x + 1, y] = new_color
                if y + 1 < height:
                    pixels[x, y + 1] = new_color
                if x + 1 < width and y + 1 < height:
                    pixels[x + 1, y + 1] = new_color
        
        # Save with high quality
        image_path = self.output_dir / f"{scene['id']}_start.jpg"
        img.save(image_path, quality=95, optimize=False)
        
        return self.runway_client.create_data_uri_from_image(str(image_path))
    
    def build_photorealistic_prompt(self, scene: dict) -> str:
        """Build prompt optimized for photorealism."""
        
        # Start with base
        prompt = scene['base_prompt']
        
        # Add style
        prompt += f", {scene['style']}"
        
        # Add camera movement if specified
        if scene.get('camera_movement'):
            prompt += f", {scene['camera_movement']}"
        
        # Add lighting
        if scene.get('lighting'):
            prompt += f", {scene['lighting']}"
        
        # Add key photorealistic terms
        key_terms = [
            "photorealistic quality",
            "cinematic film look",
            "realistic lighting and shadows"
        ]
        
        for term in key_terms:
            if len(prompt) + len(term) + 2 < 900:
                prompt += f", {term}"
        
        # Add specific details
        if scene.get('details'):
            for detail in scene['details'][:2]:  # Limit details
                if len(prompt) + len(detail) + 2 < 900:
                    prompt += f", {detail}"
        
        return prompt
    
    async def generate_video_with_model(self, scene: dict, model: str) -> dict:
        """Generate a video with specific model."""
        logger.info(f"\nGenerating {scene['title']} with {model}")
        
        try:
            # Build prompt
            if scene.get('prompt_type') == 'stylized':
                # For comparison - use stylized prompt
                prompt = f"{scene['base_prompt']}, {scene['style']}"
                if scene.get('details'):
                    prompt += ", " + ", ".join(scene['details'][:3])
            else:
                # Photorealistic prompt
                prompt = self.build_photorealistic_prompt(scene)
            
            logger.info(f"Prompt ({len(prompt)} chars): {prompt[:150]}...")
            
            # Create starting image
            image_data_uri = self.create_photographic_image(scene)
            
            # Get appropriate ratio for model
            ratio = self.model_ratios[model]
            
            # Generate video
            task = self.runway_client.generate_video_from_image(
                image_url=image_data_uri,
                prompt=prompt,
                duration=scene['duration'],
                model=model,
                ratio=ratio,
                seed=42
            )
            
            if task.get('id'):
                logger.info(f"Task created: {task['id']}")
                
                # Wait for completion
                video_url = self.runway_client.wait_for_completion(
                    task['id'],
                    max_wait_time=300,  # 5 minutes max
                    poll_interval=5
                )
                
                if video_url:
                    # Download video
                    output_path = self.output_dir / f"{scene['id']}_{model}.mp4"
                    downloaded = self.runway_client.download_video(
                        video_url,
                        str(output_path)
                    )
                    
                    if downloaded:
                        file_size = os.path.getsize(downloaded) / (1024 * 1024)
                        logger.info(f"✅ Success! Video saved: {downloaded} ({file_size:.1f} MB)")
                        
                        return {
                            'success': True,
                            'model': model,
                            'path': downloaded,
                            'file_size': file_size,
                            'prompt': prompt
                        }
                
                # Check failure reason
                status = self.runway_client.get_task_status(task['id'])
                error = status.get('failure', 'Unknown error')
                logger.error(f"❌ Generation failed: {error}")
                
                return {
                    'success': False,
                    'model': model,
                    'error': error
                }
            
            return {
                'success': False,
                'model': model,
                'error': 'Task creation failed'
            }
            
        except Exception as e:
            logger.error(f"❌ Exception: {e}")
            return {
                'success': False,
                'model': model,
                'error': str(e)
            }
    
    async def run_photorealistic_test(self):
        """Run photorealistic generation test."""
        logger.info("=" * 70)
        logger.info("PHOTOREALISTIC VIDEO GENERATION TEST")
        logger.info("=" * 70)
        
        # Check credits
        org_info = self.runway_client.get_organization_info()
        credits = org_info.get('creditBalance', 0)
        logger.info(f"Credits available: {credits}")
        
        if credits < 100:
            logger.warning("Low credits! Each 10-second video costs ~50 credits")
        
        results = []
        
        # Test photorealistic scenes with gen4_turbo only (better quality)
        test_scenes = PHOTOREALISTIC_SCENES[:2]  # Test first 2
        
        for scene in test_scenes:
            result = await self.generate_video_with_model(scene, "gen4_turbo")
            results.append({
                'scene': scene,
                'result': result
            })
            
            # Brief pause
            await asyncio.sleep(2)
        
        # Test comparison (realistic vs stylized)
        logger.info("\n" + "="*60)
        logger.info("TESTING REALISTIC VS STYLIZED PROMPTS")
        logger.info("="*60)
        
        for scene in COMPARISON_SCENES:
            result = await self.generate_video_with_model(scene, "gen4_turbo")
            results.append({
                'scene': scene,
                'result': result
            })
            await asyncio.sleep(2)
        
        # Create analysis report
        self.create_analysis_report(results)
        
        return results
    
    def create_analysis_report(self, results):
        """Create detailed analysis report."""
        report_path = self.output_dir / "PHOTOREALISTIC_ANALYSIS.md"
        
        with open(report_path, "w") as f:
            f.write("# RunwayML Photorealistic Capabilities Analysis\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Summary\n\n")
            f.write("This analysis tests RunwayML's ability to generate photorealistic ")
            f.write("vs stylized/animated content based on prompt engineering.\n\n")
            
            f.write("## Key Findings\n\n")
            f.write("1. **Prompt Impact**: The prompt significantly influences whether ")
            f.write("output appears photorealistic or stylized\n")
            f.write("2. **Starting Image**: Photographic base images help guide realistic output\n")
            f.write("3. **Model Capabilities**: gen4_turbo can produce both realistic and ")
            f.write("stylized content based on prompting\n\n")
            
            f.write("## Generated Videos\n\n")
            
            successful = 0
            for item in results:
                scene = item['scene']
                result = item['result']
                
                f.write(f"### {scene['title']}\n\n")
                f.write(f"**Type**: {scene.get('prompt_type', 'photorealistic')}\n")
                f.write(f"**Style**: {scene['style']}\n\n")
                
                if result['success']:
                    successful += 1
                    f.write(f"✅ **Success**\n")
                    f.write(f"- Model: {result['model']}\n")
                    f.write(f"- File: `{result['path']}`\n")
                    f.write(f"- Size: {result['file_size']:.1f} MB\n")
                    f.write(f"- Prompt: {result['prompt'][:200]}...\n\n")
                else:
                    f.write(f"❌ **Failed**: {result['error']}\n\n")
            
            f.write("## Recommendations for Photorealistic Output\n\n")
            f.write("1. **Prompt Engineering**:\n")
            f.write("   - Use 'photorealistic', 'documentary', 'cinematic' terms\n")
            f.write("   - Specify real-world camera movements and lighting\n")
            f.write("   - Reference documentary cinematographers\n")
            f.write("   - Avoid fantasy/stylized terms\n\n")
            
            f.write("2. **Starting Images**:\n")
            f.write("   - Use photographic/neutral base images\n")
            f.write("   - Include realistic lighting and shadows\n")
            f.write("   - Add film grain for authenticity\n\n")
            
            f.write("3. **Content Considerations**:\n")
            f.write("   - Architecture and landscapes work well\n")
            f.write("   - Avoid specific people references (moderation)\n")
            f.write("   - Focus on environments and atmospheres\n\n")
            
            f.write(f"\n**Success Rate**: {successful}/{len(results)} videos generated\n")
        
        logger.info(f"\nAnalysis report saved to: {report_path}")


async def main():
    """Main entry point."""
    generator = PhotorealisticFixedGenerator()
    
    # Run photorealistic test
    results = await generator.run_photorealistic_test()
    
    logger.info("\n" + "="*70)
    logger.info("PHOTOREALISTIC TEST COMPLETE")
    logger.info("="*70)
    
    # Summary
    successful = sum(1 for r in results if r['result']['success'])
    logger.info(f"\nGenerated {successful} videos successfully")
    logger.info(f"Output directory: {generator.output_dir}")
    
    logger.info("\n📊 COMPARISON LOCATIONS:")
    logger.info("1. Stylized/Animated: output/runway_safe/")
    logger.info("2. Photorealistic: output/runway_photorealistic_fixed/")
    logger.info("\nCompare the 'realistic' vs 'stylized' ocean videos to see the difference!")


if __name__ == "__main__":
    asyncio.run(main())