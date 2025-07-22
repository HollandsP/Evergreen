"""
Video Generation Orchestrator Service

Coordinates the video generation pipeline with proper error handling,
resource management, and separation of concerns.
"""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional, Union
from contextlib import asynccontextmanager

import structlog

from .script_parser_service import ScriptParserService
from .voice_generation_service import VoiceGenerationService
from .visual_generation_service import VisualGenerationService
from .terminal_ui_service import TerminalUIService
from .video_assembly_service import VideoAssemblyService
from .health_monitor import ServiceHealthMonitor
from .circuit_breaker import CircuitBreaker
from ..utils.retry_handler import RetryHandler
from ..utils.resource_manager import ResourceManager

logger = structlog.get_logger()


class GenerationStage(Enum):
    """Video generation pipeline stages."""
    PARSING = "parsing"
    VOICE_GENERATION = "voice_generation"
    VISUAL_GENERATION = "visual_generation"
    UI_GENERATION = "ui_generation"
    ASSEMBLY = "assembly"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class GenerationJob:
    """Video generation job state."""
    job_id: str
    script_content: str
    settings: Dict[str, Any]
    stage: GenerationStage = GenerationStage.PARSING
    progress: float = 0.0
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    
    # Pipeline artifacts
    parsed_script: Optional[Dict[str, Any]] = None
    voice_files: List[str] = field(default_factory=list)
    visual_assets: List[str] = field(default_factory=list)
    ui_elements: List[str] = field(default_factory=list)
    output_file: Optional[str] = None
    
    # Error tracking
    errors: List[Dict[str, Any]] = field(default_factory=list)
    retry_count: int = 0
    
    def update_progress(self, stage: GenerationStage, progress: float):
        """Update job progress and stage."""
        self.stage = stage
        self.progress = progress
        self.updated_at = time.time()
    
    def add_error(self, stage: str, error: str, details: Optional[Dict] = None):
        """Add error to job tracking."""
        self.errors.append({
            'stage': stage,
            'error': error,
            'details': details or {},
            'timestamp': time.time()
        })


