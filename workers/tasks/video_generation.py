"""
Video generation tasks
"""
import re
import json
import os
from typing import Dict, List, Any, Optional
from celery import Task
from workers.celery_app import app
import structlog

logger = structlog.get_logger()


class VideoGenerationTask(Task):
    """Base class for video generation tasks"""
    name = "video_generation.base"
    max_retries = 3
    default_retry_delay = 60


class ScriptParser:
    """Parse LOG script format for video generation"""
    
    def __init__(self):
        self.timestamp_pattern = r'\[(\d+:\d+)[^\]]*\]'
        self.visual_pattern = r'Visual:\s*(.+?)(?=\n(?:Audio|Narration|ON-SCREEN|Visual|\[|$))'
        self.narration_pattern = r'(?:Narration|Audio)\s*\([^)]+\):\s*(.+?)(?=\n(?:Audio|Narration|Visual|ON-SCREEN|\[|$))'
        self.onscreen_pattern = r'ON-SCREEN[^:]*:\s*(.+?)(?=\n(?:Audio|Narration|Visual|ON-SCREEN|\[|$))'
    
    def parse_script(self, script_content: str) -> Dict[str, Any]:
        """Parse script content into structured data"""
        try:
            # Extract basic metadata
            title_match = re.search(r'SCRIPT:\s*(.+)', script_content)
            title = title_match.group(1).strip() if title_match else "Unknown"
            
            # Split script into timestamp sections
            sections = re.split(self.timestamp_pattern, script_content)
            
            scenes = []
            total_duration = 0
            
            # Process each timestamp section
            for i in range(1, len(sections), 2):
                if i + 1 < len(sections):
                    timestamp = sections[i]
                    content = sections[i + 1]
                    
                    scene = self._parse_scene(timestamp, content)
                    scenes.append(scene)
                    
                    # Calculate duration (rough estimate)
                    total_duration = max(total_duration, self._timestamp_to_seconds(timestamp) + 30)
            
            return {
                "title": title,
                "scenes": scenes,
                "total_duration": total_duration,
                "scene_count": len(scenes),
                "metadata": {
                    "parsed_at": "now",
                    "parser_version": "1.0"
                }
            }
            
        except Exception as e:
            logger.error(f"Script parsing failed: {str(e)}")
            raise
    
    def _parse_scene(self, timestamp: str, content: str) -> Dict[str, Any]:
        """Parse individual scene content"""
        # Extract scene title/description
        title_match = re.search(r'([^|]+)', content.split('\n')[0])
        title = title_match.group(1).strip() if title_match else f"Scene {timestamp}"
        
        # Extract visual descriptions
        visuals = re.findall(self.visual_pattern, content, re.DOTALL | re.MULTILINE)
        visual_descriptions = [v.strip().replace('\n', ' ') for v in visuals]
        
        # Extract narration/audio
        narrations = re.findall(self.narration_pattern, content, re.DOTALL | re.MULTILINE)
        narration_text = [n.strip().replace('\n', ' ') for n in narrations]
        
        # Extract on-screen text
        onscreen_texts = re.findall(self.onscreen_pattern, content, re.DOTALL | re.MULTILINE)
        onscreen_elements = [t.strip().replace('\n', ' ') for t in onscreen_texts]
        
        return {
            "timestamp": timestamp,
            "timestamp_seconds": self._timestamp_to_seconds(timestamp),
            "title": title,
            "visual_descriptions": visual_descriptions,
            "narration": narration_text,
            "onscreen_text": onscreen_elements,
            "raw_content": content.strip()
        }
    
    def _timestamp_to_seconds(self, timestamp: str) -> int:
        """Convert MM:SS timestamp to seconds"""
        try:
            parts = timestamp.split(':')
            return int(parts[0]) * 60 + int(parts[1])
        except:
            return 0


