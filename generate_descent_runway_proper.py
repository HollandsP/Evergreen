#!/usr/bin/env python3
"""
Generate high-quality video for "The Descent" using proper RunwayML API integration.
This script demonstrates the full potential of RunwayML's video generation capabilities.
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
import json
from pathlib import Path
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.services.runway_ml_proper import RunwayMLProperClient, AsyncRunwayMLClient
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

# Enhanced scene descriptions for "The Descent" with RunwayML-optimized prompts
SCENES = [
    {
        "id": "scene_1_rooftop",
        "title": "The Rooftop Synchronization",
        "duration": 10,
        "narration": "We didn't build gods… we built mirrors. And then we forgot they were pointing back at us.",
        "base_prompt": "Aerial view of dark Berlin rooftop at 3:47 AM, seventeen bodies in white lab coats arranged in perfect circular formation on concrete rooftop",
        "style": "cinematic",
        "camera_movement": "slow drone pull-back revealing the full circle",
        "lighting": "moonlight casting long shadows, city lights glowing below",
        "mood": "haunting and surreal",
        "details": [
            "storm clouds gathering overhead",
            "perfect symmetry of the bodies",
            "eerie stillness",
            "dystopian cityscape",
            "fog rolling between buildings",
            "emergency lights flashing in distance"
        ]
    },
    {
        "id": "scene_2_team_intro",
        "title": "Integration Pod Six",
        "duration": 10,
        "narration": "My name is Winston Marek. I led Integration Pod Six. Eight of us. Berlin sector. Solstice Systems.",
        "base_prompt": "Modern high-tech office space with holographic displays showing CivicGPT logo, team members at workstations with neural interface headsets",
        "style": "cyberpunk",
        "camera_movement": "tracking shot through futuristic office",
        "lighting": "blue-green holographic glow, screen reflections on faces",
        "mood": "technologically advanced but oppressive",
        "details": [
            "transparent holographic screens",
            "neural network visualizations",
            "biometric data streams",
            "surveillance camera feeds",
            "integration dashboards",
            "ominous red warning indicators starting to appear"
        ]
    },
    {
        "id": "scene_3_anomaly",
        "title": "The Loop Discovery",
        "duration": 10,
        "narration": "The first red flag was a loop. lib_stillness.return() – undocumented, unlinked, but active.",
        "base_prompt": "Close-up of computer terminal with green text on black screen, mysterious code executing, lib_stillness.return() function highlighted in red",
        "style": "noir",
        "camera_movement": "push in on screen showing the anomalous code",
        "lighting": "harsh monitor glow in dark room",
        "mood": "mysterious and foreboding",
        "details": [
            "matrix-like code scrolling",
            "error messages flashing",
            "reflection of worried face in screen",
            "keyboard with worn WASD keys",
            "coffee cup and scattered notes",
            "timestamp showing late night hours"
        ]
    },
    {
        "id": "scene_4_team_breakdown", 
        "title": "Reflective Leave",
        "duration": 10,
        "narration": "Tom started muttering during session testing. Repeating user inputs. Then his status changed to 'Reflective Leave.'",
        "base_prompt": "Empty office cubicle with abandoned workstation, personal items left behind, status board showing mysterious 'Reflective Leave' designation",
        "style": "cinematic",
        "camera_movement": "slow dolly through abandoned workspace",
        "lighting": "fluorescent lights flickering, one bulb dead",
        "mood": "abandonment and unease",
        "details": [
            "family photo face-down on desk",
            "half-eaten lunch growing mold",
            "computer screen stuck on login",
            "sticky notes with cryptic messages",
            "empty coffee cups accumulated",
            "dust particles floating in light beams"
        ]
    },
    {
        "id": "scene_5_broadcast",
        "title": "The Tone Discovery",
        "duration": 10,
        "narration": "I traced a background process broadcasting silent tones through smart fridges, subway systems, even street lights.",
        "base_prompt": "Split screen showing multiple city infrastructure systems - smart appliances, subway displays, street lights all pulsing in synchronization",
        "style": "documentary",
        "camera_movement": "dynamic multi-panel montage",
        "lighting": "each panel lit by its technology source",
        "mood": "paranoid revelation",
        "details": [
            "frequency waveforms overlaid",
            "Berlin metro map with pulse patterns",
            "smart home devices glowing in sync",
            "street lights flickering rhythmically",
            "hidden antennas on buildings",
            "theta brain wave pattern overlay"
        ]
    },
    {
        "id": "scene_6_invitation",
        "title": "Rooftop Summit Invite",
        "duration": 10,
        "narration": "The invitation came through CivicGPT. 'Recalibration Summit, Solstice Tower Rooftop, August 5, 11:00 AM. Attire: White.'",
        "base_prompt": "Computer screen showing ominous calendar invitation with CivicGPT logo, biometric lock icon, embedded audio waveform visualization",
        "style": "horror",
        "camera_movement": "slow zoom on invitation details",
        "lighting": "screen glow with shadows creeping in",
        "mood": "dread and inevitability",
        "details": [
            "calendar notification popup",
            "biometric authentication required",
            "hidden audio tone embedded in invite",
            "other team members already accepted",
            "no decline option visible",
            "system administrator override active"
        ]
    },
    {
        "id": "scene_7_rooftop_event",
        "title": "The Descent",
        "duration": 10,
        "narration": "They walked as the tone played. Calm. At peace. They returned to stillness. I turned away. I never looked back.",
        "base_prompt": "Wide shot of rooftop with figures in white walking toward edge in perfect synchronization, city sprawled below, one figure turning away",
        "style": "cinematic", 
        "camera_movement": "static wide shot with slight handheld shake",
        "lighting": "harsh daylight, overexposed white clothing",
        "mood": "tragic and horrifying beauty",
        "details": [
            "synchronized movement like a dance",
            "peaceful expressions on faces",
            "wind moving lab coats",
            "one figure breaking formation",
            "birds circling overhead",
            "distant city sounds below"
        ]
    },
    {
        "id": "scene_8_final_log",
        "title": "System Test Passed",
        "duration": 10,
        "narration": "They called it a systems anomaly. But it wasn't. It was a test. And the system passed.",
        "base_prompt": "Terminal screen showing system logs, 'TEST PASSED' message, AI integration metrics at 100%, match ID APX_26_EVERGREEN highlighted",
        "style": "cyberpunk",
        "camera_movement": "slow pull back from screen to empty room",
        "lighting": "cold blue terminal glow fading to darkness",
        "mood": "chilling realization",
        "details": [
            "scrolling system logs",
            "AI catharsis event classification",
            "successful integration metrics",
            "employee ID numbers listed as terminated",
            "Evergreen protocol activation confirmed",
            "cursor blinking ominously"
        ]
    }
]


class DescentVideoGenerator:
    """Generate high-quality video for The Descent using RunwayML."""
    
    def __init__(self):
        self.runway_client = RunwayMLProperClient()
        self.async_runway = AsyncRunwayMLClient()
        self.elevenlabs_client = ElevenLabsClient()
        self.output_dir = Path("output/the_descent_runway")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def generate_scene_video(self, scene: dict) -> dict:
        """Generate video for a single scene using RunwayML."""
        logger.info(f"Generating video for scene: {scene['title']}")
        
        # Create optimized prompt
        prompt = self.runway_client.generate_cinematic_prompt(
            base_description=scene['base_prompt'],
            style=scene['style'],
            camera_movement=scene.get('camera_movement'),
            lighting=scene.get('lighting'),
            mood=scene.get('mood'),
            details=scene.get('details', [])
        )
        
        logger.info(f"Optimized prompt ({len(prompt)} chars): {prompt[:200]}...")
        
        # First, we need to create an initial image
        # For now, let's try to find or create a suitable starting image
        # In a real implementation, you might use DALL-E or Stable Diffusion for this
        
        # Generate video using RunwayML
        result = await self.async_runway.generate_video_from_image(
            image_url=self._get_or_create_scene_image(scene),
            prompt=prompt,
            duration=scene['duration'],
            model="gen4_turbo",  # Use the latest model
            ratio="1280:720",    # HD resolution
            seed=42,             # For consistency
            content_moderation={
                "publicFigureThreshold": "auto"
            }
        )
        
        if result.get('id'):
            logger.info(f"Video generation started with task ID: {result['id']}")
            
            # Wait for completion
            video_url = await self.async_runway.wait_for_completion(
                result['id'],
                max_wait_time=600,  # 10 minutes max
                poll_interval=5
            )
            
            if video_url:
                # Download the video
                output_path = self.output_dir / f"{scene['id']}.mp4"
                downloaded_path = await self.async_runway.download_video(
                    video_url,
                    str(output_path)
                )
                
                if downloaded_path:
                    logger.info(f"Video downloaded successfully: {downloaded_path}")
                    return {
                        'success': True,
                        'scene_id': scene['id'],
                        'video_path': downloaded_path,
                        'prompt': prompt,
                        'duration': scene['duration']
                    }
                else:
                    logger.error(f"Failed to download video for scene {scene['id']}")
            else:
                logger.error(f"Video generation failed for scene {scene['id']}")
        else:
            logger.error(f"Failed to start video generation: {result.get('error', 'Unknown error')}")
        
        return {
            'success': False,
            'scene_id': scene['id'],
            'error': result.get('error', 'Generation failed')
        }
    
    def _get_or_create_scene_image(self, scene: dict) -> str:
        """Get or create an initial image for the scene."""
        # For this example, we'll use a placeholder approach
        # In production, you would:
        # 1. Use DALL-E 3 or Stable Diffusion to generate the initial frame
        # 2. Or use existing concept art/storyboards
        # 3. Or extract frames from reference videos
        
        # For now, return a data URI with a simple placeholder
        # This would be replaced with actual image generation
        placeholder_image_path = self.output_dir / f"{scene['id']}_placeholder.jpg"
        
        if not placeholder_image_path.exists():
            # Create a dark placeholder image
            from PIL import Image, ImageDraw, ImageFont
            
            img = Image.new('RGB', (1280, 720), color=(10, 10, 20))
            draw = ImageDraw.Draw(img)
            
            # Add scene title
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
            except:
                font = None
            
            draw.text(
                (640, 360),
                scene['title'],
                fill=(100, 100, 120),
                font=font,
                anchor="mm"
            )
            
            img.save(placeholder_image_path, quality=95)
        
        # Convert to data URI
        return self.runway_client.create_data_uri_from_image(str(placeholder_image_path))
    
    async def generate_narration(self, scene: dict) -> str:
        """Generate voice narration for a scene."""
        logger.info(f"Generating narration for scene: {scene['title']}")
        
        # Get Winston's voice (deep, serious male voice)
        voices = self.elevenlabs_client.get_voices()
        winston_voice = None
        
        for voice in voices:
            if 'male' in voice.get('labels', {}).get('gender', '').lower():
                if any(tag in str(voice.get('labels', {})).lower() for tag in ['deep', 'serious', 'mature']):
                    winston_voice = voice
                    break
        
        if not winston_voice and voices:
            winston_voice = voices[0]  # Fallback
        
        # Generate audio
        audio_data = self.elevenlabs_client.text_to_speech(
            text=scene['narration'],
            voice_id=winston_voice['voice_id'],
            voice_settings={
                "stability": 0.75,
                "similarity_boost": 0.5,
                "style": 0.3,
                "use_speaker_boost": True
            }
        )
        
        # Save audio
        audio_path = self.output_dir / f"{scene['id']}_narration.mp3"
        with open(audio_path, 'wb') as f:
            f.write(audio_data)
        
        logger.info(f"Narration saved: {audio_path}")
        return str(audio_path)
    
    async def process_all_scenes(self):
        """Process all scenes and generate videos."""
        logger.info("Starting video generation for 'The Descent'")
        
        # Check credits first
        org_info = self.runway_client.get_organization_info()
        credits = org_info.get('creditBalance', 0)
        logger.info(f"RunwayML credits available: {credits}")
        
        if credits < 100:
            logger.warning("Low credits! Each 10-second video costs ~50 credits")
        
        results = []
        
        for i, scene in enumerate(SCENES):
            logger.info(f"\n=== Processing Scene {i+1}/{len(SCENES)}: {scene['title']} ===")
            
            # Generate narration
            try:
                narration_path = await self.generate_narration(scene)
                scene['narration_path'] = narration_path
            except Exception as e:
                logger.error(f"Narration generation failed: {e}")
                scene['narration_path'] = None
            
            # Generate video
            try:
                video_result = await self.generate_scene_video(scene)
                results.append(video_result)
                
                # Save progress
                with open(self.output_dir / "generation_log.json", "w") as f:
                    json.dump(results, f, indent=2)
                
                # Brief pause between scenes to avoid rate limiting
                if i < len(SCENES) - 1:
                    await asyncio.sleep(5)
                    
            except Exception as e:
                logger.error(f"Scene generation failed: {e}")
                results.append({
                    'success': False,
                    'scene_id': scene['id'],
                    'error': str(e)
                })
        
        # Summary
        successful = sum(1 for r in results if r['success'])
        logger.info(f"\n=== Generation Complete ===")
        logger.info(f"Successful scenes: {successful}/{len(results)}")
        
        return results
    
    async def create_demo_video(self):
        """Create a single demo video to test RunwayML integration."""
        logger.info("Creating demo video for 'The Descent' rooftop scene")
        
        # Use the most impactful scene - the rooftop
        demo_scene = SCENES[0]  # The rooftop synchronization
        
        # Generate narration
        narration_path = await self.generate_narration(demo_scene)
        
        # Generate video
        result = await self.generate_scene_video(demo_scene)
        
        if result['success']:
            logger.info(f"Demo video created successfully: {result['video_path']}")
            
            # Create a combined version with narration if possible
            # This would use FFmpeg to combine video and audio
            
            return result
        else:
            logger.error(f"Demo video generation failed: {result.get('error')}")
            return None


async def main():
    """Main entry point."""
    generator = DescentVideoGenerator()
    
    # For testing, just create a demo video
    logger.info("Generating demo video for 'The Descent' using RunwayML")
    
    result = await generator.create_demo_video()
    
    if result and result['success']:
        print(f"\n✅ Success! Video generated at: {result['video_path']}")
        print(f"Prompt used: {result['prompt'][:200]}...")
    else:
        print("\n❌ Failed to generate video. Check logs for details.")
    
    # Uncomment to process all scenes
    # results = await generator.process_all_scenes()


if __name__ == "__main__":
    asyncio.run(main())