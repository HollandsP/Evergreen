"""
FFmpeg wrapper service for media processing operations.
"""

import os
import json
import subprocess
import logging
import tempfile
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

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
        
        logger.info(f"Initialized FFmpeg service with: {self.ffmpeg_path}")
    
    def _find_executable(self, name: str) -> Optional[str]:
        """Find executable in system PATH."""
        import shutil
        return shutil.which(name)
    
    def _run_command(self, cmd: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run FFmpeg command with error handling."""
        logger.debug(f"Running command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                check=check,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0 and check:
                logger.error(f"FFmpeg error: {result.stderr}")
                raise subprocess.CalledProcessError(result.returncode, cmd, result.stderr)
            
            return result
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg command failed: {e.stderr}")
            raise
        except Exception as e:
            logger.error(f"Error running FFmpeg: {str(e)}")
            raise
    
    def get_media_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get detailed media file information using ffprobe.
        
        Args:
            file_path: Path to media file
        
        Returns:
            Media information dictionary
        """
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
                'fps': eval(video_stream.get('r_frame_rate', '0/1')),
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