@app.task(bind=True, base=VideoGenerationTask, name="video_generation.process")
def process_video_generation(self, job_id: str, story_file: str, settings: dict):
    """
    Main video generation task
    
    Args:
        job_id: Unique job identifier
        story_file: Script content string or file path
        settings: Generation settings (voice, style, quality)
    """
    try:
        logger.info(
            "Starting video generation",
            job_id=job_id,
            story_content_length=len(story_file) if isinstance(story_file, str) else "unknown",
            settings=settings
        )
        
        logger.info("🔧 NEW SCRIPT PARSER VERSION 2.0 ACTIVE", job_id=job_id)
        
        # Step 1: Parse script content
        parser = ScriptParser()
        
        # Use story_file as content (it's passed as content, not file path)
        script_content = story_file
        
        logger.info("Parsing script content", job_id=job_id)
        parsed_script = parser.parse_script(script_content)
        
        logger.info(
            "Script parsed successfully",
            job_id=job_id,
            title=parsed_script.get("title"),
            scenes=parsed_script.get("scene_count"),
            duration=parsed_script.get("total_duration")
        )
        
        # Step 2: Generate voice narration (placeholder for now)
        logger.info("Generating voice narration", job_id=job_id)
        voice_files = _generate_voice_narration(job_id, parsed_script, settings)
        
        # Step 3: Create terminal UI effects (placeholder for now)
        logger.info("Creating terminal UI effects", job_id=job_id)
        ui_elements = _create_terminal_ui(job_id, parsed_script, settings)
        
        # Step 4: Generate visual scenes (placeholder for now)
        logger.info("Generating visual scenes", job_id=job_id)
        visual_assets = _generate_visual_scenes(job_id, parsed_script, settings)
        
        # Step 5: Assemble final video (placeholder for now)
        logger.info("Assembling final video", job_id=job_id)
        output_file = _assemble_video(job_id, parsed_script, voice_files, ui_elements, visual_assets, settings)
        
        result = {
            "job_id": job_id,
            "status": "completed",
            "output_file": output_file,
            "duration": parsed_script.get("total_duration", 180),
            "size_mb": 250,  # Placeholder
            "parsed_script": {
                "title": parsed_script.get("title"),
                "scenes": parsed_script.get("scene_count"),
                "total_duration": parsed_script.get("total_duration")
            },
            "assets_generated": {
                "voice_files": len(voice_files),
                "ui_elements": len(ui_elements),
                "visual_assets": len(visual_assets)
            }
        }
        
        logger.info("Video generation completed successfully", result=result)
        return result
        
    except Exception as e:
        logger.error(
            "Video generation failed",
            job_id=job_id,
            error=str(e),
            exc_info=True
        )
        
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


def _generate_voice_narration(job_id: str, parsed_script: Dict, settings: Dict) -> List[str]:
    """Generate voice narration files using ElevenLabs"""
    voice_files = []
    
    # Check for API key in environment
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    
    if not api_key:
        logger.warning("ElevenLabs API key not configured, using mock voice generation")
        # Create mock voice files for demonstration
        for i, scene in enumerate(parsed_script.get("scenes", [])):
            for j, narration in enumerate(scene.get("narration", [])):
                if narration.strip():
                    timestamp_clean = scene['timestamp'].replace(':', '_')
                    voice_file = f"/app/output/audio/{job_id}_scene_{timestamp_clean}_{j}.mp3"
                    os.makedirs(os.path.dirname(voice_file), exist_ok=True)
                    
                    # Create a placeholder file
                    with open(voice_file, 'wb') as f:
                        f.write(b"MOCK_AUDIO_FILE_" + narration.encode('utf-8')[:50])
                    
                    voice_files.append(voice_file)
                    logger.info(
                        "Mock voice segment created",
                        job_id=job_id,
                        file=voice_file,
                        text=narration[:50] + "..."
                    )
        return voice_files
    
    # Try to use ElevenLabs if API key is available
    try:
        # Dynamic import to avoid module errors
        import requests
        
        # Voice ID mapping based on voice type
        voice_id_map = {
            "male_calm": "21m00Tcm4TlvDq8ikWAM",
            "female_calm": "AZnzlk1XvdvUeBnXmlld",
            "male_dramatic": "pNInz6obpgDQGcFmaJgB",
            "female_dramatic": "MF3mGyEYCl7XYWbV9V6O",
        }
        
        voice_type = settings.get("voice_type", "male_calm")
        voice_id = voice_id_map.get(voice_type, voice_id_map["male_calm"])
        
        # Extract all narration text from scenes
        for i, scene in enumerate(parsed_script.get("scenes", [])):
            for j, narration in enumerate(scene.get("narration", [])):
                if narration.strip():
                    try:
                        # Generate voice audio
                        logger.info(
                            "Generating voice segment with ElevenLabs",
                            job_id=job_id,
                            timestamp=scene.get("timestamp"),
                            text_length=len(narration),
                            voice_type=voice_type
                        )
                        
                        # Call ElevenLabs API directly
                        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
                        
                        headers = {
                            "Accept": "audio/mpeg",
                            "xi-api-key": api_key,
                            "Content-Type": "application/json"
                        }
                        
                        payload = {
                            "text": narration,
                            "model_id": "eleven_monolingual_v1",
                            "voice_settings": {
                                "stability": 0.5,
                                "similarity_boost": 0.75,
                                "style": 0.0,
                                "use_speaker_boost": True
                            }
                        }
                        
                        response = requests.post(url, json=payload, headers=headers)
                        
                        if response.status_code == 200:
                            audio_data = response.content
                            
                            # Save audio file
                            timestamp_clean = scene['timestamp'].replace(':', '_')
                            voice_file = f"/app/output/audio/{job_id}_scene_{timestamp_clean}_{j}.mp3"
                            os.makedirs(os.path.dirname(voice_file), exist_ok=True)
                            
                            with open(voice_file, 'wb') as f:
                                f.write(audio_data)
                            
                            voice_files.append(voice_file)
                            
                            logger.info(
                                "Voice segment generated successfully",
                                job_id=job_id,
                                file=voice_file,
                                size=len(audio_data)
                            )
                        else:
                            logger.error(
                                f"ElevenLabs API error: {response.status_code}",
                                job_id=job_id,
                                response=response.text[:200]
                            )
                            # Fall back to mock
                            timestamp_clean = scene['timestamp'].replace(':', '_')
                            voice_file = f"/app/output/audio/{job_id}_scene_{timestamp_clean}_{j}.mp3"
                            os.makedirs(os.path.dirname(voice_file), exist_ok=True)
                            
                            with open(voice_file, 'wb') as f:
                                f.write(b"MOCK_AUDIO_DUE_TO_API_ERROR")
                            
                            voice_files.append(voice_file)
                        
                    except Exception as e:
                        logger.error(
                            f"Failed to generate voice for scene {scene.get('timestamp')}: {e}",
                            job_id=job_id,
                            scene=scene.get("timestamp"),
                            error=str(e)
                        )
                        # Continue with other segments even if one fails
                        continue
    
    except Exception as e:
        logger.error(f"Error in voice generation: {e}")
        # Fall back to mock generation
        for i, scene in enumerate(parsed_script.get("scenes", [])):
            for j, narration in enumerate(scene.get("narration", [])):
                if narration.strip():
                    timestamp_clean = scene['timestamp'].replace(':', '_')
                    voice_file = f"/app/output/audio/{job_id}_scene_{timestamp_clean}_{j}.mp3"
                    os.makedirs(os.path.dirname(voice_file), exist_ok=True)
                    
                    with open(voice_file, 'wb') as f:
                        f.write(b"MOCK_AUDIO_FILE_ERROR")
                    
                    voice_files.append(voice_file)
    
    return voice_files


