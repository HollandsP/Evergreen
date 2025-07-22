"""
Video Assembly Service

Handles final video assembly from all generated components with proper
error handling and resource management.
"""

import os
import asyncio
import tempfile
from typing import Dict, List, Any, Optional
from pathlib import Path

import structlog

from .ffmpeg_service import FFmpegService
from ..utils.file_manager import FileManager

logger = structlog.get_logger()


class VideoAssemblyService:
    """Service for assembling final videos from components."""
    
    def __init__(self):
        """Initialize video assembly service."""
        self.ffmpeg_service = FFmpegService()
        self.file_manager = FileManager()
        
        logger.info("Video assembly service initialized")
    
    async def assemble_video(self, job_id: str, parsed_script: Dict[str, Any],
                           voice_files: List[str], ui_elements: List[str],
                           visual_assets: List[str], settings: Dict[str, Any]) -> str:
        """
        Assemble final video from all components.
        
        Args:
            job_id: Job identifier
            parsed_script: Parsed script data
            voice_files: List of voice audio files
            ui_elements: List of UI animation files
            visual_assets: List of visual asset files
            settings: Assembly settings
            
        Returns:
            Path to assembled video file
        """
        logger.info(
            "Starting video assembly",
            job_id=job_id,
            voice_files=len(voice_files),
            ui_elements=len(ui_elements),
            visual_assets=len(visual_assets)
        )
        
        try:
            # Determine assembly strategy
            has_visuals = bool(visual_assets)
            has_ui = bool(ui_elements)
            has_audio = bool(voice_files)
            
            logger.info(
                "Assembly strategy determined",
                job_id=job_id,
                has_visuals=has_visuals,
                has_ui=has_ui,
                has_audio=has_audio
            )
            
            if not (has_visuals or has_ui or has_audio):
                raise ValueError("No assets provided for assembly")
            
            # Choose assembly method
            if has_visuals and has_ui:
                # Full composition with overlay
                output_file = await self._assemble_with_overlay(
                    job_id, parsed_script, voice_files, ui_elements, visual_assets, settings
                )
            elif has_visuals:
                # Visual-only with audio
                output_file = await self._assemble_visual_only(
                    job_id, parsed_script, voice_files, visual_assets, settings
                )
            elif has_ui:
                # Terminal UI only with audio
                output_file = await self._assemble_ui_only(
                    job_id, parsed_script, voice_files, ui_elements, settings
                )
            else:
                # Audio-only (podcast style)
                output_file = await self._assemble_audio_only(
                    job_id, parsed_script, voice_files, settings
                )
            
            if not output_file or not os.path.exists(output_file):
                raise Exception("Assembly failed - no output file created")
            
            file_size = os.path.getsize(output_file) / (1024 * 1024)  # MB
            total_duration = parsed_script.get('total_duration', 0)
            
            logger.info(
                "Video assembly completed successfully",
                job_id=job_id,
                output_file=output_file,
                size_mb=round(file_size, 1),
                duration_seconds=total_duration
            )
            
            return output_file
            
        except Exception as e:
            logger.error(
                "Video assembly failed",
                job_id=job_id,
                error=str(e),
                exc_info=True
            )
            
            # Create error placeholder
            return await self._create_error_placeholder(job_id, str(e))
    
    async def _assemble_with_overlay(self, job_id: str, parsed_script: Dict[str, Any],
                                   voice_files: List[str], ui_elements: List[str],
                                   visual_assets: List[str], settings: Dict[str, Any]) -> str:
        """Assemble video with terminal UI overlaid on visuals."""
        logger.info("Assembling with overlay composition", job_id=job_id)
        
        try:
            # Build timeline for synchronization
            timeline = self._build_timeline(parsed_script, voice_files, ui_elements, visual_assets)
            
            with tempfile.TemporaryDirectory() as temp_dir:
                # Step 1: Create visual track
                visual_track = await self._create_visual_track(timeline, temp_dir)
                
                # Step 2: Add UI overlay if available
                if ui_elements:
                    composition_track = await self._add_ui_overlay(
                        visual_track, timeline, temp_dir
                    )
                else:
                    composition_track = visual_track
                
                # Step 3: Add audio track
                final_video = await self._add_audio_track(
                    composition_track, timeline, temp_dir, job_id
                )
                
                return final_video
                
        except Exception as e:
            logger.error("Overlay assembly failed", job_id=job_id, error=str(e))
            raise
    
    async def _assemble_visual_only(self, job_id: str, parsed_script: Dict[str, Any],
                                  voice_files: List[str], visual_assets: List[str],
                                  settings: Dict[str, Any]) -> str:
        """Assemble video with only visuals and audio."""
        logger.info("Assembling visual-only composition", job_id=job_id)
        
        try:
            timeline = self._build_timeline(parsed_script, voice_files, [], visual_assets)
            
            with tempfile.TemporaryDirectory() as temp_dir:
                # Create visual track
                visual_track = await self._create_visual_track(timeline, temp_dir)
                
                # Add audio
                final_video = await self._add_audio_track(
                    visual_track, timeline, temp_dir, job_id
                )
                
                return final_video
                
        except Exception as e:
            logger.error("Visual-only assembly failed", job_id=job_id, error=str(e))
            raise
    
    async def _assemble_ui_only(self, job_id: str, parsed_script: Dict[str, Any],
                              voice_files: List[str], ui_elements: List[str],
                              settings: Dict[str, Any]) -> str:
        """Assemble video with only terminal UI and audio."""
        logger.info("Assembling UI-only composition", job_id=job_id)
        
        try:
            timeline = self._build_timeline(parsed_script, voice_files, ui_elements, [])
            
            with tempfile.TemporaryDirectory() as temp_dir:
                # Create UI track (treat UI as main video)
                ui_track = await self._create_ui_track(timeline, temp_dir)
                
                # Add audio
                final_video = await self._add_audio_track(
                    ui_track, timeline, temp_dir, job_id
                )
                
                return final_video
                
        except Exception as e:
            logger.error("UI-only assembly failed", job_id=job_id, error=str(e))
            raise
    
    async def _assemble_audio_only(self, job_id: str, parsed_script: Dict[str, Any],
                                 voice_files: List[str], settings: Dict[str, Any]) -> str:
        """Create audio-only output with waveform visualization."""
        logger.info("Assembling audio-only composition", job_id=job_id)
        
        try:
            timeline = self._build_timeline(parsed_script, voice_files, [], [])
            
            with tempfile.TemporaryDirectory() as temp_dir:
                # Create audio track
                audio_track = await self._create_audio_track(timeline, temp_dir)
                
                if not audio_track:
                    raise Exception("No audio track created")
                
                # Create waveform visualization
                final_video = await self._create_waveform_video(
                    audio_track, temp_dir, job_id
                )
                
                return final_video
                
        except Exception as e:
            logger.error("Audio-only assembly failed", job_id=job_id, error=str(e))
            raise
    
    def _build_timeline(self, parsed_script: Dict[str, Any], voice_files: List[str],
                       ui_elements: List[str], visual_assets: List[str]) -> List[Dict[str, Any]]:
        """Build timeline mapping assets to scenes."""
        scenes = parsed_script.get('scenes', [])
        timeline = []
        
        # Map assets by filename patterns
        voice_map = self._map_assets_by_timestamp(voice_files)
        ui_map = self._map_assets_by_timestamp(ui_elements)
        visual_map = self._map_assets_by_timestamp(visual_assets)
        
        total_duration = parsed_script.get('total_duration', 60)
        
        for i, scene in enumerate(scenes):
            timestamp = scene['timestamp']
            timestamp_clean = timestamp.replace(':', '_')
            start_time = scene['timestamp_seconds']
            
            # Calculate scene duration
            if i + 1 < len(scenes):
                end_time = scenes[i + 1]['timestamp_seconds']
                duration = end_time - start_time
            else:
                duration = total_duration - start_time
            
            # Ensure minimum duration
            duration = max(duration, 2.0)
            
            timeline_entry = {
                'scene': scene,
                'start': start_time,
                'duration': duration,
                'voice': voice_map.get(timestamp_clean, []),
                'ui': ui_map.get(timestamp_clean, []),
                'visual': visual_map.get(timestamp_clean, [])
            }
            
            timeline.append(timeline_entry)
        
        logger.debug(
            "Timeline built",
            total_entries=len(timeline),
            total_duration=total_duration
        )
        
        return timeline
    
    def _map_assets_by_timestamp(self, asset_files: List[str]) -> Dict[str, List[str]]:
        """Map asset files to timestamps based on filename patterns."""
        asset_map = {}
        
        for file_path in asset_files:
            try:
                filename = os.path.basename(file_path)
                # Pattern: {job_id}_{type}_{timestamp}_{index}.ext
                parts = filename.split('_')
                
                # Find timestamp part (e.g., "0_00" for "0:00")
                for i, part in enumerate(parts):
                    if '_' in part and part.replace('_', ':').replace(':', '').isdigit():
                        timestamp = part
                        if timestamp not in asset_map:
                            asset_map[timestamp] = []
                        asset_map[timestamp].append(file_path)
                        break
                    elif i > 0 and parts[i-1] in ['scene', 'ui', 'visual', 'voice']:
                        # Found timestamp after type identifier
                        timestamp = part
                        if i + 1 < len(parts) and '_' in parts[i + 1]:
                            timestamp = f"{timestamp}_{parts[i + 1].split('.')[0]}"
                        
                        if timestamp not in asset_map:
                            asset_map[timestamp] = []
                        asset_map[timestamp].append(file_path)
                        break
            except Exception as e:
                logger.debug("Failed to map asset", file_path=file_path, error=str(e))
        
        return asset_map
    
    async def _create_visual_track(self, timeline: List[Dict], temp_dir: str) -> str:
        """Create concatenated visual track."""
        visual_segments = []
        
        for i, entry in enumerate(timeline):
            if entry['visual']:
                # Use first visual asset
                visual_file = entry['visual'][0]
                
                # Trim/extend to match scene duration
                segment_file = os.path.join(temp_dir, f"visual_segment_{i}.mp4")
                
                try:
                    # Use FFmpeg service to trim video
                    trimmed_file = self.ffmpeg_service.trim_video(
                        visual_file, segment_file,
                        duration=entry['duration']
                    )
                    visual_segments.append(trimmed_file)
                except Exception as e:
                    logger.warning(f"Failed to trim visual segment: {e}")
                    # Create black frame placeholder
                    black_segment = await self._create_black_frame(
                        temp_dir, f"black_{i}.mp4", entry['duration']
                    )
                    visual_segments.append(black_segment)
            else:
                # Create black frame for missing visuals
                black_segment = await self._create_black_frame(
                    temp_dir, f"black_{i}.mp4", entry['duration']
                )
                visual_segments.append(black_segment)
        
        # Concatenate all segments
        if visual_segments:
            concat_file = os.path.join(temp_dir, "visual_track.mp4")
            return self.ffmpeg_service.concatenate(visual_segments, concat_file)
        
        raise Exception("No visual segments created")
    
    async def _create_black_frame(self, temp_dir: str, filename: str, duration: float) -> str:
        """Create black frame video."""
        output_path = os.path.join(temp_dir, filename)
        
        cmd = [
            'ffmpeg', '-y',
            '-f', 'lavfi',
            '-i', f'color=c=black:s=1920x1080:d={duration}',
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-pix_fmt', 'yuv420p',
            output_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        await process.communicate()
        
        if process.returncode == 0:
            return output_path
        else:
            raise Exception(f"Failed to create black frame: {filename}")
    
    async def _add_audio_track(self, video_file: str, timeline: List[Dict],
                             temp_dir: str, job_id: str) -> str:
        """Add synchronized audio track to video."""
        # Create audio track from timeline
        audio_track = await self._create_audio_track(timeline, temp_dir)
        
        if audio_track:
            # Combine video and audio
            final_file = await self.file_manager.get_output_path(f"{job_id}_final.mp4")
            
            return self.ffmpeg_service.add_audio_to_video(
                video_file,
                [{'audio_path': audio_track, 'timing': {'start': 0}}],
                final_file
            )
        else:
            # No audio - just copy video to final location
            final_file = await self.file_manager.get_output_path(f"{job_id}_final.mp4")
            
            cmd = ['ffmpeg', '-y', '-i', video_file, '-c', 'copy', final_file]
            process = await asyncio.create_subprocess_exec(*cmd)
            await process.communicate()
            
            return final_file if process.returncode == 0 else video_file
    
    async def _create_audio_track(self, timeline: List[Dict], temp_dir: str) -> Optional[str]:
        """Create synchronized audio track from timeline."""
        audio_segments = []
        
        # Build audio sequence with proper timing
        for entry in timeline:
            if entry['voice']:
                # Add voice file
                audio_segments.append(entry['voice'][0])
            else:
                # Add silence for scenes without audio
                silence_file = os.path.join(temp_dir, f"silence_{len(audio_segments)}.wav")
                
                cmd = [
                    'ffmpeg', '-y',
                    '-f', 'lavfi',
                    '-i', f'anullsrc=r=44100:cl=stereo:d={entry["duration"]}',
                    silence_file
                ]
                
                process = await asyncio.create_subprocess_exec(*cmd)
                await process.communicate()
                
                if process.returncode == 0:
                    audio_segments.append(silence_file)
        
        if audio_segments:
            # Concatenate audio segments
            audio_track = os.path.join(temp_dir, "audio_track.wav")
            return self.ffmpeg_service.merge_audio(audio_segments, audio_track)
        
        return None
    
    async def _create_error_placeholder(self, job_id: str, error_message: str) -> str:
        """Create error placeholder file."""
        try:
            error_file = await self.file_manager.get_output_path(f"{job_id}_error.txt")
            
            error_content = f"""
Video Assembly Failed
Job ID: {job_id}
Error: {error_message}
Timestamp: {time.time()}

This is a placeholder file indicating that video assembly failed.
Please check the logs for more detailed error information.
"""
            
            with open(error_file, 'w') as f:
                f.write(error_content)
            
            return error_file
            
        except Exception as e:
            logger.error("Failed to create error placeholder", error=str(e))
            raise
    
    def health_check(self) -> Dict[str, Any]:
        """Return service health status."""
        ffmpeg_health = bool(self.ffmpeg_service.ffmpeg_path)
        
        return {
            "status": "healthy" if ffmpeg_health else "degraded",
            "service": "video_assembly",
            "ffmpeg_available": ffmpeg_health,
            "ffmpeg_path": self.ffmpeg_service.ffmpeg_path
        }