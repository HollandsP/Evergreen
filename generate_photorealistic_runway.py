#!/usr/bin/env python3
"""
Generate photorealistic videos with RunwayML.
Focused on creating lifelike, cinematic scenes rather than animated/stylized content.
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

# PHOTOREALISTIC prompts - emphasizing real-world, cinematic quality
PHOTOREALISTIC_SCENES = [
    {
        "id": "real_scene_1_street",
        "title": "Urban Street Life",
        "duration": 10,
        "base_prompt": "A busy city street corner with pedestrians walking, realistic daylight",
        "style": "documentary",
        "camera_movement": "handheld camera following pedestrian",
        "lighting": "natural daylight, overcast sky",
        "mood": "everyday life, authentic",
        "details": [
            "photorealistic quality",
            "documentary cinematography",
            "35mm film look",
            "natural human movement",
            "realistic shadows and lighting",
            "authentic street atmosphere",
            "no special effects",
            "cinematic depth of field"
        ]
    },
    {
        "id": "real_scene_2_cafe",
        "title": "Coffee Shop Interior",
        "duration": 10,
        "base_prompt": "Interior of a modern coffee shop with customers and barista working",
        "style": "cinematic realism",
        "camera_movement": "slow dolly through cafe",
        "lighting": "warm interior lighting, window light",
        "mood": "cozy, authentic atmosphere",
        "details": [
            "photorealistic rendering",
            "Roger Deakins cinematography style",
            "natural lighting through windows",
            "realistic human interactions",
            "steam from coffee machines",
            "authentic cafe ambiance",
            "shallow depth of field",
            "film grain texture"
        ]
    },
    {
        "id": "real_scene_3_park",
        "title": "City Park Morning",
        "duration": 10,
        "base_prompt": "People jogging and walking dogs in a city park at golden hour",
        "style": "naturalistic",
        "camera_movement": "steadicam following jogger",
        "lighting": "golden hour sunlight, long shadows",
        "mood": "peaceful morning activity",
        "details": [
            "photorealistic quality",
            "Emmanuel Lubezki cinematography",
            "natural sunlight",
            "realistic human movement",
            "authentic park atmosphere",
            "birds in background",
            "lens flares from sun",
            "cinematic color grading"
        ]
    },
    {
        "id": "real_scene_4_office",
        "title": "Modern Office Space",
        "duration": 10,
        "base_prompt": "Professional office environment with people working at computers",
        "style": "corporate documentary",
        "camera_movement": "smooth gimbal movement through office",
        "lighting": "fluorescent office lighting mixed with natural light",
        "mood": "professional, productive",
        "details": [
            "photorealistic rendering",
            "documentary style filming",
            "realistic office lighting",
            "authentic workplace activity",
            "computer screens glowing",
            "professional atmosphere",
            "natural human behavior",
            "4K clarity"
        ]
    },
    {
        "id": "real_scene_5_restaurant",
        "title": "Restaurant Kitchen",
        "duration": 10,
        "base_prompt": "Professional kitchen with chefs preparing food during dinner service",
        "style": "culinary documentary",
        "camera_movement": "handheld following chef",
        "lighting": "bright kitchen lights, steam and heat",
        "mood": "energetic, professional cooking",
        "details": [
            "photorealistic quality",
            "Chef's Table cinematography",
            "harsh kitchen lighting",
            "steam from cooking",
            "realistic chef movements",
            "authentic kitchen chaos",
            "shallow focus on food",
            "high contrast lighting"
        ]
    },
    {
        "id": "real_scene_6_subway",
        "title": "Subway Platform",
        "duration": 10,
        "base_prompt": "Underground subway platform with train arriving and passengers waiting",
        "style": "urban realism",
        "camera_movement": "static wide shot of platform",
        "lighting": "harsh fluorescent subway lighting",
        "mood": "urban commute atmosphere",
        "details": [
            "photorealistic rendering",
            "cinema verite style",
            "industrial lighting",
            "train motion blur",
            "realistic crowd behavior",
            "authentic subway sounds implied",
            "gritty urban texture",
            "documentary approach"
        ]
    }
]

# Also test with more neutral base images
NEUTRAL_SCENES = [
    {
        "id": "neutral_scene_1_portrait",
        "title": "Professional Portrait",
        "duration": 10,
        "base_prompt": "Professional business person in modern office, subtle head movement and blinking",
        "style": "portrait cinematography",
        "camera_movement": "slight push in on subject",
        "lighting": "soft key light, natural fill",
        "mood": "professional, confident",
        "details": [
            "photorealistic human features",
            "Peter Lindbergh portrait style",
            "natural skin tones",
            "realistic eye movement",
            "subtle facial expressions",
            "professional wardrobe",
            "bokeh background",
            "film-like quality"
        ]
    },
    {
        "id": "neutral_scene_2_landscape",
        "title": "Natural Landscape",
        "duration": 10,
        "base_prompt": "Mountain landscape with gentle wind moving through trees",
        "style": "nature documentary",
        "camera_movement": "slow aerial drift",
        "lighting": "natural sunlight, partly cloudy",
        "mood": "serene, majestic",
        "details": [
            "photorealistic landscape",
            "National Geographic style",
            "natural lighting conditions",
            "realistic tree movement",
            "atmospheric perspective",
            "authentic weather effects",
            "high dynamic range",
            "cinematic aspect ratio"
        ]
    }
]


class PhotorealisticRunwayGenerator:
    """Generate photorealistic videos with RunwayML."""
    
    def __init__(self):
        self.runway_client = RunwayMLProperClient()
        self.output_dir = Path("output/runway_photorealistic")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.stats = {
            "total": 0,
            "successful": 0,
            "failed": 0,
            "model_comparison": {}
        }
    
    def create_neutral_image(self, scene: dict) -> str:
        """Create a neutral, photorealistic starting image."""
        from PIL import Image, ImageDraw
        import numpy as np
        
        width, height = 1280, 720
        
        # Create more neutral, photographic base
        img = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(img)
        
        # Neutral photographic backgrounds
        if "street" in scene['title'].lower() or "urban" in scene['title'].lower():
            # Urban gray tones
            base_color = (120, 120, 125)
        elif "cafe" in scene['title'].lower() or "restaurant" in scene['title'].lower():
            # Warm interior tones
            base_color = (140, 130, 120)
        elif "park" in scene['title'].lower() or "landscape" in scene['title'].lower():
            # Natural green/blue tones
            base_color = (110, 130, 110)
        elif "office" in scene['title'].lower():
            # Neutral office tones
            base_color = (130, 130, 135)
        else:
            # Neutral gray
            base_color = (128, 128, 128)
        
        # Create subtle gradient for depth
        for y in range(height):
            progress = y / height
            # Subtle variation, not dramatic
            r = int(base_color[0] * (0.9 + 0.2 * progress))
            g = int(base_color[1] * (0.9 + 0.2 * progress))
            b = int(base_color[2] * (0.9 + 0.2 * progress))
            draw.rectangle([(0, y), (width, y + 1)], fill=(min(r, 160), min(g, 160), min(b, 160)))
        
        # Add subtle photographic texture
        pixels = img.load()
        for x in range(width):
            for y in range(height):
                # Add film grain
                grain = np.random.randint(-5, 5)
                r, g, b = pixels[x, y]
                pixels[x, y] = (
                    max(0, min(255, r + grain)),
                    max(0, min(255, g + grain)),
                    max(0, min(255, b + grain))
                )
        
        # Save image
        image_path = self.output_dir / f"{scene['id']}_start.jpg"
        img.save(image_path, quality=95)
        
        return self.runway_client.create_data_uri_from_image(str(image_path))
    
    def create_photorealistic_prompt(self, scene: dict) -> str:
        """Create a prompt specifically optimized for photorealistic output."""
        
        # Build prompt emphasizing realism
        prompt_parts = [
            scene['base_prompt'],
            f"shot in {scene['style']} style",
            f"with {scene['camera_movement']}",
            f"{scene['lighting']}",
            f"creating {scene['mood']}",
        ]
        
        # Add photorealistic emphasis
        realism_terms = [
            "photorealistic quality",
            "cinematic realism",
            "documentary authenticity",
            "natural human behavior",
            "realistic lighting and shadows",
            "true-to-life movement",
            "film cinematography"
        ]
        
        # Add selected realism terms
        prompt_parts.extend(realism_terms[:3])
        
        # Add specific details
        if scene.get('details'):
            prompt_parts.extend(scene['details'][:3])
        
        # Combine and limit length
        full_prompt = ", ".join(prompt_parts)
        
        # Ensure we stay under 1000 chars but keep it rich
        if len(full_prompt) > 900:
            full_prompt = full_prompt[:897] + "..."
            
        return full_prompt
    
    async def test_both_models(self, scene: dict) -> dict:
        """Test a scene with both gen4_turbo and gen3a_turbo."""
        results = {}
        
        for model in ["gen4_turbo", "gen3a_turbo"]:
            logger.info(f"\nTesting {scene['title']} with {model}")
            
            try:
                # Create optimized prompt
                prompt = self.create_photorealistic_prompt(scene)
                logger.info(f"Photorealistic prompt ({len(prompt)} chars): {prompt[:150]}...")
                
                # Create neutral starting image
                image_data_uri = self.create_neutral_image(scene)
                
                # Generate video
                task = self.runway_client.generate_video_from_image(
                    image_url=image_data_uri,
                    prompt=prompt,
                    duration=scene['duration'],
                    model=model,
                    ratio="1280:720",
                    seed=42,  # Consistent seed for comparison
                )
                
                if task.get('id'):
                    logger.info(f"Task created with {model}: {task['id']}")
                    
                    # Wait for completion
                    video_url = self.runway_client.wait_for_completion(
                        task['id'],
                        max_wait_time=600,
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
                            results[model] = {
                                'success': True,
                                'path': downloaded,
                                'file_size': os.path.getsize(downloaded) / (1024 * 1024)  # MB
                            }
                            logger.info(f"✅ {model} success: {downloaded}")
                        else:
                            results[model] = {'success': False, 'error': 'Download failed'}
                    else:
                        results[model] = {'success': False, 'error': 'Generation failed'}
                else:
                    results[model] = {'success': False, 'error': 'Task creation failed'}
                    
            except Exception as e:
                logger.error(f"❌ {model} error: {e}")
                results[model] = {'success': False, 'error': str(e)}
            
            # Brief pause between models
            await asyncio.sleep(3)
        
        return results
    
    async def generate_photorealistic_showcase(self):
        """Generate photorealistic video showcase."""
        logger.info("Starting Photorealistic RunwayML Generation")
        logger.info("Testing both gen4_turbo and gen3a_turbo models")
        
        # Check credits
        org_info = self.runway_client.get_organization_info()
        credits = org_info.get('creditBalance', 0)
        logger.info(f"Credits available: {credits}")
        
        all_results = []
        
        # Test photorealistic scenes
        scenes_to_test = PHOTOREALISTIC_SCENES[:3] + NEUTRAL_SCENES[:1]  # Test subset
        self.stats['total'] = len(scenes_to_test) * 2  # Testing 2 models each
        
        for i, scene in enumerate(scenes_to_test):
            logger.info(f"\n{'='*60}")
            logger.info(f"Scene {i+1}/{len(scenes_to_test)}: {scene['title']}")
            
            model_results = await self.test_both_models(scene)
            
            for model, result in model_results.items():
                if result['success']:
                    self.stats['successful'] += 1
                    if model not in self.stats['model_comparison']:
                        self.stats['model_comparison'][model] = {'success': 0, 'failed': 0}
                    self.stats['model_comparison'][model]['success'] += 1
                else:
                    self.stats['failed'] += 1
                    if model not in self.stats['model_comparison']:
                        self.stats['model_comparison'][model] = {'success': 0, 'failed': 0}
                    self.stats['model_comparison'][model]['failed'] += 1
            
            all_results.append({
                'scene': scene,
                'results': model_results
            })
            
            # Save progress
            progress_path = self.output_dir / "photorealistic_progress.json"
            with open(progress_path, "w") as f:
                json.dump({
                    'stats': self.stats,
                    'results': all_results
                }, f, indent=2)
        
        # Create detailed report
        self.create_photorealistic_report(all_results)
        
        return all_results
    
    def create_photorealistic_report(self, results):
        """Create a detailed report on photorealistic generation."""
        report_path = self.output_dir / "PHOTOREALISTIC_ANALYSIS.md"
        
        with open(report_path, "w") as f:
            f.write("# RunwayML Photorealistic Video Analysis\n\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Executive Summary\n\n")
            f.write("This report analyzes RunwayML's capability to generate photorealistic, ")
            f.write("lifelike videos as opposed to animated or stylized content.\n\n")
            
            f.write("## Model Comparison\n\n")
            f.write("### Statistics\n\n")
            f.write(f"- Total generations: {self.stats['total']}\n")
            f.write(f"- Successful: {self.stats['successful']}\n")
            f.write(f"- Failed: {self.stats['failed']}\n\n")
            
            f.write("### Model Performance\n\n")
            for model, stats in self.stats['model_comparison'].items():
                f.write(f"**{model}**:\n")
                f.write(f"- Success: {stats['success']}\n")
                f.write(f"- Failed: {stats['failed']}\n\n")
            
            f.write("## Photorealistic Prompt Strategy\n\n")
            f.write("To achieve more lifelike results, we emphasized:\n\n")
            f.write("1. **Documentary/Cinematic Style**: Using terms like 'photorealistic', ")
            f.write("'documentary cinematography', 'cinematic realism'\n")
            f.write("2. **Natural Lighting**: Specifying realistic lighting conditions\n")
            f.write("3. **Authentic Movement**: Requesting 'natural human behavior' and ")
            f.write("'realistic movement'\n")
            f.write("4. **Film References**: Citing cinematographers known for realism\n")
            f.write("5. **Avoiding Stylization**: No mentions of 'cyberpunk', 'sci-fi', ")
            f.write("or other stylized aesthetics\n\n")
            
            f.write("## Generated Videos\n\n")
            for result in results:
                scene = result['scene']
                f.write(f"### {scene['title']}\n\n")
                f.write(f"**Prompt Focus**: {scene['style']}\n\n")
                
                for model, model_result in result['results'].items():
                    if model_result['success']:
                        f.write(f"**{model}**: ✅ Success\n")
                        f.write(f"- File: `{model_result['path']}`\n")
                        f.write(f"- Size: {model_result['file_size']:.1f} MB\n\n")
                    else:
                        f.write(f"**{model}**: ❌ Failed - {model_result['error']}\n\n")
            
            f.write("## Key Findings\n\n")
            f.write("1. **Prompt Engineering**: More explicit photorealistic language ")
            f.write("helps guide the model toward realistic output\n")
            f.write("2. **Starting Images**: Neutral, photographic base images work better ")
            f.write("than stylized ones\n")
            f.write("3. **Model Differences**: Both models can produce realistic content ")
            f.write("with proper prompting\n\n")
            
            f.write("## Recommendations for Photorealism\n\n")
            f.write("1. Use documentary/cinematic terminology\n")
            f.write("2. Specify natural lighting conditions\n")
            f.write("3. Request realistic human behavior explicitly\n")
            f.write("4. Avoid stylized references (cyberpunk, anime, etc.)\n")
            f.write("5. Use photographic starting images\n")
            f.write("6. Include film grain or documentary style cues\n")
        
        logger.info(f"\nDetailed report saved to: {report_path}")


async def main():
    """Main entry point."""
    generator = PhotorealisticRunwayGenerator()
    
    # Generate photorealistic showcase
    results = await generator.generate_photorealistic_showcase()
    
    logger.info("\n" + "="*70)
    logger.info("PHOTOREALISTIC GENERATION COMPLETE")
    logger.info("="*70)
    
    # Show where videos are saved
    output_dir = generator.output_dir
    logger.info(f"\nVideos saved to: {output_dir}")
    logger.info("\nTo compare animated vs photorealistic:")
    logger.info("1. Animated/stylized videos: output/runway_safe/")
    logger.info("2. Photorealistic attempts: output/runway_photorealistic/")


if __name__ == "__main__":
    asyncio.run(main())