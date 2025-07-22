"""
Voice Generation Service

Handles voice narration generation with ElevenLabs integration, proper error handling,
and fallback mechanisms.
"""

import os
import asyncio
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

import structlog

from ..utils.elevenlabs_client import ElevenLabsClient
from ..utils.file_manager import FileManager

logger = structlog.get_logger()


class VoiceGenerationService:
    """Service for generating voice narration from script content."""
    
    def __init__(self):
        """Initialize voice generation service."""
        self.api_key = os.environ.get("ELEVENLABS_API_KEY")
        self.client = ElevenLabsClient(self.api_key) if self.api_key else None
        self.file_manager = FileManager()
        
        # Voice mapping
        self.voice_id_map = {
            "male_calm": "21m00Tcm4TlvDq8ikWAM",
            "female_calm": "AZnzlk1XvdvUeBnXmlld", 
            "male_dramatic": "pNInz6obpgDQGcFmaJgB",
            "female_dramatic": "MF3mGyEYCl7XYWbV9V6O",
        }
        
        # Active generation jobs for cancellation
        self.active_jobs: Dict[str, asyncio.Task] = {}
        
        logger.info(
            "Voice generation service initialized",
            has_api_key=bool(self.api_key),
            available_voices=len(self.voice_id_map)
        )
    
    async def generate_narration(self, parsed_script: Dict[str, Any], 
                               settings: Dict[str, Any]) -> List[str]:
        """
        Generate voice narration from parsed script.
        
        Args:
            parsed_script: Parsed script data
            settings: Generation settings including voice type
            
        Returns:
            List of generated voice file paths
        """
        if not self.client:
            logger.warning("ElevenLabs API not available, using mock generation")
            return await self.generate_mock_files(
                parsed_script, 
                settings.get('job_id', 'unknown')
            )
        
        voice_files = []
        voice_type = settings.get("voice_type", "male_calm")
        voice_id = self.voice_id_map.get(voice_type, self.voice_id_map["male_calm"])
        
        logger.info(
            "Starting voice generation",
            voice_type=voice_type,
            voice_id=voice_id,
            scenes=len(parsed_script.get("scenes", []))
        )
        
        try:
            # Process each scene
            tasks = []
            for i, scene in enumerate(parsed_script.get("scenes", [])):
                for j, narration in enumerate(scene.get("narration", [])):
                    if narration.strip():
                        task = self._generate_voice_segment(
                            narration,
                            voice_id,
                            settings.get('job_id', 'unknown'),
                            scene['timestamp'],
                            j
                        )
                        tasks.append(task)
            
            # Generate all segments concurrently with limit
            semaphore = asyncio.Semaphore(3)  # Limit concurrent requests
            
            async def _bounded_generation(task):
                async with semaphore:
                    return await task
            
            results = await asyncio.gather(
                *[_bounded_generation(task) for task in tasks],
                return_exceptions=True
            )
            
            # Process results
            for result in results:
                if isinstance(result, Exception):
                    logger.warning("Voice segment generation failed", error=str(result))
                    continue
                elif result:  # Valid file path
                    voice_files.append(result)
            
            logger.info(
                "Voice generation completed",
                total_segments=len(tasks),
                successful_segments=len(voice_files),
                failed_segments=len(tasks) - len(voice_files)
            )
            
            return voice_files
            
        except Exception as e:
            logger.error("Voice generation failed", error=str(e), exc_info=True)
            # Fall back to mock generation
            return await self.generate_mock_files(
                parsed_script,
                settings.get('job_id', 'unknown')
            )
    
    async def _generate_voice_segment(self, text: str, voice_id: str, 
                                    job_id: str, timestamp: str, 
                                    index: int) -> Optional[str]:
        """
        Generate a single voice segment.
        
        Args:
            text: Text to convert to speech
            voice_id: ElevenLabs voice ID
            job_id: Job identifier
            timestamp: Scene timestamp
            index: Segment index
            
        Returns:
            Path to generated audio file or None if failed
        """
        try:
            logger.debug(
                "Generating voice segment",
                job_id=job_id,
                timestamp=timestamp,
                text_length=len(text)
            )
            
            # Generate audio data
            audio_data = await self.client.text_to_speech(
                text=text,
                voice_id=voice_id,
                model_id="eleven_monolingual_v1",
                voice_settings={
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                    "style": 0.0,
                    "use_speaker_boost": True
                }
            )
            
            if not audio_data:
                raise ValueError("No audio data received from ElevenLabs")
            
            # Save audio file
            timestamp_clean = timestamp.replace(':', '_')
            filename = f"{job_id}_voice_{timestamp_clean}_{index}.mp3"
            file_path = await self.file_manager.save_audio_file(filename, audio_data)
            
            logger.debug(
                "Voice segment generated",
                job_id=job_id,
                timestamp=timestamp,
                file_path=file_path,
                size_bytes=len(audio_data)
            )
            
            return file_path
            
        except Exception as e:
            logger.error(
                "Failed to generate voice segment",
                job_id=job_id,
                timestamp=timestamp,
                error=str(e)
            )
            return None
    
    async def generate_mock_files(self, parsed_script: Dict[str, Any], 
                                job_id: str) -> List[str]:
        """
        Generate mock voice files for testing/fallback.
        
        Args:
            parsed_script: Parsed script data
            job_id: Job identifier
            
        Returns:
            List of mock file paths
        """
        logger.info("Generating mock voice files", job_id=job_id)
        
        mock_files = []
        
        try:
            for scene in parsed_script.get("scenes", []):
                for j, narration in enumerate(scene.get("narration", [])):
                    if narration.strip():
                        timestamp_clean = scene['timestamp'].replace(':', '_')
                        filename = f"{job_id}_voice_mock_{timestamp_clean}_{j}.mp3"
                        
                        # Create mock audio data
                        mock_data = f"MOCK_AUDIO:{narration[:100]}".encode('utf-8')
                        
                        file_path = await self.file_manager.save_audio_file(filename, mock_data)
                        mock_files.append(file_path)
                        
                        logger.debug(
                            "Mock voice file created",
                            job_id=job_id,
                            file_path=file_path,
                            text_preview=narration[:50] + "..."
                        )
            
            return mock_files
            
        except Exception as e:
            logger.error("Failed to generate mock files", job_id=job_id, error=str(e))
            return []
    
    async def cancel_generation(self, job_id: str) -> bool:
        """
        Cancel active voice generation job.
        
        Args:
            job_id: Job identifier to cancel
            
        Returns:
            True if cancellation was successful
        """
        if job_id in self.active_jobs:
            task = self.active_jobs[job_id]
            task.cancel()
            
            try:
                await task
            except asyncio.CancelledError:
                pass
            
            del self.active_jobs[job_id]
            logger.info("Voice generation cancelled", job_id=job_id)
            return True
        
        return False
    
    def get_available_voices(self) -> Dict[str, str]:
        """Get available voice types and their descriptions."""
        return {
            "male_calm": "Male voice, calm and professional",
            "female_calm": "Female voice, calm and professional", 
            "male_dramatic": "Male voice, dramatic and intense",
            "female_dramatic": "Female voice, dramatic and intense"
        }
    
    async def validate_settings(self, settings: Dict[str, Any]) -> List[str]:
        """
        Validate voice generation settings.
        
        Args:
            settings: Settings to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        voice_type = settings.get("voice_type")
        if voice_type and voice_type not in self.voice_id_map:
            errors.append(f"Unknown voice type: {voice_type}")
        
        # Check API availability if real generation is requested
        if not self.client and settings.get("require_real_voice", False):
            errors.append("ElevenLabs API key not configured but real voice generation required")
        
        return errors
    
    def health_check(self) -> Dict[str, Any]:
        """Return service health status."""
        return {
            "status": "healthy" if self.client else "degraded",
            "service": "voice_generation",
            "api_available": bool(self.client),
            "available_voices": len(self.voice_id_map),
            "active_jobs": len(self.active_jobs)
        }
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get voice generation usage statistics."""
        if self.client:
            return await self.client.get_usage_stats()
        
        return {
            "character_count": 0,
            "character_limit": 0,
            "cost_usd": 0.0
        }