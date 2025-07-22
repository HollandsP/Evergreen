"""
FFmpeg wrapper service for media processing operations.
"""

import os
import json
import subprocess
import logging
import tempfile
import asyncio
import signal
import time
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
from contextlib import asynccontextmanager

import structlog
import re
from fractions import Fraction

logger = structlog.get_logger()

def safe_parse_frame_rate(frame_rate_str: str) -> float:
    """
    Safely parse frame rate string without using eval().
    
    Args:
        frame_rate_str: Frame rate as string (e.g., "30/1", "25/1")
    
    Returns:
        Frame rate as float
    """
    if not frame_rate_str or frame_rate_str == "0/0":
        return 0.0
    
    try:
        # Validate input format (should be "number/number")
        if not re.match(r'^\d+/\d+$', frame_rate_str):
            logger.warning(f"Invalid frame rate format: {frame_rate_str}")
            return 0.0
        
        # Use Fraction for safe parsing
        fraction = Fraction(frame_rate_str)
        return float(fraction)
    except (ValueError, ZeroDivisionError) as e:
        logger.warning(f"Error parsing frame rate '{frame_rate_str}': {e}")
        return 0.0

def validate_file_path(file_path: str) -> str:
    """
    Validate and sanitize file path to prevent path traversal attacks.
    
    Args:
        file_path: Input file path
    
    Returns:
        Sanitized file path
    
    Raises:
        ValueError: If path is invalid or potentially malicious
    """
    if not file_path:
        raise ValueError("File path cannot be empty")
    
    # Convert to Path object for safer handling
    path = Path(file_path).resolve()
    
    # Check for path traversal attempts
    if ".." in str(path) or str(path).startswith("/"):
        # Allow absolute paths but log for security monitoring
        logger.info(f"Absolute path used: {path}")
    
    # Ensure path exists and is a file (for input files)
    if not path.exists():
        raise ValueError(f"File does not exist: {path}")
    
    return str(path)