def _create_terminal_ui(job_id: str, parsed_script: Dict, settings: Dict) -> List[str]:
    """Create terminal UI animation assets"""
    ui_elements = []
    
    try:
        # Import terminal effects module
        from workers.effects import TerminalRenderer, AnimationSequence, TerminalTheme, parse_terminal_commands
        
        # Determine theme from settings
        theme_map = {
            "dark": TerminalTheme.DARK,
            "light": TerminalTheme.LIGHT,
            "matrix": TerminalTheme.MATRIX,
            "hacker": TerminalTheme.HACKER,
            "vscode": TerminalTheme.VSCODE
        }
        terminal_theme = theme_map.get(settings.get("terminal_theme", "dark"), TerminalTheme.DARK)
        
        # Extract all on-screen text from scenes
        for i, scene in enumerate(parsed_script.get("scenes", [])):
            for j, onscreen in enumerate(scene.get("onscreen_text", [])):
                if onscreen.strip():
                    try:
                        # Create renderer for this animation
                        renderer = TerminalRenderer(
                            width=1920,
                            height=1080,
                            cols=80,
                            rows=24,
                            theme=terminal_theme,
                            font_size=20
                        )
                        
                        # Parse terminal commands from on-screen text
                        commands = parse_terminal_commands(onscreen)
                        
                        # Calculate duration based on scene duration or default
                        scene_duration = 10.0  # Default 10 seconds per terminal animation
                        if i + 1 < len(parsed_script.get("scenes", [])):
                            next_scene = parsed_script["scenes"][i + 1]
                            scene_duration = next_scene["timestamp_seconds"] - scene["timestamp_seconds"]
                        
                        # Create animation sequence
                        sequence = AnimationSequence(renderer)
                        current_time = 0.0
                        
                        for cmd in commands:
                            if cmd.get('instant', False):
                                sequence.add_instant_text(cmd['text'] + '\n', current_time)
                                current_time += 0.5  # Small pause after instant text
                            else:
                                # Calculate typing duration
                                typing_duration = len(cmd['text']) * cmd.get('typing_speed', 0.05)
                                sequence.add_typing(cmd['text'] + '\n', current_time, typing_duration)
                                current_time += typing_duration + 0.5  # Pause after typing
                        
                        # Render frames
                        frames = []
                        
                        # For simple implementation, create typing animation for entire text
                        typing_duration = min(scene_duration * 0.8, current_time)  # Use 80% of scene duration
                        frames = renderer.create_typing_animation(onscreen, typing_duration, fps=30)
                        
                        # Export video
                        timestamp_clean = scene['timestamp'].replace(':', '_')
                        ui_file = f"/app/output/ui/{job_id}_ui_{timestamp_clean}_{j}.mp4"
                        os.makedirs(os.path.dirname(ui_file), exist_ok=True)
                        
                        renderer.export_video(frames, ui_file, fps=30)
                        ui_elements.append(ui_file)
                        
                        logger.info(
                            "Terminal UI animation created",
                            job_id=job_id,
                            file=ui_file,
                            timestamp=scene.get("timestamp"),
                            frame_count=len(frames),
                            duration=len(frames) / 30.0
                        )
                        
                    except Exception as e:
                        logger.error(
                            f"Failed to create terminal animation: {e}",
                            job_id=job_id,
                            scene=scene.get("timestamp"),
                            error=str(e)
                        )
                        # Create placeholder file on error
                        timestamp_clean = scene['timestamp'].replace(':', '_')
                        ui_file = f"/app/output/ui/{job_id}_ui_{timestamp_clean}_{j}.mp4"
                        os.makedirs(os.path.dirname(ui_file), exist_ok=True)
                        with open(ui_file, 'w') as f:
                            f.write("TERMINAL_UI_PLACEHOLDER")
                        ui_elements.append(ui_file)
    
    except ImportError as e:
        logger.error(f"Failed to import terminal effects module: {e}")
        # Fall back to placeholder generation
        for scene in parsed_script.get("scenes", []):
            for j, onscreen in enumerate(scene.get("onscreen_text", [])):
                if onscreen.strip():
                    timestamp_clean = scene['timestamp'].replace(':', '_')
                    ui_file = f"/app/output/ui/{job_id}_ui_{timestamp_clean}_{j}.mp4"
                    os.makedirs(os.path.dirname(ui_file), exist_ok=True)
                    with open(ui_file, 'w') as f:
                        f.write("TERMINAL_UI_PLACEHOLDER")
                    ui_elements.append(ui_file)
    
    return ui_elements