class VideoGenerationOrchestrator:
    """
    Orchestrates the video generation pipeline with comprehensive error handling,
    monitoring, and resource management.
    """
    
    def __init__(self):
        """Initialize the orchestrator with all required services."""
        self.jobs: Dict[str, GenerationJob] = {}
        
        # Initialize services
        self.script_parser = ScriptParserService()
        self.voice_service = VoiceGenerationService()
        self.visual_service = VisualGenerationService()
        self.ui_service = TerminalUIService()
        self.assembly_service = VideoAssemblyService()
        
        # Monitoring and reliability
        self.health_monitor = ServiceHealthMonitor()
        self.resource_manager = ResourceManager()
        self.retry_handler = RetryHandler()
        
        # Circuit breakers for external services
        self.voice_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            expected_exception=Exception
        )
        self.visual_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=120,
            expected_exception=Exception
        )
        
        logger.info("Video generation orchestrator initialized")
    
    async def generate_video(self, job_id: str, script_content: str, 
                           settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main video generation pipeline with comprehensive error handling.
        
        Args:
            job_id: Unique job identifier
            script_content: Script content to process
            settings: Generation settings
            
        Returns:
            Generation result with job status and artifacts
        """
        job = GenerationJob(job_id, script_content, settings)
        self.jobs[job_id] = job
        
        logger.info("Starting video generation", job_id=job_id)
        
        try:
            async with self.resource_manager.acquire_resources(
                memory_mb=2048, 
                cpu_cores=2
            ):
                # Stage 1: Parse script
                await self._parse_script(job)
                
                # Stage 2: Generate voice narration (with circuit breaker)
                await self._generate_voice_with_protection(job)
                
                # Stage 3: Generate visual content (with circuit breaker)
                await self._generate_visuals_with_protection(job)
                
                # Stage 4: Create terminal UI elements
                await self._generate_ui_elements(job)
                
                # Stage 5: Assemble final video
                await self._assemble_video(job)
                
                job.update_progress(GenerationStage.COMPLETED, 100.0)
                
                result = {
                    'job_id': job_id,
                    'status': 'completed',
                    'output_file': job.output_file,
                    'duration': job.parsed_script.get('total_duration', 0) if job.parsed_script else 0,
                    'assets_generated': {
                        'voice_files': len(job.voice_files),
                        'visual_assets': len(job.visual_assets),
                        'ui_elements': len(job.ui_elements)
                    },
                    'processing_time': time.time() - job.created_at
                }
                
                logger.info("Video generation completed successfully", result=result)
                return result
                
        except Exception as e:
            await self._handle_generation_error(job, e)
            raise
        
        finally:
            # Cleanup resources
            await self._cleanup_job_resources(job)
    
    async def _parse_script(self, job: GenerationJob):
        """Parse script content with error handling."""
        job.update_progress(GenerationStage.PARSING, 10.0)
        
        try:
            logger.info("Parsing script content", job_id=job.job_id)
            
            job.parsed_script = await self.retry_handler.execute_with_retry(
                self.script_parser.parse_script,
                job.script_content,
                max_retries=2,
                backoff_factor=1.0
            )
            
            job.update_progress(GenerationStage.PARSING, 20.0)
            
            logger.info(
                "Script parsed successfully",
                job_id=job.job_id,
                scenes=job.parsed_script.get('scene_count', 0),
                duration=job.parsed_script.get('total_duration', 0)
            )
            
        except Exception as e:
            job.add_error('parsing', str(e))
            logger.error("Script parsing failed", job_id=job.job_id, error=str(e))
            raise
    
    async def _generate_voice_with_protection(self, job: GenerationJob):
        """Generate voice narration with circuit breaker protection."""
        job.update_progress(GenerationStage.VOICE_GENERATION, 25.0)
        
        try:
            logger.info("Generating voice narration", job_id=job.job_id)
            
            async def _voice_generation():
                return await self.voice_service.generate_narration(
                    job.parsed_script,
                    job.settings
                )
            
            job.voice_files = await self.voice_breaker.call(_voice_generation)
            job.update_progress(GenerationStage.VOICE_GENERATION, 40.0)
            
            logger.info(
                "Voice generation completed",
                job_id=job.job_id,
                files_generated=len(job.voice_files)
            )
            
        except Exception as e:
            job.add_error('voice_generation', str(e))
            logger.error("Voice generation failed", job_id=job.job_id, error=str(e))
            
            # Continue with mock voice files for demo purposes
            job.voice_files = await self.voice_service.generate_mock_files(
                job.parsed_script,
                job.job_id
            )
            logger.warning("Continuing with mock voice files", job_id=job.job_id)
    
    async def _generate_visuals_with_protection(self, job: GenerationJob):
        """Generate visual content with circuit breaker protection."""
        job.update_progress(GenerationStage.VISUAL_GENERATION, 45.0)
        
        try:
            logger.info("Generating visual content", job_id=job.job_id)
            
            async def _visual_generation():
                return await self.visual_service.generate_scenes(
                    job.parsed_script,
                    job.settings
                )
            
            job.visual_assets = await self.visual_breaker.call(_visual_generation)
            job.update_progress(GenerationStage.VISUAL_GENERATION, 70.0)
            
            logger.info(
                "Visual generation completed",
                job_id=job.job_id,
                assets_generated=len(job.visual_assets)
            )
            
        except Exception as e:
            job.add_error('visual_generation', str(e))
            logger.error("Visual generation failed", job_id=job.job_id, error=str(e))
            
            # Continue with placeholder visuals
            job.visual_assets = await self.visual_service.generate_placeholders(
                job.parsed_script,
                job.job_id
            )
            logger.warning("Continuing with placeholder visuals", job_id=job.job_id)
    
    async def _generate_ui_elements(self, job: GenerationJob):
        """Generate terminal UI elements."""
        job.update_progress(GenerationStage.UI_GENERATION, 75.0)
        
        try:
            logger.info("Generating UI elements", job_id=job.job_id)
            
            job.ui_elements = await self.retry_handler.execute_with_retry(
                self.ui_service.generate_animations,
                job.parsed_script,
                job.settings,
                max_retries=2,
                backoff_factor=1.0
            )
            
            job.update_progress(GenerationStage.UI_GENERATION, 85.0)
            
            logger.info(
                "UI generation completed",
                job_id=job.job_id,
                elements_generated=len(job.ui_elements)
            )
            
        except Exception as e:
            job.add_error('ui_generation', str(e))
            logger.error("UI generation failed", job_id=job.job_id, error=str(e))
            
            # Continue with empty UI elements
            job.ui_elements = []
            logger.warning("Continuing without UI elements", job_id=job.job_id)
    
    async def _assemble_video(self, job: GenerationJob):
        """Assemble final video from all components."""
        job.update_progress(GenerationStage.ASSEMBLY, 90.0)
        
        try:
            logger.info("Assembling final video", job_id=job.job_id)
            
            job.output_file = await self.retry_handler.execute_with_retry(
                self.assembly_service.assemble_video,
                job.job_id,
                job.parsed_script,
                job.voice_files,
                job.ui_elements,
                job.visual_assets,
                job.settings,
                max_retries=2,
                backoff_factor=2.0
            )
            
            job.update_progress(GenerationStage.ASSEMBLY, 95.0)
            
            logger.info(
                "Video assembly completed",
                job_id=job.job_id,
                output_file=job.output_file
            )
            
        except Exception as e:
            job.add_error('assembly', str(e))
            logger.error("Video assembly failed", job_id=job.job_id, error=str(e))
            raise
    
    async def _handle_generation_error(self, job: GenerationJob, error: Exception):
        """Handle generation errors with appropriate logging and cleanup."""
        job.update_progress(GenerationStage.FAILED, job.progress)
        job.add_error('orchestrator', str(error))
        
        logger.error(
            "Video generation failed",
            job_id=job.job_id,
            stage=job.stage.value,
            error=str(error),
            errors=job.errors,
            exc_info=True
        )
        
        # Record metrics for monitoring
        self.health_monitor.record_failure(job.stage.value, str(error))
    
    async def _cleanup_job_resources(self, job: GenerationJob):
        """Clean up temporary resources for completed job."""
        try:
            # Cleanup temporary files if configured
            cleanup_temp = job.settings.get('cleanup_temp_files', False)
            if cleanup_temp:
                temp_files = []
                temp_files.extend(job.voice_files)
                temp_files.extend(job.visual_assets)
                temp_files.extend(job.ui_elements)
                
                for file_path in temp_files:
                    try:
                        if file_path and file_path.startswith('/tmp'):
                            import os
                            if os.path.exists(file_path):
                                os.unlink(file_path)
                    except Exception as e:
                        logger.warning(
                            "Failed to cleanup temp file",
                            file_path=file_path,
                            error=str(e)
                        )
                        
            logger.debug("Job cleanup completed", job_id=job.job_id)
            
        except Exception as e:
            logger.warning("Job cleanup failed", job_id=job.job_id, error=str(e))
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get current job status and progress."""
        job = self.jobs.get(job_id)
        if not job:
            return None
        
        return {
            'job_id': job_id,
            'stage': job.stage.value,
            'progress': job.progress,
            'created_at': job.created_at,
            'updated_at': job.updated_at,
            'errors': job.errors,
            'retry_count': job.retry_count,
            'assets': {
                'voice_files': len(job.voice_files),
                'visual_assets': len(job.visual_assets),
                'ui_elements': len(job.ui_elements),
                'output_file': job.output_file
            }
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall service health status."""
        return {
            'status': 'healthy',  # TODO: Implement actual health checks
            'services': {
                'script_parser': self.script_parser.health_check(),
                'voice_service': self.voice_service.health_check(),
                'visual_service': self.visual_service.health_check(),
                'ui_service': self.ui_service.health_check(),
                'assembly_service': self.assembly_service.health_check()
            },
            'circuit_breakers': {
                'voice_breaker': {
                    'state': self.voice_breaker.state.value,
                    'failure_count': self.voice_breaker.failure_count
                },
                'visual_breaker': {
                    'state': self.visual_breaker.state.value,
                    'failure_count': self.visual_breaker.failure_count
                }
            },
            'resource_usage': self.resource_manager.get_usage_stats()
        }
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job and cleanup resources."""
        job = self.jobs.get(job_id)
        if not job:
            return False
        
        logger.info("Cancelling job", job_id=job_id)
        
        try:
            # Stop any running processes
            await self.voice_service.cancel_generation(job_id)
            await self.visual_service.cancel_generation(job_id)
            await self.ui_service.cancel_generation(job_id)
            
            # Update job status
            job.update_progress(GenerationStage.FAILED, job.progress)
            job.add_error('orchestrator', 'Job cancelled by user')
            
            # Cleanup resources
            await self._cleanup_job_resources(job)
            
            return True
            
        except Exception as e:
            logger.error("Failed to cancel job", job_id=job_id, error=str(e))
            return False