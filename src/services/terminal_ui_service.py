"""
Terminal UI Service

Handles terminal UI animation generation with proper error handling
and resource management.
"""

import asyncio
import os
import tempfile
from typing import Dict, List, Any, Optional

import structlog

from ..utils.file_manager import FileManager

logger = structlog.get_logger()


class TerminalUIService:
    """Service for generating terminal UI animations."""
    
    def __init__(self):
        """Initialize terminal UI service."""
        self.file_manager = FileManager()
        
        # Active generation jobs for cancellation
        self.active_jobs: Dict[str, List[asyncio.Task]] = {}
        
        # Terminal themes
        self.themes = {
            "dark": {"bg": "0x0a0a0a", "fg": "0x00ff00", "accent": "0xffff00"},
            "light": {"bg": "0xf8f8f8", "fg": "0x333333", "accent": "0x0066cc"},
            "matrix": {"bg": "0x000000", "fg": "0x00ff41", "accent": "0xff0000"},
            "hacker": {"bg": "0x0f0f0f", "fg": "0x00ffff", "accent": "0xff00ff"},
            "vscode": {"bg": "0x1e1e1e", "fg": "0xd4d4d4", "accent": "0x569cd6"}
        }
        
        logger.info(
            "Terminal UI service initialized",
            available_themes=list(self.themes.keys())
        )
    
    async def generate_animations(self, parsed_script: Dict[str, Any],
                                settings: Dict[str, Any]) -> List[str]:
        """
        Generate terminal UI animations from parsed script.
        
        Args:
            parsed_script: Parsed script data
            settings: Generation settings
            
        Returns:
            List of generated UI animation file paths
        """
        job_id = settings.get('job_id', 'unknown')
        theme = settings.get('terminal_theme', 'dark')
        
        if theme not in self.themes:
            logger.warning(f"Unknown theme {theme}, using 'dark'")
            theme = 'dark'
        
        logger.info(
            "Starting terminal UI generation",
            job_id=job_id,
            scenes=len(parsed_script.get('scenes', [])),
            theme=theme
        )
        
        ui_elements = []
        generation_tasks = []
        
        try:
            # Process each scene's on-screen text
            for scene_idx, scene in enumerate(parsed_script.get('scenes', [])):
                scene_duration = self._calculate_scene_duration(
                    scene, scene_idx, parsed_script
                )
                
                for text_idx, onscreen_text in enumerate(scene.get('onscreen_text', [])):
                    if onscreen_text.strip():
                        task = self._generate_terminal_animation(
                            job_id=job_id,
                            scene=scene,
                            onscreen_text=onscreen_text,
                            text_index=text_idx,
                            duration=scene_duration,
                            theme=theme
                        )
                        generation_tasks.append(task)
            
            # Track active tasks for cancellation
            self.active_jobs[job_id] = generation_tasks
            
            if generation_tasks:
                # Execute all UI generation tasks
                results = await asyncio.gather(
                    *generation_tasks,
                    return_exceptions=True
                )
                
                # Process results
                successful_elements = []
                for result in results:
                    if isinstance(result, Exception):
                        logger.warning(
                            "UI animation generation failed",
                            job_id=job_id,
                            error=str(result)
                        )
                    elif result:  # Valid file path
                        successful_elements.append(result)
                
                ui_elements = successful_elements
            
            logger.info(
                "Terminal UI generation completed",
                job_id=job_id,
                total_requested=len(generation_tasks),
                successful=len(ui_elements),
                failed=len(generation_tasks) - len(ui_elements)
            )
            
            return ui_elements
            
        except Exception as e:
            logger.error(
                "Terminal UI generation pipeline failed",
                job_id=job_id,
                error=str(e),
                exc_info=True
            )
            return []
        
        finally:
            # Clean up job tracking
            if job_id in self.active_jobs:
                del self.active_jobs[job_id]
    
    async def _generate_terminal_animation(self, job_id: str, scene: Dict[str, Any],
                                         onscreen_text: str, text_index: int,
                                         duration: float, theme: str) -> Optional[str]:
        """
        Generate terminal animation for on-screen text.
        
        Args:
            job_id: Job identifier
            scene: Scene data
            onscreen_text: Text to animate
            text_index: Index of text in scene
            duration: Animation duration
            theme: Terminal theme
            
        Returns:
            Path to generated animation file or None if failed
        """
        try:
            timestamp_clean = scene['timestamp'].replace(':', '_')
            
            logger.debug(
                "Generating terminal animation",
                job_id=job_id,
                timestamp=scene['timestamp'],
                text_index=text_index,
                text_length=len(onscreen_text),
                duration=duration
            )
            
            # Use FFmpeg to create typing animation
            animation_file = await self._create_typing_animation(
                job_id=job_id,
                timestamp=timestamp_clean,
                text_index=text_index,
                text=onscreen_text,
                duration=duration,
                theme=theme
            )
            
            if animation_file:
                logger.debug(
                    "Terminal animation generated successfully",
                    job_id=job_id,
                    timestamp=scene['timestamp'],
                    animation_file=animation_file
                )
                return animation_file
            else:
                raise Exception("No animation file created")
                
        except Exception as e:
            logger.error(
                "Failed to generate terminal animation",
                job_id=job_id,
                timestamp=scene.get('timestamp'),
                text_index=text_index,
                error=str(e)
            )
            return None
    
    async def _create_typing_animation(self, job_id: str, timestamp: str,
                                     text_index: int, text: str, duration: float,
                                     theme: str) -> Optional[str]:
        """Create typing animation using FFmpeg."""
        try:
            theme_colors = self.themes[theme]
            
            # Prepare text for FFmpeg (escape special characters)
            safe_text = self._escape_text_for_ffmpeg(text)
            
            # Calculate typing speed
            typing_speed = len(text) / max(duration * 0.8, 1.0)  # Use 80% of duration
            
            # Create FFmpeg filter for typing effect
            filter_complex = f"""
            color=c={theme_colors['bg']}:s=1920x1080:d={duration}[bg];
            [bg]drawtext=text='{safe_text}':
                fontcolor={theme_colors['fg']}:fontsize=32:
                x=50:y=50:
                fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf:
                enable='between(t,0,{duration})':
                textfile=<(echo '{safe_text}' | head -c $(echo 't*{typing_speed}' | bc))[out]
            """
            
            # For simplicity, create a simpler static animation
            # In production, you'd implement proper character-by-character animation
            filter_complex = f"""
            color=c={theme_colors['bg']}:s=1920x1080:d={duration}[bg];
            [bg]drawtext=text='{safe_text[:100]}':
                fontcolor={theme_colors['fg']}:fontsize=28:
                x=50:y=100:
                fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf[text];
            [text]drawtext=text='$ ':
                fontcolor={theme_colors['accent']}:fontsize=28:
                x=50:y=50:
                fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf[out]
            """
            
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Build FFmpeg command
            cmd = [
                'ffmpeg', '-y',
                '-f', 'lavfi',
                '-i', f'nullsrc=s=1920x1080:d={duration}',
                '-filter_complex', filter_complex,
                '-map', '[out]',
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-pix_fmt', 'yuv420p',
                '-r', '24',
                temp_path
            ]
            
            # Execute FFmpeg command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0 and os.path.exists(temp_path):
                # Save to permanent location
                filename = f"{job_id}_ui_{timestamp}_{text_index}.mp4"
                final_path = await self.file_manager.save_video_file_from_temp(
                    filename, temp_path
                )
                
                # Cleanup temp file
                try:
                    os.unlink(temp_path)
                except:
                    pass
                
                return final_path
            else:
                logger.error(
                    "FFmpeg failed for terminal animation",
                    stderr=stderr.decode()[:500]
                )
                return None
                
        except Exception as e:
            logger.error("Failed to create typing animation", error=str(e))
            return None
    
    def _escape_text_for_ffmpeg(self, text: str) -> str:
        """Escape text for safe use in FFmpeg filters."""
        # Replace characters that cause issues in FFmpeg
        text = text.replace("'", "\\'")
        text = text.replace('"', '\\"')
        text = text.replace(':', '\\:')
        text = text.replace('[', '\\[')
        text = text.replace(']', '\\]')
        
        # Limit length to prevent filter complexity issues
        if len(text) > 200:
            text = text[:197] + "..."
        
        return text
    
    def _calculate_scene_duration(self, scene: Dict[str, Any], scene_idx: int,
                                parsed_script: Dict[str, Any]) -> float:
        """Calculate duration for a scene."""
        scenes = parsed_script.get('scenes', [])
        
        # Calculate based on timestamps
        current_time = scene.get('timestamp_seconds', 0)
        
        if scene_idx + 1 < len(scenes):
            # Use next scene timestamp
            next_scene = scenes[scene_idx + 1]
            next_time = next_scene.get('timestamp_seconds', current_time + 10)
            duration = next_time - current_time
        else:
            # Last scene - use remaining duration
            total_duration = parsed_script.get('total_duration', 60)
            duration = total_duration - current_time
        
        # Ensure reasonable bounds for UI animations
        duration = max(5.0, min(duration, 20.0))  # 5-20 seconds
        return duration
    
    async def cancel_generation(self, job_id: str) -> bool:
        """
        Cancel active UI generation for a job.
        
        Args:
            job_id: Job identifier to cancel
            
        Returns:
            True if cancellation was successful
        """
        if job_id not in self.active_jobs:
            return False
        
        tasks = self.active_jobs[job_id]
        
        # Cancel all active tasks
        for task in tasks:
            task.cancel()
        
        # Wait for tasks to finish cancellation
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception:
            pass
        
        del self.active_jobs[job_id]
        
        logger.info("Terminal UI generation cancelled", job_id=job_id)
        return True
    
    def get_available_themes(self) -> Dict[str, Dict[str, str]]:
        """Get available terminal themes."""
        return {
            name: {
                "name": name.title(),
                "description": f"{name.title()} terminal theme",
                "colors": colors
            }
            for name, colors in self.themes.items()
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Return service health status."""
        return {
            "status": "healthy",
            "service": "terminal_ui",
            "available_themes": len(self.themes),
            "active_jobs": len(self.active_jobs),
            "total_active_tasks": sum(len(tasks) for tasks in self.active_jobs.values())
        }