class FFmpegService:
    """Service wrapper for FFmpeg operations."""
    
    def __init__(self, ffmpeg_path: Optional[str] = None, ffprobe_path: Optional[str] = None):
        """
        Initialize FFmpeg service.
        
        Args:
            ffmpeg_path: Path to ffmpeg executable
            ffprobe_path: Path to ffprobe executable
        """
        self.ffmpeg_path = ffmpeg_path or self._find_executable('ffmpeg')
        self.ffprobe_path = ffprobe_path or self._find_executable('ffprobe')
        
        if not self.ffmpeg_path:
            raise RuntimeError("FFmpeg not found. Please install FFmpeg or provide path.")
        if not self.ffprobe_path:
            raise RuntimeError("FFprobe not found. Please install FFmpeg or provide path.")
        
        # Process management
        self.active_processes: Dict[str, subprocess.Popen] = {}
        self.default_timeout = 300  # 5 minutes
        
        logger.info(f"Initialized FFmpeg service with: {self.ffmpeg_path}")
    
    def _find_executable(self, name: str) -> Optional[str]:
        """Find executable in system PATH."""
        import shutil
        return shutil.which(name)
    
    def _terminate_process(self, process: subprocess.Popen) -> None:
        """Safely terminate a process."""
        try:
            if os.name == 'nt':  # Windows
                process.terminate()
            else:  # Unix-like
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            
            # Give it a moment to terminate gracefully
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if needed
                if os.name == 'nt':
                    process.kill()
                else:
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                    
        except (ProcessLookupError, OSError):
            # Process already terminated
            pass
    
    async def _run_command_async(self, cmd: List[str], check: bool = True,
                                timeout: Optional[float] = None,
                                progress_callback=None) -> subprocess.CompletedProcess:
        """Run FFmpeg command asynchronously with progress monitoring."""
        logger.debug(f"Running async command: {' '.join(cmd[:3])}...")
        
        timeout = timeout or self.default_timeout
        process_id = f"ffmpeg_async_{int(time.time() * 1000)}"
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            self.active_processes[process_id] = process
            
            # Monitor progress if callback provided
            if progress_callback:
                asyncio.create_task(self._monitor_progress(process, progress_callback))
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )
            
            if process.returncode != 0 and check:
                logger.error(
                    "Async FFmpeg command failed",
                    returncode=process.returncode,
                    stderr=stderr.decode()[:500]
                )
                raise subprocess.CalledProcessError(
                    process.returncode, cmd, stderr.decode()
                )
            
            result = subprocess.CompletedProcess(
                cmd, process.returncode, 
                stdout.decode() if stdout else '',
                stderr.decode() if stderr else ''
            )
            return result
            
        except asyncio.TimeoutError:
            if process:
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), timeout=5)
                except asyncio.TimeoutError:
                    process.kill()
            logger.error("Async FFmpeg command timed out", timeout=timeout)
            raise
        finally:
            if process_id in self.active_processes:
                del self.active_processes[process_id]
    
    async def _monitor_progress(self, process, progress_callback):
        """Monitor FFmpeg progress and call callback with updates."""
        try:
            while process.returncode is None:
                # Read stderr line by line for progress info
                line = await process.stderr.readline()
                if not line:
                    break
                
                line = line.decode().strip()
                if 'time=' in line:
                    # Extract time information for progress
                    try:
                        time_match = re.search(r'time=([\d:.]+)', line)
                        if time_match:
                            progress_callback(time_match.group(1))
                    except Exception:
                        pass
                        
                await asyncio.sleep(0.1)
        except Exception as e:
            logger.debug("Progress monitoring error", error=str(e))
    
    def _run_command(self, cmd: List[str], check: bool = True, 
                    timeout: Optional[float] = None, 
                    process_id: Optional[str] = None) -> subprocess.CompletedProcess:
        """Run FFmpeg command with error handling and timeout."""
        logger.debug(f"Running command: {' '.join(cmd[:3])}...")
        
        timeout = timeout or self.default_timeout
        process_id = process_id or f"ffmpeg_{int(time.time() * 1000)}"
        
        process = None
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=os.setsid if os.name != 'nt' else None
            )
            
            # Track active process
            self.active_processes[process_id] = process
            
            stdout, stderr = process.communicate(timeout=timeout)
            returncode = process.returncode
            
            if returncode != 0 and check:
                logger.error(
                    "FFmpeg command failed",
                    returncode=returncode,
                    stderr=stderr[:500]
                )
                raise subprocess.CalledProcessError(returncode, cmd, stderr)
            
            # Create result object matching subprocess.run
            result = subprocess.CompletedProcess(cmd, returncode, stdout, stderr)
            return result
            
        except subprocess.TimeoutExpired:
            if process:
                self._terminate_process(process)
            logger.error("FFmpeg command timed out", timeout=timeout)
            raise
        except subprocess.CalledProcessError as e:
            logger.error("FFmpeg command failed", error=e.stderr)
            raise
        except Exception as e:
            if process:
                self._terminate_process(process)
            logger.error("Error running FFmpeg", error=str(e))
            raise
        finally:
            # Clean up process tracking
            if process_id in self.active_processes:
                del self.active_processes[process_id]
    
    def get_media_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get detailed media file information using ffprobe.
        
        Args:
            file_path: Path to media file
        
        Returns:
            Media information dictionary
        """
        # Validate and sanitize file path
        file_path = validate_file_path(file_path)
        cmd = [
            self.ffprobe_path,
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            file_path
        ]
        
        result = self._run_command(cmd)
        info = json.loads(result.stdout)
        
        # Extract relevant information
        format_info = info.get('format', {})
        streams = info.get('streams', [])
        
        video_stream = next((s for s in streams if s['codec_type'] == 'video'), None)
        audio_stream = next((s for s in streams if s['codec_type'] == 'audio'), None)
        
        media_info = {
            'duration': float(format_info.get('duration', 0)),
            'size': int(format_info.get('size', 0)),
            'bit_rate': int(format_info.get('bit_rate', 0)),
            'format_name': format_info.get('format_name', ''),
        }
        
        if video_stream:
            media_info.update({
                'width': int(video_stream.get('width', 0)),
                'height': int(video_stream.get('height', 0)),
                'fps': safe_parse_frame_rate(video_stream.get('r_frame_rate', '0/1')),
                'codec': video_stream.get('codec_name', ''),
                'video_bitrate': int(video_stream.get('bit_rate', 0))
            })
        
        if audio_stream:
            media_info.update({
                'audio_codec': audio_stream.get('codec_name', ''),
                'sample_rate': int(audio_stream.get('sample_rate', 0)),
                'channels': int(audio_stream.get('channels', 0)),
                'audio_bitrate': int(audio_stream.get('bit_rate', 0))
            })
        
        return media_info
    
    def concatenate(self, input_files: List[str], output_path: str,
                   video_fade_in: float = 0, video_fade_out: float = 0) -> str:
        """
        Concatenate multiple video files.
        
        Args:
            input_files: List of input video file paths
            output_path: Output file path
            video_fade_in: Fade in duration in seconds
            video_fade_out: Fade out duration in seconds
        
        Returns:
            Output file path
        """
        # Validate all input files
        validated_files = [validate_file_path(f) for f in input_files]
        input_files = validated_files
        # Create a temporary file list for concat
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for file_path in input_files:
                f.write(f"file '{os.path.abspath(file_path)}'\n")
            list_file = f.name
        
        try:
            cmd = [
                self.ffmpeg_path,
                '-f', 'concat',
                '-safe', '0',
                '-i', list_file,
                '-c', 'copy'
            ]
            
            # Add fade effects if specified
            if video_fade_in > 0 or video_fade_out > 0:
                # Need to re-encode for fade effects
                cmd.extend(['-c:v', 'libx264'])
                
                filters = []
                if video_fade_in > 0:
                    filters.append(f"fade=t=in:d={video_fade_in}")
                if video_fade_out > 0:
                    # Get total duration first
                    total_duration = sum(self.get_media_info(f)['duration'] for f in input_files)
                    fade_out_start = total_duration - video_fade_out
                    filters.append(f"fade=t=out:st={fade_out_start}:d={video_fade_out}")
                
                if filters:
                    cmd.extend(['-vf', ','.join(filters)])
            
            cmd.extend(['-y', output_path])
            
            self._run_command(cmd)
            return output_path
            
        finally:
            os.unlink(list_file)
    
    def add_audio_to_video(self, video_path: str, audio_tracks: List[Dict[str, Any]],
                          output_path: str, sync_mode: str = 'timestamp') -> str:
        """
        Add audio tracks to video with synchronization.
        
        Args:
            video_path: Path to video file
            audio_tracks: List of audio track info with paths and timing
            output_path: Output file path
            sync_mode: Synchronization mode ('timestamp' or 'stretch')
        
        Returns:
            Output file path
        """
        if not audio_tracks:
            raise ValueError("No audio tracks provided")
        
        cmd = [self.ffmpeg_path, '-i', video_path]
        
        # Add all audio inputs
        for track in audio_tracks:
            cmd.extend(['-i', track['audio_path']])
        
        # Build complex filter for audio mixing and timing
        filter_complex = []
        audio_inputs = []
        
        for idx, track in enumerate(audio_tracks):
            audio_idx = idx + 1  # Video is input 0
            
            # Apply delay if needed
            start_time = track.get('timing', {}).get('start', 0)
            if start_time > 0:
                filter_complex.append(
                    f"[{audio_idx}:a]adelay={int(start_time * 1000)}|{int(start_time * 1000)}[a{idx}]"
                )
                audio_inputs.append(f"[a{idx}]")
            else:
                audio_inputs.append(f"[{audio_idx}:a]")
        
        # Mix all audio tracks
        if len(audio_inputs) > 1:
            mix_filter = f"{''.join(audio_inputs)}amix=inputs={len(audio_inputs)}:duration=longest[aout]"
            filter_complex.append(mix_filter)
            audio_output = "[aout]"
        else:
            audio_output = audio_inputs[0]
        
        if filter_complex:
            cmd.extend(['-filter_complex', ';'.join(filter_complex)])
        
        cmd.extend([
            '-map', '0:v',  # Video from first input
            '-map', audio_output,  # Mixed audio
            '-c:v', 'copy',  # Copy video codec
            '-c:a', 'aac',  # Audio codec
            '-b:a', '192k',  # Audio bitrate
            '-y', output_path
        ])
        
        self._run_command(cmd)
        return output_path
    
    def merge_audio(self, input_files: List[str], output_path: str,
                   normalize: bool = True) -> str:
        """
        Merge multiple audio files into one.
        
        Args:
            input_files: List of input audio file paths
            output_path: Output file path
            normalize: Whether to normalize audio levels
        
        Returns:
            Output file path
        """
        cmd = [self.ffmpeg_path]
        
        # Add all inputs
        for file_path in input_files:
            cmd.extend(['-i', file_path])
        
        # Build filter for merging
        filter_parts = []
        for i in range(len(input_files)):
            filter_parts.append(f"[{i}:a]")
        
        filter_str = f"{''.join(filter_parts)}amix=inputs={len(input_files)}:duration=longest"
        
        if normalize:
            filter_str += ",loudnorm"
        
        cmd.extend([
            '-filter_complex', filter_str,
            '-ac', '2',  # Stereo output
            '-ar', '44100',  # Sample rate
            '-y', output_path
        ])
        
        self._run_command(cmd)
        return output_path
    
    def mix_audio(self, input_tracks: List[Dict[str, Any]], output_path: str,
                 normalize: bool = True) -> str:
        """
        Mix audio tracks with individual volume control.
        
        Args:
            input_tracks: List of track dicts with 'audio_path' and 'volume'
            output_path: Output file path
            normalize: Whether to normalize final output
        
        Returns:
            Output file path
        """
        cmd = [self.ffmpeg_path]
        
        # Add all inputs
        for track in input_tracks:
            cmd.extend(['-i', track['audio_path']])
        
        # Build complex filter
        filter_parts = []
        for i, track in enumerate(input_tracks):
            volume = track.get('volume', 1.0)
            filter_parts.append(f"[{i}:a]volume={volume}[a{i}]")
        
        # Mix all tracks
        mix_inputs = ''.join([f"[a{i}]" for i in range(len(input_tracks))])
        mix_filter = f"{mix_inputs}amix=inputs={len(input_tracks)}:duration=longest"
        
        if normalize:
            mix_filter += "[mixed];[mixed]loudnorm"
        
        filter_complex = ';'.join(filter_parts) + ';' + mix_filter
        
        cmd.extend([
            '-filter_complex', filter_complex,
            '-ac', '2',
            '-ar', '44100',
            '-y', output_path
        ])
        
        self._run_command(cmd)
        return output_path
    
    def add_subtitles(self, video_path: str, subtitle_path: str,
                     output_path: str, subtitle_filter: str = "") -> str:
        """
        Add subtitles to video.
        
        Args:
            video_path: Path to video file
            subtitle_path: Path to subtitle file (SRT, ASS, etc.)
            output_path: Output file path
            subtitle_filter: Additional subtitle filter options
        
        Returns:
            Output file path
        """
        cmd = [
            self.ffmpeg_path,
            '-i', video_path,
            '-vf', f"subtitles={subtitle_path}{subtitle_filter}",
            '-c:a', 'copy',
            '-y', output_path
        ]
        
        self._run_command(cmd)
        return output_path
    
    def extract_segment(self, input_path: str, output_path: str,
                       start_time: float, duration: float) -> str:
        """
        Extract a segment from media file.
        
        Args:
            input_path: Input file path
            output_path: Output file path
            start_time: Start time in seconds
            duration: Duration in seconds
        
        Returns:
            Output file path
        """
        cmd = [
            self.ffmpeg_path,
            '-ss', str(start_time),
            '-i', input_path,
            '-t', str(duration),
            '-c', 'copy',
            '-avoid_negative_ts', 'make_zero',
            '-y', output_path
        ]
        
        self._run_command(cmd)
        return output_path
    
    def transcode(self, input_path: str, output_path: str,
                 video_codec: str = 'libx264', video_bitrate: str = '5M',
                 resolution: Optional[str] = None, fps: Optional[int] = None,
                 audio_codec: str = 'aac', audio_bitrate: str = '192k',
                 preset: str = 'medium', **kwargs) -> str:
        """
        Transcode media file with specified settings.
        
        Args:
            input_path: Input file path
            output_path: Output file path
            video_codec: Video codec to use
            video_bitrate: Video bitrate
            resolution: Output resolution (e.g., '1920x1080')
            fps: Output frame rate
            audio_codec: Audio codec to use
            audio_bitrate: Audio bitrate
            preset: Encoding preset (ultrafast, fast, medium, slow, veryslow)
            **kwargs: Additional FFmpeg options
        
        Returns:
            Output file path
        """
        cmd = [
            self.ffmpeg_path,
            '-i', input_path,
            '-c:v', video_codec,
            '-b:v', video_bitrate,
            '-preset', preset,
            '-c:a', audio_codec,
            '-b:a', audio_bitrate
        ]
        
        if resolution:
            cmd.extend(['-s', resolution])
        
        if fps:
            cmd.extend(['-r', str(fps)])
        
        # Add any additional options
        for key, value in kwargs.items():
            cmd.extend([f'-{key}', str(value)])
        
        cmd.extend(['-y', output_path])
        
        self._run_command(cmd)
        return output_path
    
    def apply_filters(self, input_path: str, output_path: str,
                     filters: List[str]) -> str:
        """
        Apply video filters to media file.
        
        Args:
            input_path: Input file path
            output_path: Output file path
            filters: List of FFmpeg filter strings
        
        Returns:
            Output file path
        """
        filter_complex = ','.join(filters)
        
        cmd = [
            self.ffmpeg_path,
            '-i', input_path,
            '-vf', filter_complex,
            '-c:a', 'copy',
            '-y', output_path
        ]
        
        self._run_command(cmd)
        return output_path
    
    def trim_video(self, input_path: str, output_path: str,
                  start_time: Optional[float] = None,
                  duration: Optional[float] = None,
                  end_time: Optional[float] = None) -> str:
        """
        Trim video to specified duration or time range.
        
        Args:
            input_path: Input file path
            output_path: Output file path
            start_time: Start time in seconds
            duration: Duration in seconds
            end_time: End time in seconds
        
        Returns:
            Output file path
        """
        cmd = [self.ffmpeg_path]
        
        if start_time is not None:
            cmd.extend(['-ss', str(start_time)])
        
        cmd.extend(['-i', input_path])
        
        if duration is not None:
            cmd.extend(['-t', str(duration)])
        elif end_time is not None and start_time is not None:
            duration = end_time - start_time
            cmd.extend(['-t', str(duration)])
        
        cmd.extend([
            '-c', 'copy',
            '-avoid_negative_ts', 'make_zero',
            '-y', output_path
        ])
        
        self._run_command(cmd)
        return output_path
    
    def generate_thumbnail(self, video_path: str, output_path: str,
                          timestamp: float = 0) -> str:
        """
        Generate thumbnail from video at specified timestamp.
        
        Args:
            video_path: Path to video file
            output_path: Output image path
            timestamp: Timestamp in seconds
        
        Returns:
            Output file path
        """
        cmd = [
            self.ffmpeg_path,
            '-ss', str(timestamp),
            '-i', video_path,
            '-vframes', '1',
            '-q:v', '2',
            '-y', output_path
        ]
        
        self._run_command(cmd)
        return output_path