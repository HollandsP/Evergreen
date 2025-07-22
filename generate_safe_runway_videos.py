#!/usr/bin/env python3
"""
Generate videos with RunwayML using moderation-safe prompts.
Avoids terms that might trigger content moderation.
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

# SAFE prompts that avoid moderation triggers
# Avoiding: violence, weapons, death, bodies, fighting, etc.
SAFE_SCENES = [
    {
        "id": "scene_1_cityscape",
        "title": "Futuristic City at Night",
        "duration": 10,
        "base_prompt": "Aerial view of futuristic cityscape at night with glowing neon lights and flying vehicles",
        "style": "cyberpunk",
        "camera_movement": "smooth drone flight between skyscrapers",
        "lighting": "neon blue and purple city lights with volumetric fog",
        "mood": "mysterious and beautiful",
        "details": [
            "Blade Runner 2049 aesthetic",
            "holographic advertisements",
            "rain reflections on streets",
            "4K ultra detailed",
            "cinematic composition",
            "flying cars with light trails"
        ]
    },
    {
        "id": "scene_2_technology",
        "title": "Advanced Technology Lab",
        "duration": 10,
        "base_prompt": "High-tech laboratory with holographic displays showing data visualizations and AI interfaces",
        "style": "sci-fi",
        "camera_movement": "slow tracking shot through lab",
        "lighting": "cool blue LED lighting with hologram glow",
        "mood": "innovative and futuristic",
        "details": [
            "Ex Machina visual style",
            "transparent screens",
            "floating holograms",
            "clean minimalist design",
            "particle effects",
            "depth of field"
        ]
    },
    {
        "id": "scene_3_nature",
        "title": "Mystical Forest Dawn",
        "duration": 10,
        "base_prompt": "Ancient forest at dawn with sunlight streaming through misty trees",
        "style": "cinematic",
        "camera_movement": "crane shot rising through forest canopy",
        "lighting": "golden hour sunlight with atmospheric haze",
        "mood": "peaceful and magical",
        "details": [
            "Terrence Malick cinematography",
            "volumetric light rays",
            "morning mist",
            "lens flares",
            "wildlife in distance",
            "8K nature documentary quality"
        ]
    },
    {
        "id": "scene_4_abstract",
        "title": "Digital Dreams",
        "duration": 10,
        "base_prompt": "Abstract visualization of flowing data streams and geometric patterns in cyberspace",
        "style": "artistic",
        "camera_movement": "fluid movement through 3D digital space",
        "lighting": "luminescent colors and glowing particles",
        "mood": "mesmerizing and transcendent",
        "details": [
            "Tron Legacy aesthetic",
            "fractal patterns",
            "neon grid lines",
            "particle systems",
            "color gradients",
            "motion graphics style"
        ]
    },
    {
        "id": "scene_5_architecture",
        "title": "Modern Architecture Marvel",
        "duration": 10,
        "base_prompt": "Contemporary glass skyscraper with innovative architecture reflecting sunset sky",
        "style": "architectural",
        "camera_movement": "vertical crane shot along building facade",
        "lighting": "golden hour reflection on glass surfaces",
        "mood": "impressive and sophisticated",
        "details": [
            "architectural photography style",
            "geometric patterns",
            "glass reflections",
            "urban landscape",
            "dramatic shadows",
            "4K clarity"
        ]
    },
    {
        "id": "scene_6_underwater",
        "title": "Deep Ocean Discovery",
        "duration": 10,
        "base_prompt": "Underwater scene with bioluminescent creatures and coral reef ecosystem",
        "style": "documentary",
        "camera_movement": "smooth underwater glide through reef",
        "lighting": "underwater caustics with bioluminescent glow",
        "mood": "mysterious and beautiful",
        "details": [
            "BBC Blue Planet style",
            "schools of fish",
            "light rays through water",
            "coral formations",
            "marine life diversity",
            "submarine documentary quality"
        ]
    }
]


class SafeRunwayGenerator:
    """Generate safe videos with RunwayML."""
    
    def __init__(self):
        self.runway_client = RunwayMLProperClient()
        self.output_dir = Path("output/runway_safe")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.stats = {
            "total": len(SAFE_SCENES),
            "successful": 0,
            "failed": 0,
            "moderated": 0
        }
    
    def create_safe_image(self, scene: dict) -> str:
        """Create a safe starting image."""
        from PIL import Image, ImageDraw
        import numpy as np
        
        width, height = 1280, 720
        
        # Use pleasant, non-threatening colors
        color_schemes = {
            "futuristic": (20, 30, 60),
            "technology": (10, 40, 50),
            "nature": (30, 50, 30),
            "abstract": (40, 20, 60),
            "architectural": (50, 50, 60),
            "underwater": (10, 30, 50)
        }
        
        # Get base color from scene type
        base_color = (30, 30, 40)  # default
        for key, color in color_schemes.items():
            if key in scene['title'].lower():
                base_color = color
                break
        
        # Create gradient background
        img = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(img)
        
        for y in range(height):
            progress = y / height
            r = int(base_color[0] * (1 - progress) + base_color[0] * 2 * progress)
            g = int(base_color[1] * (1 - progress) + base_color[1] * 2 * progress)
            b = int(base_color[2] * (1 - progress) + base_color[2] * 2 * progress)
            draw.rectangle([(0, y), (width, y + 1)], fill=(min(r, 100), min(g, 100), min(b, 100)))
        
        # Add some safe visual elements
        if "city" in scene['title'].lower():
            # Add city lights
            for _ in range(200):
                x = np.random.randint(0, width)
                y = np.random.randint(height // 2, height)
                size = np.random.randint(2, 5)
                brightness = np.random.randint(100, 200)
                color = (brightness, brightness - 20, brightness - 40)
                draw.ellipse([(x, y), (x + size, y + size)], fill=color)
        
        elif "forest" in scene['title'].lower():
            # Add tree silhouettes
            for i in range(20):
                x = i * (width // 20)
                tree_height = np.random.randint(200, 400)
                draw.polygon([
                    (x - 20, height),
                    (x, height - tree_height),
                    (x + 20, height)
                ], fill=(20, 40, 20))
        
        # Save image
        image_path = self.output_dir / f"{scene['id']}_start.jpg"
        img.save(image_path, quality=95)
        
        return self.runway_client.create_data_uri_from_image(str(image_path))
    
    async def generate_safe_video(self, scene: dict) -> dict:
        """Generate a single safe video."""
        logger.info(f"\nGenerating: {scene['title']}")
        
        start_time = datetime.now()
        
        try:
            # Create safe prompt
            prompt = self.runway_client.generate_cinematic_prompt(
                base_description=scene['base_prompt'],
                style=scene['style'],
                camera_movement=scene.get('camera_movement'),
                lighting=scene.get('lighting'),
                mood=scene.get('mood'),
                details=scene.get('details', [])
            )
            
            logger.info(f"Safe prompt ({len(prompt)} chars): {prompt[:150]}...")
            
            # Create starting image
            image_data_uri = self.create_safe_image(scene)
            
            # Generate video with less strict moderation
            task = self.runway_client.generate_video_from_image(
                image_url=image_data_uri,
                prompt=prompt,
                duration=scene['duration'],
                model="gen4_turbo",
                ratio="1280:720",
                seed=42,
                content_moderation={
                    "publicFigureThreshold": "low"  # Less strict
                }
            )
            
            if task.get('id'):
                logger.info(f"Task created: {task['id']}")
                
                # Wait for completion
                video_url = self.runway_client.wait_for_completion(
                    task['id'],
                    max_wait_time=600,
                    poll_interval=5
                )
                
                if video_url:
                    # Download video
                    output_path = self.output_dir / f"{scene['id']}.mp4"
                    downloaded = self.runway_client.download_video(
                        video_url,
                        str(output_path)
                    )
                    
                    if downloaded:
                        generation_time = (datetime.now() - start_time).total_seconds()
                        self.stats['successful'] += 1
                        
                        logger.info(f"✅ Success! Video saved to: {downloaded}")
                        logger.info(f"Generation time: {generation_time:.1f} seconds")
                        
                        return {
                            'success': True,
                            'scene_id': scene['id'],
                            'title': scene['title'],
                            'video_path': downloaded,
                            'generation_time': generation_time
                        }
                else:
                    # Check if it was moderated
                    status = self.runway_client.get_task_status(task['id'])
                    if status.get('failureCode', '').startswith('SAFETY'):
                        self.stats['moderated'] += 1
                        logger.warning(f"⚠️ Content moderated: {status.get('failure', '')}")
                    else:
                        self.stats['failed'] += 1
                        logger.error(f"❌ Generation failed: {status.get('failure', 'Unknown')}")
            
            return {
                'success': False,
                'scene_id': scene['id'],
                'title': scene['title'],
                'error': 'Generation failed'
            }
            
        except Exception as e:
            self.stats['failed'] += 1
            logger.error(f"❌ Exception: {e}")
            
            return {
                'success': False,
                'scene_id': scene['id'],
                'title': scene['title'],
                'error': str(e)
            }
    
    async def generate_all_safe_videos(self):
        """Generate all safe videos."""
        logger.info("Starting Safe RunwayML Video Generation")
        logger.info(f"Total scenes: {len(SAFE_SCENES)}")
        
        # Check credits
        org_info = self.runway_client.get_organization_info()
        credits = org_info.get('creditBalance', 0)
        logger.info(f"Credits available: {credits}")
        
        results = []
        
        for i, scene in enumerate(SAFE_SCENES):
            logger.info(f"\n{'='*60}")
            logger.info(f"Scene {i+1}/{len(SAFE_SCENES)}")
            
            result = await self.generate_safe_video(scene)
            results.append(result)
            
            # Save progress
            with open(self.output_dir / "generation_log.json", "w") as f:
                json.dump({
                    'stats': self.stats,
                    'results': results
                }, f, indent=2)
            
            # Brief pause
            if i < len(SAFE_SCENES) - 1:
                await asyncio.sleep(3)
        
        # Summary
        logger.info(f"\n{'='*70}")
        logger.info("SAFE VIDEO GENERATION COMPLETE")
        logger.info(f"{'='*70}")
        logger.info(f"Total: {self.stats['total']}")
        logger.info(f"Successful: {self.stats['successful']}")
        logger.info(f"Failed: {self.stats['failed']}")
        logger.info(f"Moderated: {self.stats['moderated']}")
        
        # Create summary
        summary_path = self.output_dir / "SAFE_GENERATION_SUMMARY.md"
        with open(summary_path, "w") as f:
            f.write("# Safe RunwayML Video Generation Results\n\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("## Statistics\n\n")
            f.write(f"- Total Scenes: {self.stats['total']}\n")
            f.write(f"- Successful: {self.stats['successful']}\n")
            f.write(f"- Failed: {self.stats['failed']}\n")
            f.write(f"- Moderated: {self.stats['moderated']}\n\n")
            f.write("## Videos\n\n")
            
            for result in results:
                if result['success']:
                    f.write(f"### ✅ {result['title']}\n")
                    f.write(f"- File: `{result['video_path']}`\n")
                    f.write(f"- Time: {result['generation_time']:.1f}s\n\n")
                else:
                    f.write(f"### ❌ {result['title']}\n")
                    f.write(f"- Error: {result['error']}\n\n")
        
        logger.info(f"\nSummary saved to: {summary_path}")
        
        return results


async def main():
    """Main entry point."""
    generator = SafeRunwayGenerator()
    
    # Generate safe videos
    results = await generator.generate_all_safe_videos()
    
    # Show successful videos
    successful = [r for r in results if r['success']]
    if successful:
        logger.info(f"\n✅ Successfully generated {len(successful)} videos:")
        for r in successful:
            logger.info(f"  - {r['title']}: {r['video_path']}")


if __name__ == "__main__":
    asyncio.run(main())