def _generate_visual_scenes(job_id: str, parsed_script: Dict, settings: Dict) -> List[str]:
    """Generate visual scenes using Runway API"""
    visual_assets = []
    
    # Check for API key in environment
    api_key = os.environ.get("RUNWAY_API_KEY")
    
    if not api_key:
        logger.warning("Runway API key not configured, using placeholder video generation")
        # Create placeholder videos
        for scene in parsed_script.get("scenes", []):
            for i, visual in enumerate(scene.get("visual_descriptions", [])):
                if visual.strip():
                    timestamp_clean = scene['timestamp'].replace(':', '_')
                    visual_file = f"/app/output/visuals/{job_id}_visual_{timestamp_clean}_{i}.mp4"
                    os.makedirs(os.path.dirname(visual_file), exist_ok=True)
                    
                    # Create a placeholder file
                    with open(visual_file, 'wb') as f:
                        f.write(b"PLACEHOLDER_VIDEO_FILE_" + visual.encode('utf-8')[:50])
                    
                    visual_assets.append(visual_file)
                    logger.info(
                        "Placeholder visual created",
                        job_id=job_id,
                        file=visual_file,
                        description=visual[:50] + "..."
                    )
        return visual_assets
    
    try:
        # Import RunwayClient
        import sys
        sys.path.append('/app')
        from src.services.runway_client import RunwayClient
        client = RunwayClient(api_key=api_key)
        
        # Style mapping for prompt enhancement
        style_prompts = {
            "techwear": "cyberpunk aesthetic, neon accents, urban environment, high-tech fashion, cinematic lighting",
            "minimalist": "clean aesthetic, simple composition, minimal design, soft lighting",
            "vintage": "retro aesthetic, film grain, nostalgic mood, warm tones",
            "futuristic": "sci-fi aesthetic, holographic elements, advanced technology, dramatic lighting"
        }
        
        style = settings.get("style", "techwear")
        style_enhancement = style_prompts.get(style, "cinematic quality, professional lighting")
        
        # Process each visual description
        generation_jobs = []
        
        for scene in parsed_script.get("scenes", []):
            scene_duration = 10.0  # Default duration
            
            # Calculate actual scene duration
            if scene.get("timestamp_seconds", 0) > 0:
                current_time = scene["timestamp_seconds"]
                # Find next scene timestamp
                scene_index = parsed_script["scenes"].index(scene)
                if scene_index + 1 < len(parsed_script["scenes"]):
                    next_scene = parsed_script["scenes"][scene_index + 1]
                    scene_duration = next_scene["timestamp_seconds"] - current_time
                else:
                    # Last scene - use remaining duration
                    scene_duration = parsed_script.get("total_duration", 60) - current_time
            
            for i, visual in enumerate(scene.get("visual_descriptions", [])):
                if visual.strip():
                    # Enhance prompt with style and quality modifiers
                    enhanced_prompt = f"{visual}, {style_enhancement}, 4K quality, smooth motion"
                    
                    # Determine video duration (max 16 seconds for Runway Gen-2)
                    video_duration = min(scene_duration, 16.0)
                    
                    logger.info(
                        "Submitting visual generation request",
                        job_id=job_id,
                        timestamp=scene.get("timestamp"),
                        prompt_length=len(enhanced_prompt),
                        duration=video_duration
                    )
                    
                    try:
                        # Submit generation job
                        generation_job = client.generate_video(
                            prompt=enhanced_prompt,
                            duration=video_duration,
                            resolution="1920x1080",
                            fps=30,
                            style=style,
                            camera_movement="smooth" if "motion" in visual.lower() else "static"
                        )
                        
                        generation_jobs.append({
                            'job': generation_job,
                            'scene': scene,
                            'visual_index': i,
                            'description': visual
                        })
                        
                        logger.info(
                            "Visual generation job submitted",
                            job_id=job_id,
                            generation_id=generation_job['id'],
                            timestamp=scene.get("timestamp")
                        )
                        
                    except Exception as e:
                        logger.error(
                            f"Failed to submit visual generation: {e}",
                            job_id=job_id,
                            scene=scene.get("timestamp"),
                            error=str(e)
                        )
        
        # Poll for completion
        import time
        max_wait_time = 300  # 5 minutes max
        poll_interval = 5    # Check every 5 seconds
        start_time = time.time()
        
        for job_info in generation_jobs:
            generation_job = job_info['job']
            scene = job_info['scene']
            visual_index = job_info['visual_index']
            
            while time.time() - start_time < max_wait_time:
                try:
                    status = client.get_generation_status(generation_job['id'])
                    
                    logger.info(
                        "Generation status",
                        job_id=job_id,
                        generation_id=generation_job['id'],
                        status=status['status'],
                        progress=status.get('progress', 0)
                    )
                    
                    if status['status'] == 'completed':
                        # Download video
                        video_data = client.download_video(status['video_url'])
                        
                        # Save video file
                        timestamp_clean = scene['timestamp'].replace(':', '_')
                        visual_file = f"/app/output/visuals/{job_id}_visual_{timestamp_clean}_{visual_index}.mp4"
                        os.makedirs(os.path.dirname(visual_file), exist_ok=True)
                        
                        with open(visual_file, 'wb') as f:
                            f.write(video_data)
                        
                        visual_assets.append(visual_file)
                        
                        logger.info(
                            "Visual scene generated successfully",
                            job_id=job_id,
                            file=visual_file,
                            size=len(video_data)
                        )
                        break
                        
                    elif status['status'] == 'failed':
                        logger.error(
                            "Visual generation failed",
                            job_id=job_id,
                            generation_id=generation_job['id'],
                            error=status.get('error', 'Unknown error')
                        )
                        break
                    
                    time.sleep(poll_interval)
                    
                except Exception as e:
                    logger.error(
                        f"Error polling generation status: {e}",
                        job_id=job_id,
                        generation_id=generation_job['id'],
                        error=str(e)
                    )
                    break
            else:
                logger.warning(
                    "Visual generation timed out",
                    job_id=job_id,
                    generation_id=generation_job['id']
                )
                
                # Create placeholder for timed out generation
                timestamp_clean = scene['timestamp'].replace(':', '_')
                visual_file = f"/app/output/visuals/{job_id}_visual_{timestamp_clean}_{visual_index}.mp4"
                os.makedirs(os.path.dirname(visual_file), exist_ok=True)
                
                with open(visual_file, 'wb') as f:
                    f.write(b"TIMEOUT_PLACEHOLDER_VIDEO")
                
                visual_assets.append(visual_file)
    
    except ImportError as e:
        logger.error(f"Failed to import RunwayClient: {e}")
        # Fall back to placeholder generation
        for scene in parsed_script.get("scenes", []):
            for i, visual in enumerate(scene.get("visual_descriptions", [])):
                if visual.strip():
                    timestamp_clean = scene['timestamp'].replace(':', '_')
                    visual_file = f"/app/output/visuals/{job_id}_visual_{timestamp_clean}_{i}.mp4"
                    os.makedirs(os.path.dirname(visual_file), exist_ok=True)
                    
                    with open(visual_file, 'wb') as f:
                        f.write(b"IMPORT_ERROR_PLACEHOLDER_VIDEO")
                    
                    visual_assets.append(visual_file)
    
    except Exception as e:
        logger.error(f"Unexpected error in visual generation: {e}")
        # Ensure we return something even on error
        for scene in parsed_script.get("scenes", []):
            for i, visual in enumerate(scene.get("visual_descriptions", [])):
                if visual.strip():
                    timestamp_clean = scene['timestamp'].replace(':', '_')
                    visual_file = f"/app/output/visuals/{job_id}_visual_{timestamp_clean}_{i}.mp4"
                    os.makedirs(os.path.dirname(visual_file), exist_ok=True)
                    
                    with open(visual_file, 'wb') as f:
                        f.write(b"ERROR_PLACEHOLDER_VIDEO")
                    
                    visual_assets.append(visual_file)
    
    return visual_assets


