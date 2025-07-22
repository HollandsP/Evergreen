"""
Visual Generation Service

Handles visual content generation using Runway API and fallback mechanisms.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional

import structlog

from .runway_service import RunwayService
from ..utils.file_manager import FileManager

logger = structlog.get_logger()


class VisualGenerationService:
    """Service for generating visual content from script descriptions."""
    
    def __init__(self):
        """Initialize visual generation service."""
        self.runway_service = RunwayService()
        self.file_manager = FileManager()
        
        # Active generation jobs for cancellation
        self.active_jobs: Dict[str, List[asyncio.Task]] = {}
        
        logger.info("Visual generation service initialized")
    
    async def generate_scenes(self, parsed_script: Dict[str, Any],
                            settings: Dict[str, Any]) -> List[str]:
        """
        Generate visual scenes from parsed script.
        
        Args:
            parsed_script: Parsed script data
            settings: Generation settings
            
        Returns:
            List of generated visual asset file paths
        """
        job_id = settings.get('job_id', 'unknown')
        style = settings.get('style', 'cinematic')
        
        logger.info(
            "Starting visual scene generation",
            job_id=job_id,
            scenes=len(parsed_script.get('scenes', [])),
            style=style
        )
        
        visual_assets = []
        generation_tasks = []
        
        try:
            # Process each scene's visual descriptions
            for scene_idx, scene in enumerate(parsed_script.get('scenes', [])):
                scene_duration = self._calculate_scene_duration(
                    scene, scene_idx, parsed_script
                )
                
                for visual_idx, visual_desc in enumerate(scene.get('visual_descriptions', [])):
                    if visual_desc.strip():
                        task = self._generate_scene_visual(
                            job_id=job_id,
                            scene=scene,
                            visual_description=visual_desc,
                            visual_index=visual_idx,
                            duration=scene_duration,
                            style=style
                        )
                        generation_tasks.append(task)
            
            # Track active tasks for cancellation
            self.active_jobs[job_id] = generation_tasks
            
            # Execute all visual generation tasks with concurrency limit
            semaphore = asyncio.Semaphore(2)  # Limit concurrent generations
            
            async def _bounded_generation(task):
                async with semaphore:
                    return await task
            
            # Execute tasks and collect results
            results = await asyncio.gather(
                *[_bounded_generation(task) for task in generation_tasks],
                return_exceptions=True
            )
            
            # Process results
            successful_assets = []
            for result in results:
                if isinstance(result, Exception):
                    logger.warning(
                        "Visual generation failed for scene",
                        job_id=job_id,
                        error=str(result)
                    )
                elif result:  # Valid file path
                    successful_assets.append(result)
            
            visual_assets = successful_assets
            
            logger.info(
                "Visual generation completed",
                job_id=job_id,
                total_requested=len(generation_tasks),
                successful=len(visual_assets),
                failed=len(generation_tasks) - len(visual_assets)
            )
            
            return visual_assets
            
        except Exception as e:
            logger.error(
                "Visual generation pipeline failed",
                job_id=job_id,
                error=str(e),
                exc_info=True
            )
            # Fall back to placeholders
            return await self.generate_placeholders(parsed_script, job_id)
        
        finally:
            # Clean up job tracking
            if job_id in self.active_jobs:
                del self.active_jobs[job_id]
    
    async def _generate_scene_visual(self, job_id: str, scene: Dict[str, Any],
                                   visual_description: str, visual_index: int,
                                   duration: float, style: str) -> Optional[str]:
        """
        Generate visual content for a single scene.
        
        Args:
            job_id: Job identifier
            scene: Scene data
            visual_description: Visual description text
            visual_index: Index of visual in scene
            duration: Scene duration
            style: Visual style
            
        Returns:
            Path to generated visual file or None if failed
        """
        try:
            timestamp_clean = scene['timestamp'].replace(':', '_')
            
            logger.debug(
                "Generating scene visual",
                job_id=job_id,
                timestamp=scene['timestamp'],
                visual_index=visual_index,
                description_length=len(visual_description),
                duration=duration
            )
            
            # Generate video using Runway service
            visual_file = await self.runway_service.generate_video(
                prompt=visual_description,
                duration=min(duration, 16.0),  # Runway limit
                resolution="1920x1080",
                fps=24,
                style=style,
                job_id=f"{job_id}_visual_{timestamp_clean}_{visual_index}"
            )
            
            if visual_file:
                logger.debug(
                    "Scene visual generated successfully",
                    job_id=job_id,
                    timestamp=scene['timestamp'],
                    visual_file=visual_file
                )
                return visual_file
            else:
                raise Exception("No visual file returned from Runway service")
                
        except Exception as e:
            logger.error(
                "Failed to generate scene visual",
                job_id=job_id,
                timestamp=scene.get('timestamp'),
                visual_index=visual_index,
                error=str(e)
            )
            return None
    
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
        
        # Ensure reasonable bounds
        duration = max(3.0, min(duration, 30.0))  # 3-30 seconds
        return duration
    
    async def generate_placeholders(self, parsed_script: Dict[str, Any],
                                  job_id: str) -> List[str]:
        """
        Generate placeholder visual assets for fallback.
        
        Args:
            parsed_script: Parsed script data
            job_id: Job identifier
            
        Returns:
            List of placeholder file paths
        """
        logger.info("Generating placeholder visuals", job_id=job_id)
        
        placeholder_files = []
        
        try:
            for scene in parsed_script.get('scenes', []):
                for visual_idx, visual_desc in enumerate(scene.get('visual_descriptions', [])):
                    if visual_desc.strip():
                        timestamp_clean = scene['timestamp'].replace(':', '_')
                        filename = f"{job_id}_placeholder_{timestamp_clean}_{visual_idx}.mp4"
                        
                        # Create simple placeholder data
                        placeholder_data = f"PLACEHOLDER_VISUAL:{visual_desc[:100]}".encode('utf-8')
                        
                        file_path = await self.file_manager.save_video_file(
                            filename, placeholder_data
                        )
                        placeholder_files.append(file_path)
                        
                        logger.debug(
                            "Placeholder visual created",
                            job_id=job_id,
                            file_path=file_path,
                            description_preview=visual_desc[:50] + "..."
                        )
            
            return placeholder_files
            
        except Exception as e:
            logger.error(
                "Failed to generate placeholder visuals",
                job_id=job_id,
                error=str(e)
            )
            return []
    
    async def cancel_generation(self, job_id: str) -> bool:
        """
        Cancel active visual generation for a job.
        
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
        
        # Cancel any Runway jobs
        await self.runway_service.cancel_generation(job_id)
        
        del self.active_jobs[job_id]
        
        logger.info("Visual generation cancelled", job_id=job_id)
        return True
    
    def get_available_styles(self) -> Dict[str, str]:
        """Get available visual styles."""
        return self.runway_service.get_available_styles()
    
    def health_check(self) -> Dict[str, Any]:
        """Return service health status."""
        runway_health = self.runway_service.health_check()
        
        return {
            "status": runway_health.get("status", "unknown"),
            "service": "visual_generation",
            "runway_status": runway_health.get("status"),
            "active_jobs": len(self.active_jobs),
            "total_active_tasks": sum(len(tasks) for tasks in self.active_jobs.values())
        }