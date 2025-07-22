"""
Runway Service

Simplified Runway API client with proper error handling, resource management,
and fallback mechanisms.
"""

import os
import asyncio
import logging
import tempfile
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass

import structlog

from .ffmpeg_service import FFmpegService
from ..utils.file_manager import FileManager
from ..utils.runway_api_client import RunwayAPIClient

logger = structlog.get_logger()


@dataclass
class GenerationJob:
    """Runway generation job tracking."""
    job_id: str
    runway_id: Optional[str] = None
    prompt: str = ""
    duration: float = 5.0
    status: str = "pending"
    progress: float = 0.0
    video_url: Optional[str] = None
    error: Optional[str] = None
    created_at: float = 0.0


class RunwayService:
    """Service for generating video content using Runway API with fallbacks."""
    
    def __init__(self):
        """Initialize Runway service."""
        self.api_key = os.environ.get("RUNWAY_API_KEY")
        self.api_client = RunwayAPIClient(self.api_key) if self.api_key else None
        self.ffmpeg_service = FFmpegService()
        self.file_manager = FileManager()
        
        # Job tracking
        self.active_jobs: Dict[str, GenerationJob] = {}
        
        # Style configuration
        self.style_prompts = {
            "techwear": "cyberpunk aesthetic, neon accents, urban environment, high-tech fashion, cinematic lighting",
            "minimalist": "clean aesthetic, simple composition, minimal design, soft lighting", 
            "vintage": "retro aesthetic, film grain, nostalgic mood, warm tones",
            "futuristic": "sci-fi aesthetic, holographic elements, advanced technology, dramatic lighting",
            "cinematic": "cinematic quality, professional lighting, depth of field, atmospheric"
        }
        
        # Cinematic mode configuration
        self.cinematic_mode = os.environ.get('RUNWAY_CINEMATIC_MODE', 'true').lower() == 'true'
        
        logger.info(
            "Runway service initialized",
            has_api_key=bool(self.api_key),
            cinematic_mode=self.cinematic_mode,
            available_styles=len(self.style_prompts)
        )
    
    async def generate_video(self, prompt: str, duration: float = 5.0,
                           resolution: str = "1920x1080", fps: int = 24,
                           style: str = "cinematic", **kwargs) -> str:
        """
        Generate video from text prompt.
        
        Args:
            prompt: Text description
            duration: Video duration in seconds
            resolution: Video resolution
            fps: Frames per second
            style: Visual style
            **kwargs: Additional parameters
            
        Returns:
            Path to generated video file
        """
        job_id = kwargs.get('job_id', f"video_{hash(prompt) % 10000}")
        
        logger.info(
            "Starting video generation",
            job_id=job_id,
            prompt=prompt[:100],
            duration=duration,
            style=style
        )
        
        job = GenerationJob(
            job_id=job_id,
            prompt=prompt,
            duration=duration,
            created_at=asyncio.get_event_loop().time()
        )
        self.active_jobs[job_id] = job
        
        try:
            if self.api_client:
                # Try real API first
                video_file = await self._generate_with_api(job, resolution, fps, style)
            else:
                # Use enhanced placeholder generation
                video_file = await self._generate_placeholder(job, resolution, fps, style)
            
            job.status = "completed"
            job.progress = 100.0
            
            logger.info(
                "Video generation completed",
                job_id=job_id,
                video_file=video_file
            )
            
            return video_file
            
        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            
            logger.error(
                "Video generation failed",
                job_id=job_id,
                error=str(e)
            )
            
            # Fall back to basic placeholder
            return await self._generate_basic_placeholder(job)
        
        finally:
            # Keep job for status queries but mark as finished
            pass
    
    async def _generate_with_api(self, job: GenerationJob, resolution: str, 
                               fps: int, style: str) -> str:
        """Generate video using actual Runway API."""
        try:
            # Enhance prompt with style
            enhanced_prompt = self._enhance_prompt(job.prompt, style)
            
            # Submit generation request
            runway_job = await self.api_client.submit_generation(
                prompt=enhanced_prompt,
                duration=min(job.duration, 16.0),  # Runway limit
                resolution=resolution,
                fps=fps
            )
            
            job.runway_id = runway_job['id']
            job.status = "processing"
            
            logger.info(
                "Runway job submitted",
                job_id=job.job_id,
                runway_id=job.runway_id
            )
            
            # Poll for completion
            video_data = await self._poll_runway_completion(job)
            
            if not video_data:
                raise Exception("Failed to retrieve video from Runway")
            
            # Save video file
            filename = f"{job.job_id}_runway.mp4"
            return await self.file_manager.save_video_file(filename, video_data)
            
        except Exception as e:
            logger.warning(
                "Runway API generation failed, falling back to placeholder",
                job_id=job.job_id,
                error=str(e)
            )
            return await self._generate_placeholder(job, resolution, fps, style)
    
    async def _poll_runway_completion(self, job: GenerationJob, 
                                    timeout: float = 300.0) -> Optional[bytes]:
        """Poll Runway API for job completion."""
        start_time = asyncio.get_event_loop().time()
        poll_interval = 5.0  # Poll every 5 seconds
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            try:
                status = await self.api_client.get_job_status(job.runway_id)
                
                job.status = status.get('status', 'processing')
                job.progress = status.get('progress', job.progress)
                
                logger.debug(
                    "Runway job status",
                    job_id=job.job_id,
                    runway_id=job.runway_id,
                    status=job.status,
                    progress=job.progress
                )
                
                if job.status == 'completed':
                    video_url = status.get('video_url')
                    if video_url:
                        return await self.api_client.download_video(video_url)
                    else:
                        raise Exception("No video URL in completion response")
                
                elif job.status == 'failed':
                    job.error = status.get('error', 'Unknown error')
                    raise Exception(f"Runway generation failed: {job.error}")
                
                # Wait before next poll
                await asyncio.sleep(poll_interval)
                
            except Exception as e:
                logger.error(
                    "Error polling Runway status",
                    job_id=job.job_id,
                    runway_id=job.runway_id,
                    error=str(e)
                )
                break
        
        # Timeout or error
        job.error = "Generation timeout or polling error"
        return None
    
    async def _generate_placeholder(self, job: GenerationJob, resolution: str, 
                                  fps: int, style: str) -> str:
        """Generate enhanced placeholder video."""
        logger.info(
            "Generating enhanced placeholder video",
            job_id=job.job_id,
            cinematic_mode=self.cinematic_mode
        )
        
        try:
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
                output_path = temp_file.name
            
            if self.cinematic_mode:
                success = await self._generate_cinematic_placeholder(
                    job, output_path, resolution, fps
                )
            else:
                success = await self._generate_basic_visual_placeholder(
                    job, output_path, resolution, fps
                )
            
            if success and os.path.exists(output_path):
                # Save to permanent location
                filename = f"{job.job_id}_placeholder.mp4"
                final_path = await self.file_manager.save_video_file_from_temp(
                    filename, output_path
                )
                
                # Cleanup temp file
                try:
                    os.unlink(output_path)
                except:
                    pass
                
                return final_path
            else:
                raise Exception("Failed to generate placeholder video")
                
        except Exception as e:
            logger.error(
                "Placeholder generation failed",
                job_id=job.job_id,
                error=str(e)
            )
            return await self._generate_basic_placeholder(job)
    
    async def _generate_cinematic_placeholder(self, job: GenerationJob, 
                                            output_path: str, resolution: str, 
                                            fps: int) -> bool:
        """Generate cinematic quality placeholder using scene-specific filters."""
        from .runway_client_cinematic import CinematicVisualGenerator
        
        try:
            # Determine scene type and generate appropriate filter
            prompt = job.prompt.lower()
            
            if 'rooftop' in prompt or 'bodies' in prompt:
                filter_complex = CinematicVisualGenerator.generate_rooftop_scene(job.duration)
            elif 'concrete' in prompt or 'message' in prompt:
                filter_complex = CinematicVisualGenerator.generate_concrete_message_scene(job.duration)
            elif 'server' in prompt or 'screens' in prompt:
                filter_complex = CinematicVisualGenerator.generate_server_room_scene(job.duration)
            elif 'control' in prompt or 'operators' in prompt:
                filter_complex = CinematicVisualGenerator.generate_control_room_scene(job.duration)
            else:
                # Generic cinematic scene
                filter_complex = self._generate_generic_cinematic_filter(job.duration, prompt)
            
            # Apply filter using FFmpeg
            return CinematicVisualGenerator.apply_filter_complex(
                filter_complex, job.duration, output_path
            )
            
        except Exception as e:
            logger.error("Cinematic generation failed", error=str(e))
            return False
    
    async def _generate_basic_visual_placeholder(self, job: GenerationJob,
                                               output_path: str, resolution: str,
                                               fps: int) -> bool:
        """Generate basic visual placeholder."""
        try:
            # Simple gradient background with text overlay
            filter_str = f"""
            color=c=0x1a1a1a:s={resolution}:d={job.duration}[bg];
            [bg]drawtext=text='{job.prompt[:50]}...':
                fontcolor=white:fontsize=24:x=(W-tw)/2:y=(H-th)/2[out]
            """
            
            cmd = [
                'ffmpeg', '-y',
                '-f', 'lavfi',
                '-i', f'nullsrc=s={resolution}:d={job.duration}',
                '-filter_complex', filter_str,
                '-map', '[out]',
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-pix_fmt', 'yuv420p',
                '-r', str(fps),
                output_path
            ]
            
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error("Basic placeholder generation failed", error=str(e))
            return False
    
    def _generate_generic_cinematic_filter(self, duration: float, prompt: str) -> str:
        """Generate generic cinematic filter based on prompt keywords."""
        if any(word in prompt for word in ['city', 'urban', 'building']):
            # Urban scene
            return f"""
            color=c=0x0a0a1a:s=1920x1080:d={duration}[bg];
            [bg]drawbox=x=0:y=600:w=1920:h=480:color=0x1a1a1a:t=fill,
            drawbox=x=100:y=500:w=200:h=300:color=0x2a2a2a:t=fill,
            drawbox=x=350:y=550:w=150:h=250:color=0x252525:t=fill,
            curves=preset=darker,vignette=a=0.7[out]
            """
        else:
            # Generic atmospheric scene
            return f"""
            color=c=0x1a1a1a:s=1920x1080:d={duration}[bg];
            [bg]noise=alls=8:allf=t,
            curves=preset=darker,vignette=a=0.6[out]
            """
    
    async def _generate_basic_placeholder(self, job: GenerationJob) -> str:
        """Generate basic placeholder as last resort."""
        logger.warning("Using basic placeholder", job_id=job.job_id)
        
        # Create minimal placeholder file
        filename = f"{job.job_id}_basic.mp4"
        placeholder_data = b"BASIC_VIDEO_PLACEHOLDER_" + job.prompt.encode('utf-8')[:100]
        
        return await self.file_manager.save_video_file(filename, placeholder_data)
    
    def _enhance_prompt(self, prompt: str, style: str) -> str:
        """Enhance prompt with style modifiers."""
        style_enhancement = self.style_prompts.get(style, self.style_prompts["cinematic"])
        return f"{prompt}, {style_enhancement}, professional quality"
    
    async def cancel_generation(self, job_id: str) -> bool:
        """Cancel active generation job."""
        job = self.active_jobs.get(job_id)
        if not job:
            return False
        
        if job.runway_id and self.api_client:
            try:
                await self.api_client.cancel_job(job.runway_id)
            except Exception as e:
                logger.warning(
                    "Failed to cancel Runway job",
                    job_id=job_id,
                    runway_id=job.runway_id,
                    error=str(e)
                )
        
        job.status = "cancelled"
        logger.info("Video generation cancelled", job_id=job_id)
        return True
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get generation job status."""
        job = self.active_jobs.get(job_id)
        if not job:
            return None
        
        return {
            'job_id': job.job_id,
            'runway_id': job.runway_id,
            'status': job.status,
            'progress': job.progress,
            'prompt': job.prompt,
            'duration': job.duration,
            'error': job.error,
            'created_at': job.created_at
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Return service health status."""
        return {
            "status": "healthy" if self.api_client else "degraded",
            "service": "runway",
            "api_available": bool(self.api_client),
            "cinematic_mode": self.cinematic_mode,
            "active_jobs": len(self.active_jobs),
            "ffmpeg_available": bool(self.ffmpeg_service.ffmpeg_path)
        }
    
    def get_available_styles(self) -> Dict[str, str]:
        """Get available visual styles."""
        return {k: f"Style: {v}" for k, v in self.style_prompts.items()}