def _assemble_video(job_id: str, parsed_script: Dict, voice_files: List[str], 
                   ui_elements: List[str], visual_assets: List[str], settings: Dict) -> str:
    """Assemble final video using FFmpeg"""
    output_file = f"/app/output/exports/{job_id}.mp4"
    
    try:
        import subprocess
        
        logger.info(
            "Starting video assembly",
            job_id=job_id,
            output_file=output_file,
            voice_files=len(voice_files),
            ui_elements=len(ui_elements),
            visual_assets=len(visual_assets),
            quality=settings.get("quality", "high")
        )
        
        # Create output directory
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Create video composer
        composer = VideoComposer(job_id, parsed_script, settings)
        
        # Build timeline mapping assets to scenes
        timeline = composer.build_timeline(voice_files, ui_elements, visual_assets)
        
        logger.info(
            "Timeline built",
            job_id=job_id,
            timeline_entries=len(timeline),
            total_duration=composer.total_duration
        )
        
        # Generate and execute FFmpeg command
        success = composer.assemble_video(timeline, output_file)
        
        if success and os.path.exists(output_file):
            # Get file size
            file_size = os.path.getsize(output_file) / (1024 * 1024)  # MB
            
            logger.info(
                "Video assembly completed",
                job_id=job_id,
                output_file=output_file,
                size_mb=f"{file_size:.1f}",
                duration=composer.total_duration
            )
            
            return output_file
        else:
            raise Exception("FFmpeg assembly failed")
            
    except Exception as e:
        logger.error(f"Video assembly failed: {e}", job_id=job_id, error=str(e))
        
        # Create placeholder on error
        with open(output_file, 'w') as f:
            f.write(f"Video assembly failed for job {job_id}\n")
            f.write(f"Error: {str(e)}\n")
        
        return output_file


