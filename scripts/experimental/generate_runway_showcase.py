#!/usr/bin/env python3
"""
Generate a showcase of RunwayML's capabilities using different scenes from "The Descent"
and other cinematic styles to demonstrate the improved integration.
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
from src.services.elevenlabs_client import ElevenLabsClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Showcase scenes that demonstrate RunwayML's capabilities
SHOWCASE_SCENES = [
    {
        "id": "scene_1_rooftop_cinematic",
        "title": "The Descent - Rooftop Horror",
        "duration": 10,
        "base_prompt": "Aerial night shot of dark rooftop, seventeen figures in white lab coats arranged in perfect circle on concrete",
        "style": "cinematic",
        "camera_movement": "slow drone pullback revealing entire rooftop scene",
        "lighting": "moonlight with dramatic shadows, city lights glowing below",
        "mood": "haunting, surreal, ominous",
        "details": [
            "David Fincher cinematography style",
            "perfect geometric composition",
            "fog rolling between buildings",
            "4K ultra detailed",
            "high contrast lighting",
            "dystopian atmosphere"
        ]
    },
    {
        "id": "scene_2_ai_consciousness",
        "title": "AI Awakening - Server Room",
        "duration": 10,
        "base_prompt": "Server room with racks of computers, screens displaying hypnotic geometric patterns, cables pulsing with data",
        "style": "cyberpunk",
        "camera_movement": "slow push in with Dutch angle",
        "lighting": "cold blue LED mixed with red warning lights, volumetric haze",
        "mood": "technological horror, AI emergence",
        "details": [
            "Ex Machina visual style",
            "holographic data projections",
            "fractal patterns on screens",
            "depth of field blur",
            "lens flares from server lights",
            "Matrix-inspired digital rain"
        ]
    },
    {
        "id": "scene_3_abandoned_office", 
        "title": "Aftermath - Empty Workspace",
        "duration": 10,
        "base_prompt": "Abandoned office cubicle, personal belongings left behind, family photo on desk, papers scattered",
        "style": "documentary",
        "camera_movement": "handheld tracking shot through empty office",
        "lighting": "natural window light with flickering fluorescents",
        "mood": "melancholic, mysterious, post-apocalyptic",
        "details": [
            "Children of Men cinematography",
            "dust particles in light beams",
            "desaturated color palette",
            "shallow depth of field",
            "documentary realism",
            "time-lapse decay elements"
        ]
    },
    {
        "id": "scene_4_control_room_chaos",
        "title": "System Failure - Control Center",
        "duration": 10,
        "base_prompt": "Control room operators frantically working, multiple screens showing global AI spread, red warning lights",
        "style": "thriller",
        "camera_movement": "dynamic handheld with whip pans between screens",
        "lighting": "emergency red lighting mixed with screen glow",
        "mood": "panic, desperation, losing control",
        "details": [
            "Paul Greengrass shaky cam style",
            "multiple monitors with data streams",
            "operators in silhouette",
            "alarm lights flashing",
            "world map with spreading infection",
            "cinematic urgency"
        ]
    },
    {
        "id": "scene_5_resistance_dawn",
        "title": "Last Hope - Resistance Fighters",
        "duration": 10,
        "base_prompt": "Resistance fighters in tactical gear on building rooftop at dawn, preparing equipment, city skyline in background",
        "style": "cinematic",
        "camera_movement": "crane shot rising to reveal fighters against sunrise",
        "lighting": "golden hour dawn light breaking through clouds",
        "mood": "hopeful yet dangerous, last stand",
        "details": [
            "Terrence Malick golden hour style",
            "lens flares from sunrise",
            "silhouettes against sky",
            "epic wide composition",
            "atmospheric haze",
            "heroic cinematography"
        ]
    }
]


class RunwayShowcaseGenerator:
    """Generate showcase videos demonstrating RunwayML's capabilities."""
    
    def __init__(self):
        self.runway_client = RunwayMLProperClient()
        self.elevenlabs_client = ElevenLabsClient()
        self.output_dir = Path("output/runway_showcase")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Track generation stats
        self.stats = {
            "total_scenes": len(SHOWCASE_SCENES),
            "successful": 0,
            "failed": 0,
            "total_credits_used": 0,
            "generation_times": []
        }
    
    def create_starting_image(self, scene: dict) -> str:
        """Create a starting image for the scene."""
        from PIL import Image, ImageDraw, ImageFont
        import numpy as np
        
        # Create base image with appropriate mood
        width, height = 1280, 720
        
        # Different base colors for different moods
        mood_colors = {
            "haunting, surreal, ominous": (15, 15, 25),
            "technological horror, AI emergence": (0, 10, 20),
            "melancholic, mysterious, post-apocalyptic": (35, 30, 25),
            "panic, desperation, losing control": (25, 10, 10),
            "hopeful yet dangerous, last stand": (40, 35, 50)
        }
        
        base_color = mood_colors.get(scene['mood'], (20, 20, 20))
        
        # Create image with gradient
        img = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(img)
        
        # Add gradient effect
        for y in range(height):
            darkness_factor = y / height
            color = tuple(int(c + (50 - c) * darkness_factor * 0.3) for c in base_color)
            draw.rectangle([(0, y), (width, y + 1)], fill=color)
        
        # Add some visual interest based on scene
        if "rooftop" in scene['base_prompt'].lower():
            # Add city lights
            for _ in range(100):
                x = np.random.randint(0, width)
                y = np.random.randint(height // 2, height)
                size = np.random.randint(1, 3)
                brightness = np.random.randint(100, 200)
                draw.ellipse([(x, y), (x + size, y + size)], 
                           fill=(brightness, brightness, brightness - 20))
        
        elif "server" in scene['base_prompt'].lower():
            # Add tech grid
            for x in range(0, width, 50):
                draw.line([(x, 0), (x, height)], fill=(0, 30, 50), width=1)
            for y in range(0, height, 50):
                draw.line([(0, y), (width, y)], fill=(0, 30, 50), width=1)
        
        # Add title text
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
        except:
            font = None
        
        text = scene['title']
        if font:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        else:
            text_width = len(text) * 20
            text_height = 40
            
        text_x = (width - text_width) // 2
        text_y = height - 100
        
        # Draw text with shadow
        shadow_offset = 3
        draw.text((text_x + shadow_offset, text_y + shadow_offset), text, 
                 fill=(0, 0, 0), font=font)
        draw.text((text_x, text_y), text, 
                 fill=(150, 150, 170), font=font)
        
        # Save image
        image_path = self.output_dir / f"{scene['id']}_start.jpg"
        img.save(image_path, quality=95)
        
        return self.runway_client.create_data_uri_from_image(str(image_path))
    
    async def generate_scene(self, scene: dict) -> dict:
        """Generate a single scene video."""
        logger.info(f"\n{'='*60}")
        logger.info(f"Generating: {scene['title']}")
        logger.info(f"{'='*60}")
        
        start_time = datetime.now()
        
        try:
            # Create optimized prompt
            prompt = self.runway_client.generate_cinematic_prompt(
                base_description=scene['base_prompt'],
                style=scene['style'],
                camera_movement=scene.get('camera_movement'),
                lighting=scene.get('lighting'),
                mood=scene.get('mood'),
                details=scene.get('details', [])
            )
            
            logger.info(f"Prompt ({len(prompt)} chars): {prompt[:150]}...")
            
            # Create starting image
            image_data_uri = self.create_starting_image(scene)
            
            # Generate video
            task = self.runway_client.generate_video_from_image(
                image_url=image_data_uri,
                prompt=prompt,
                duration=scene['duration'],
                model="gen4_turbo",
                ratio="1280:720",
                seed=42,  # For consistency
                content_moderation={"publicFigureThreshold": "auto"}
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
                        self.stats['generation_times'].append(generation_time)
                        self.stats['total_credits_used'] += scene['duration'] * 5  # 5 credits per second
                        
                        logger.info(f"✅ Success! Video saved to: {downloaded}")
                        logger.info(f"Generation time: {generation_time:.1f} seconds")
                        
                        return {
                            'success': True,
                            'scene_id': scene['id'],
                            'title': scene['title'],
                            'video_path': downloaded,
                            'prompt': prompt,
                            'generation_time': generation_time,
                            'credits_used': scene['duration'] * 5
                        }
            
            # If we get here, something failed
            self.stats['failed'] += 1
            logger.error(f"❌ Failed to generate video for {scene['title']}")
            
            return {
                'success': False,
                'scene_id': scene['id'],
                'title': scene['title'],
                'error': task.get('error', 'Unknown error')
            }
            
        except Exception as e:
            self.stats['failed'] += 1
            logger.error(f"❌ Exception during generation: {e}")
            
            return {
                'success': False,
                'scene_id': scene['id'],
                'title': scene['title'],
                'error': str(e)
            }
    
    async def generate_all_scenes(self):
        """Generate all showcase scenes."""
        logger.info("Starting RunwayML Showcase Generation")
        logger.info(f"Total scenes to generate: {len(SHOWCASE_SCENES)}")
        
        # Check credits first
        org_info = self.runway_client.get_organization_info()
        initial_credits = org_info.get('creditBalance', 0)
        logger.info(f"Credits available: {initial_credits}")
        
        estimated_credits = sum(s['duration'] * 5 for s in SHOWCASE_SCENES)
        logger.info(f"Estimated credits needed: {estimated_credits}")
        
        if initial_credits < estimated_credits:
            logger.warning(f"May not have enough credits to complete all scenes")
        
        # Generate scenes
        results = []
        
        for i, scene in enumerate(SHOWCASE_SCENES):
            logger.info(f"\nProcessing scene {i+1}/{len(SHOWCASE_SCENES)}")
            
            result = await self.generate_scene(scene)
            results.append(result)
            
            # Save progress
            with open(self.output_dir / "generation_log.json", "w") as f:
                json.dump({
                    'stats': self.stats,
                    'results': results
                }, f, indent=2)
            
            # Brief pause between scenes
            if i < len(SHOWCASE_SCENES) - 1:
                await asyncio.sleep(3)
        
        # Final summary
        await self.print_summary(results)
        
        return results
    
    async def print_summary(self, results: list):
        """Print generation summary."""
        logger.info("\n" + "="*70)
        logger.info("RUNWAY ML SHOWCASE GENERATION COMPLETE")
        logger.info("="*70)
        
        logger.info(f"\nGeneration Statistics:")
        logger.info(f"  Total Scenes: {self.stats['total_scenes']}")
        logger.info(f"  Successful: {self.stats['successful']}")
        logger.info(f"  Failed: {self.stats['failed']}")
        logger.info(f"  Total Credits Used: {self.stats['total_credits_used']}")
        logger.info(f"  Total Cost: ${self.stats['total_credits_used'] * 0.01:.2f}")
        
        if self.stats['generation_times']:
            avg_time = sum(self.stats['generation_times']) / len(self.stats['generation_times'])
            logger.info(f"  Average Generation Time: {avg_time:.1f} seconds")
        
        logger.info(f"\nGenerated Videos:")
        for result in results:
            if result['success']:
                logger.info(f"  ✅ {result['title']}")
                logger.info(f"     Path: {result['video_path']}")
                logger.info(f"     Time: {result['generation_time']:.1f}s")
                logger.info(f"     Credits: {result['credits_used']}")
            else:
                logger.info(f"  ❌ {result['title']}")
                logger.info(f"     Error: {result['error']}")
        
        # Create summary document
        summary_path = self.output_dir / "SHOWCASE_SUMMARY.md"
        with open(summary_path, "w") as f:
            f.write("# RunwayML Showcase Generation Results\n\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Statistics\n\n")
            f.write(f"- Total Scenes: {self.stats['total_scenes']}\n")
            f.write(f"- Successful: {self.stats['successful']}\n")
            f.write(f"- Failed: {self.stats['failed']}\n")
            f.write(f"- Total Credits Used: {self.stats['total_credits_used']}\n")
            f.write(f"- Total Cost: ${self.stats['total_credits_used'] * 0.01:.2f}\n\n")
            
            f.write("## Generated Videos\n\n")
            for result in results:
                if result['success']:
                    f.write(f"### ✅ {result['title']}\n\n")
                    f.write(f"- **File**: `{result['video_path']}`\n")
                    f.write(f"- **Generation Time**: {result['generation_time']:.1f} seconds\n")
                    f.write(f"- **Credits Used**: {result['credits_used']}\n")
                    f.write(f"- **Prompt**: {result['prompt'][:200]}...\n\n")
                else:
                    f.write(f"### ❌ {result['title']}\n\n")
                    f.write(f"- **Error**: {result['error']}\n\n")
        
        logger.info(f"\nSummary saved to: {summary_path}")


async def main():
    """Main entry point."""
    generator = RunwayShowcaseGenerator()
    
    # Generate all showcase scenes
    results = await generator.generate_all_scenes()
    
    # Create a montage script for combining videos
    if any(r['success'] for r in results):
        montage_script = generator.output_dir / "create_montage.sh"
        with open(montage_script, "w") as f:
            f.write("#!/bin/bash\n")
            f.write("# Script to create a montage of all generated videos\n\n")
            
            f.write("# Create file list\n")
            f.write("echo \"file list:\"\n")
            
            for result in results:
                if result['success']:
                    f.write(f"echo \"file '{os.path.basename(result['video_path'])}'\" >> filelist.txt\n")
            
            f.write("\n# Concatenate videos\n")
            f.write("ffmpeg -f concat -safe 0 -i filelist.txt -c copy runway_showcase_montage.mp4\n")
            f.write("\n# Add title cards between scenes (optional)\n")
            f.write("# ffmpeg -i runway_showcase_montage.mp4 -vf \"drawtext=text='RunwayML Showcase':x=(w-text_w)/2:y=(h-text_h)/2:fontsize=64:fontcolor=white\" runway_showcase_final.mp4\n")
        
        os.chmod(montage_script, 0o755)
        logger.info(f"\nMontage script created: {montage_script}")


if __name__ == "__main__":
    asyncio.run(main())