class VideoComposer:
    """Handles video composition and FFmpeg assembly"""
    
    def __init__(self, job_id: str, parsed_script: Dict, settings: Dict):
        self.job_id = job_id
        self.parsed_script = parsed_script
        self.settings = settings
        self.total_duration = parsed_script.get("total_duration", 60)
        
    def build_timeline(self, voice_files: List[str], ui_elements: List[str], 
                      visual_assets: List[str]) -> List[Dict]:
        """Build timeline mapping assets to scenes"""
        timeline = []
        
        # Parse asset filenames to extract timestamps
        voice_map = self._map_assets_by_timestamp(voice_files)
        ui_map = self._map_assets_by_timestamp(ui_elements)
        visual_map = self._map_assets_by_timestamp(visual_assets)
        
        # Build timeline entries for each scene
        for scene in self.parsed_script.get("scenes", []):
            timestamp = scene["timestamp"]
            timestamp_clean = timestamp.replace(':', '_')
            
            # Calculate scene duration
            scene_start = scene["timestamp_seconds"]
            scene_index = self.parsed_script["scenes"].index(scene)
            
            if scene_index + 1 < len(self.parsed_script["scenes"]):
                next_scene = self.parsed_script["scenes"][scene_index + 1]
                scene_duration = next_scene["timestamp_seconds"] - scene_start
            else:
                scene_duration = self.total_duration - scene_start
            
            # Ensure minimum duration
            scene_duration = max(scene_duration, 2.0)
            
            entry = {
                "scene": scene,
                "start": scene_start,
                "duration": scene_duration,
                "voice": voice_map.get(timestamp_clean, []),
                "ui": ui_map.get(timestamp_clean, []),
                "visual": visual_map.get(timestamp_clean, [])
            }
            
            timeline.append(entry)
            
        return timeline
    
    def _map_assets_by_timestamp(self, asset_files: List[str]) -> Dict[str, List[str]]:
        """Map asset files to timestamps based on filenames"""
        asset_map = {}
        
        for file_path in asset_files:
            # Extract timestamp from filename
            # Pattern: {job_id}_type_{timestamp}_{index}.ext
            filename = os.path.basename(file_path)
            parts = filename.split('_')
            
            if len(parts) >= 3:
                # Find timestamp part (e.g., "0_00" for "0:00")
                for i, part in enumerate(parts):
                    if i > 0 and parts[i-1] in ['scene', 'ui', 'visual']:
                        timestamp = part
                        if i + 1 < len(parts):
                            timestamp = f"{timestamp}_{parts[i+1]}"
                        
                        if timestamp not in asset_map:
                            asset_map[timestamp] = []
                        asset_map[timestamp].append(file_path)
                        break
        
        return asset_map
    
    def assemble_video(self, timeline: List[Dict], output_file: str) -> bool:
        """Execute FFmpeg assembly based on composition mode"""
        import subprocess
        
        # Determine composition mode
        has_visuals = any(entry["visual"] for entry in timeline)
        has_ui = any(entry["ui"] for entry in timeline)
        has_audio = any(entry["voice"] for entry in timeline)
        
        if not (has_visuals or has_ui or has_audio):
            logger.error("No assets to assemble", job_id=self.job_id)
            return False
        
        # Choose assembly strategy
        if has_visuals and has_ui:
            # Full composition with overlay
            return self._assemble_with_overlay(timeline, output_file)
        elif has_visuals:
            # Visual-only with audio
            return self._assemble_visual_only(timeline, output_file)
        elif has_ui:
            # Terminal UI only with audio
            return self._assemble_ui_only(timeline, output_file)
        else:
            # Audio-only (podcast style)
            return self._assemble_audio_only(timeline, output_file)
    
    def _assemble_with_overlay(self, timeline: List[Dict], output_file: str) -> bool:
        """Assemble video with terminal UI overlaid on visual scenes"""
        import subprocess
        import tempfile
        
        try:
            # Create temporary files for intermediate processing
            temp_dir = tempfile.mkdtemp()
            
            # Step 1: Create visual track with transitions
            visual_segments = []
            for i, entry in enumerate(timeline):
                if entry["visual"]:
                    # Use first visual asset for scene
                    visual_file = entry["visual"][0]
                    
                    # Prepare segment with fade transitions
                    segment_file = f"{temp_dir}/visual_segment_{i}.mp4"
                    
                    # Add fade in/out for smooth transitions
                    fade_duration = 0.5
                    ffmpeg_cmd = [
                        "ffmpeg", "-i", visual_file,
                        "-vf", f"fade=t=in:st=0:d={fade_duration},fade=t=out:st={entry['duration']-fade_duration}:d={fade_duration}",
                        "-t", str(entry["duration"]),
                        "-c:v", "libx264", "-preset", "fast",
                        "-y", segment_file
                    ]
                    
                    result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
                    if result.returncode == 0:
                        visual_segments.append(segment_file)
                    else:
                        logger.error(f"Failed to process visual segment: {result.stderr}")
                else:
                    # Create black frame for missing visuals
                    segment_file = f"{temp_dir}/black_segment_{i}.mp4"
                    ffmpeg_cmd = [
                        "ffmpeg",
                        "-f", "lavfi", "-i", f"color=c=black:s=1920x1080:d={entry['duration']}",
                        "-c:v", "libx264", "-preset", "fast",
                        "-y", segment_file
                    ]
                    subprocess.run(ffmpeg_cmd, capture_output=True)
                    visual_segments.append(segment_file)
            
            # Step 2: Concatenate visual segments
            concat_list = f"{temp_dir}/concat_list.txt"
            with open(concat_list, 'w') as f:
                for segment in visual_segments:
                    f.write(f"file '{segment}'\n")
            
            visual_track = f"{temp_dir}/visual_track.mp4"
            ffmpeg_cmd = [
                "ffmpeg", "-f", "concat", "-safe", "0", "-i", concat_list,
                "-c", "copy", "-y", visual_track
            ]
            
            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"Failed to concatenate visuals: {result.stderr}")
                return False
            
            # Step 3: Create overlay composition with terminal UI
            if any(entry["ui"] for entry in timeline):
                # Complex filter for overlay composition
                filter_complex = self._build_overlay_filter(timeline, temp_dir)
                
                # Collect all input files
                input_files = ["-i", visual_track]
                for entry in timeline:
                    if entry["ui"]:
                        input_files.extend(["-i", entry["ui"][0]])
                
                # Build final composition
                composition_file = f"{temp_dir}/composition.mp4"
                ffmpeg_cmd = ["ffmpeg"] + input_files + [
                    "-filter_complex", filter_complex,
                    "-map", "[outv]",
                    "-c:v", "libx264", "-preset", "fast",
                    "-y", composition_file
                ]
                
                result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.error(f"Failed to create overlay composition: {result.stderr}")
                    composition_file = visual_track
            else:
                composition_file = visual_track
            
            # Step 4: Add audio track
            if any(entry["voice"] for entry in timeline):
                # Concatenate audio files
                audio_concat = self._concatenate_audio(timeline, temp_dir)
                
                # Merge audio with video
                ffmpeg_cmd = [
                    "ffmpeg",
                    "-i", composition_file,
                    "-i", audio_concat,
                    "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-shortest",  # Match duration to shortest stream
                    "-y", output_file
                ]
            else:
                # No audio, just copy video
                ffmpeg_cmd = [
                    "ffmpeg",
                    "-i", composition_file,
                    "-c:v", "copy",
                    "-y", output_file
                ]
            
            # Execute final assembly
            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
            
            # Cleanup temp files
            import shutil
            shutil.rmtree(temp_dir)
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Error in overlay assembly: {e}")
            return False
    
    def _build_overlay_filter(self, timeline: List[Dict], temp_dir: str) -> str:
        """Build FFmpeg filter for terminal UI overlay"""
        filter_parts = []
        
        # Scale and position terminal UI as picture-in-picture
        ui_scale = "640:360"  # 1/3 size of 1920x1080
        ui_x = "W-w-50"  # 50 pixels from right
        ui_y = "H-h-50"  # 50 pixels from bottom
        
        current_input = 0  # Visual track is input 0
        
        for i, entry in enumerate(timeline):
            if entry["ui"]:
                ui_input = current_input + 1
                
                # Create overlay with timing
                if i == 0:
                    # First overlay
                    filter_parts.append(
                        f"[{ui_input}:v]scale={ui_scale}[ui{i}];"
                        f"[0:v][ui{i}]overlay=x={ui_x}:y={ui_y}:"
                        f"enable='between(t,{entry['start']},{entry['start']+entry['duration']})'[v{i}]"
                    )
                else:
                    # Subsequent overlays
                    prev = f"v{i-1}" if i > 0 else "0:v"
                    filter_parts.append(
                        f"[{ui_input}:v]scale={ui_scale}[ui{i}];"
                        f"[{prev}][ui{i}]overlay=x={ui_x}:y={ui_y}:"
                        f"enable='between(t,{entry['start']},{entry['start']+entry['duration']})'[v{i}]"
                    )
                
                current_input = ui_input
        
        # Final output
        last_video = f"v{len([e for e in timeline if e['ui']])-1}" if filter_parts else "0:v"
        filter_parts.append(f"[{last_video}]copy[outv]")
        
        return ";".join(filter_parts)
    
    def _concatenate_audio(self, timeline: List[Dict], temp_dir: str) -> str:
        """Concatenate audio files with proper timing"""
        import subprocess
        
        # Create silence for gaps
        audio_segments = []
        last_end = 0
        
        for entry in timeline:
            if entry["voice"]:
                # Add silence if there's a gap
                if entry["start"] > last_end:
                    silence_duration = entry["start"] - last_end
                    silence_file = f"{temp_dir}/silence_{last_end}.mp3"
                    
                    ffmpeg_cmd = [
                        "ffmpeg",
                        "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo:d={silence_duration}",
                        "-c:a", "mp3", "-b:a", "192k",
                        "-y", silence_file
                    ]
                    subprocess.run(ffmpeg_cmd, capture_output=True)
                    audio_segments.append(silence_file)
                
                # Add voice file
                audio_segments.append(entry["voice"][0])
                last_end = entry["start"] + entry["duration"]
        
        # Concatenate all audio segments
        if audio_segments:
            concat_list = f"{temp_dir}/audio_concat.txt"
            with open(concat_list, 'w') as f:
                for segment in audio_segments:
                    f.write(f"file '{segment}'\n")
            
            audio_track = f"{temp_dir}/audio_track.mp3"
            ffmpeg_cmd = [
                "ffmpeg", "-f", "concat", "-safe", "0", "-i", concat_list,
                "-c:a", "mp3", "-b:a", "192k",
                "-y", audio_track
            ]
            
            subprocess.run(ffmpeg_cmd, capture_output=True)
            return audio_track
        
        return None
    
    def _assemble_visual_only(self, timeline: List[Dict], output_file: str) -> bool:
        """Assemble video with only visual scenes and audio"""
        # Similar to overlay but without terminal UI
        return self._simple_concatenation(timeline, output_file, "visual")
    
    def _assemble_ui_only(self, timeline: List[Dict], output_file: str) -> bool:
        """Assemble video with only terminal UI and audio"""
        return self._simple_concatenation(timeline, output_file, "ui")
    
    def _assemble_audio_only(self, timeline: List[Dict], output_file: str) -> bool:
        """Create audio-only output (podcast style)"""
        import subprocess
        import tempfile
        
        temp_dir = tempfile.mkdtemp()
        audio_track = self._concatenate_audio(timeline, temp_dir)
        
        if audio_track:
            # Create video with waveform visualization
            ffmpeg_cmd = [
                "ffmpeg",
                "-i", audio_track,
                "-filter_complex", "[0:a]showwaves=s=1920x1080:mode=cline:rate=25:colors=white[v]",
                "-map", "[v]", "-map", "0:a",
                "-c:v", "libx264", "-preset", "fast",
                "-c:a", "copy",
                "-y", output_file
            ]
            
            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
            
            # Cleanup
            import shutil
            shutil.rmtree(temp_dir)
            
            return result.returncode == 0
        
        return False
    
    def _simple_concatenation(self, timeline: List[Dict], output_file: str, asset_type: str) -> bool:
        """Simple concatenation of video assets"""
        import subprocess
        import tempfile
        
        try:
            temp_dir = tempfile.mkdtemp()
            
            # Collect video segments
            video_segments = []
            for i, entry in enumerate(timeline):
                if entry[asset_type]:
                    video_segments.append(entry[asset_type][0])
                else:
                    # Create black frame
                    black_file = f"{temp_dir}/black_{i}.mp4"
                    ffmpeg_cmd = [
                        "ffmpeg",
                        "-f", "lavfi", "-i", f"color=c=black:s=1920x1080:d={entry['duration']}",
                        "-c:v", "libx264", "-preset", "fast",
                        "-y", black_file
                    ]
                    subprocess.run(ffmpeg_cmd, capture_output=True)
                    video_segments.append(black_file)
            
            # Create concat list
            concat_list = f"{temp_dir}/concat.txt"
            with open(concat_list, 'w') as f:
                for segment in video_segments:
                    f.write(f"file '{segment}'\n")
            
            # Concatenate with audio if available
            if any(entry["voice"] for entry in timeline):
                audio_track = self._concatenate_audio(timeline, temp_dir)
                
                ffmpeg_cmd = [
                    "ffmpeg",
                    "-f", "concat", "-safe", "0", "-i", concat_list,
                    "-i", audio_track,
                    "-map", "0:v", "-map", "1:a",
                    "-c:v", "libx264", "-preset", "fast",
                    "-c:a", "aac", "-b:a", "192k",
                    "-shortest",
                    "-y", output_file
                ]
            else:
                ffmpeg_cmd = [
                    "ffmpeg",
                    "-f", "concat", "-safe", "0", "-i", concat_list,
                    "-c:v", "libx264", "-preset", "fast",
                    "-y", output_file
                ]
            
            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
            
            # Cleanup
            import shutil
            shutil.rmtree(temp_dir)
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Error in simple concatenation: {e}")
            return False


@app.task(name="video_generation.validate_story")
def validate_story_file(story_file: str) -> dict:
    """Validate story file before processing"""
    # TODO: Implement validation
    return {"valid": True, "warnings": []}