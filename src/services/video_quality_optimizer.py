"""
Video quality optimization with adaptive encoding.
Analyzes content and applies optimal encoding settings for quality vs file size.
"""

import os
import asyncio
import logging
import subprocess
import json
import tempfile
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path
import cv2
import numpy as np
from dataclasses import dataclass
from enum import Enum

from .gpu_accelerated_ffmpeg import GPUAcceleratedFFmpeg
from .ffmpeg_service import FFmpegService

logger = logging.getLogger(__name__)


class ContentType(Enum):
    """Types of video content for optimization."""
    TALKING_HEAD = "talking_head"
    ACTION = "action"
    ANIMATION = "animation"
    SLIDESHOW = "slideshow"
    NATURE = "nature"
    GAMING = "gaming"
    SCREENCAST = "screencast"
    MUSIC_VIDEO = "music_video"


class QualityPreset(Enum):
    """Quality optimization presets."""
    ULTRA = "ultra"          # Maximum quality, larger files
    HIGH = "high"           # High quality, balanced
    MEDIUM = "medium"       # Good quality, smaller files
    LOW = "low"            # Acceptable quality, minimal size
    STREAMING = "streaming" # Optimized for streaming
    MOBILE = "mobile"      # Optimized for mobile devices


@dataclass
class VideoAnalysis:
    """Video content analysis results."""
    content_type: ContentType
    motion_score: float  # 0-1, amount of motion
    complexity_score: float  # 0-1, visual complexity
    dark_scenes: float  # 0-1, percentage of dark content
    resolution: Tuple[int, int]
    fps: float
    duration: float
    bitrate: int
    has_audio: bool
    scene_changes: List[float]  # Timestamps of scene changes


@dataclass
class OptimizationProfile:
    """Encoding optimization profile."""
    codec: str
    preset: str
    crf: int  # Constant Rate Factor
    bitrate: Optional[str]
    maxrate: Optional[str]
    bufsize: Optional[str]
    gop_size: int  # Group of Pictures size
    b_frames: int
    ref_frames: int
    profile: str
    level: str
    pixel_format: str
    audio_codec: str
    audio_bitrate: str
    two_pass: bool
    filters: List[str]


class VideoQualityOptimizer:
    """Optimizes video quality with adaptive encoding."""
    
    def __init__(self):
        self.gpu_ffmpeg = GPUAcceleratedFFmpeg()
        self.ffmpeg = FFmpegService()
        self.use_gpu = self.gpu_ffmpeg.gpu_info['vendor'] is not None
        
    async def analyze_video(self, video_path: str) -> VideoAnalysis:
        """Analyze video content for optimization."""
        
        # Get basic video info
        info = await self._get_video_info(video_path)
        
        # Analyze motion and complexity
        motion_score = await self._analyze_motion(video_path)
        complexity_score = await self._analyze_complexity(video_path)
        dark_scenes = await self._analyze_brightness(video_path)
        scene_changes = await self._detect_scene_changes(video_path)
        
        # Determine content type
        content_type = self._determine_content_type(
            motion_score, complexity_score, scene_changes, info
        )
        
        return VideoAnalysis(
            content_type=content_type,
            motion_score=motion_score,
            complexity_score=complexity_score,
            dark_scenes=dark_scenes,
            resolution=(info['width'], info['height']),
            fps=info['fps'],
            duration=info['duration'],
            bitrate=info['bitrate'],
            has_audio=info['has_audio'],
            scene_changes=scene_changes
        )
    
    async def _get_video_info(self, video_path: str) -> Dict[str, Any]:
        """Get video metadata."""
        
        cmd = [
            'ffprobe', '-v', 'quiet',
            '-print_format', 'json',
            '-show_format', '-show_streams',
            video_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, _ = await process.communicate()
        data = json.loads(stdout.decode())
        
        # Extract video stream info
        video_stream = next(
            (s for s in data['streams'] if s['codec_type'] == 'video'), None
        )
        
        if not video_stream:
            raise ValueError("No video stream found")
        
        # Extract audio stream info
        audio_stream = next(
            (s for s in data['streams'] if s['codec_type'] == 'audio'), None
        )
        
        return {
            'width': int(video_stream['width']),
            'height': int(video_stream['height']),
            'fps': eval(video_stream['r_frame_rate']),
            'duration': float(data['format']['duration']),
            'bitrate': int(data['format'].get('bit_rate', 0)),
            'codec': video_stream['codec_name'],
            'has_audio': audio_stream is not None
        }
    
    async def _analyze_motion(self, video_path: str) -> float:
        """Analyze motion in video (0-1 scale)."""
        
        cap = cv2.VideoCapture(video_path)
        
        # Sample frames for analysis
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        sample_interval = max(1, total_frames // 30)  # Sample 30 frames
        
        motion_scores = []
        prev_frame = None
        
        for i in range(0, total_frames, sample_interval):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            
            if not ret:
                break
            
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            if prev_frame is not None:
                # Calculate frame difference
                diff = cv2.absdiff(prev_frame, gray)
                motion_score = np.mean(diff) / 255.0
                motion_scores.append(motion_score)
            
            prev_frame = gray
        
        cap.release()
        
        # Return average motion score
        return np.mean(motion_scores) if motion_scores else 0.0
    
    async def _analyze_complexity(self, video_path: str) -> float:
        """Analyze visual complexity (0-1 scale)."""
        
        cap = cv2.VideoCapture(video_path)
        
        # Sample frames
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        sample_interval = max(1, total_frames // 20)
        
        complexity_scores = []
        
        for i in range(0, total_frames, sample_interval):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            
            if not ret:
                break
            
            # Calculate complexity using edge detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            
            # Complexity score based on edge density
            complexity = np.sum(edges > 0) / edges.size
            complexity_scores.append(complexity)
        
        cap.release()
        
        return np.mean(complexity_scores) if complexity_scores else 0.0
    
    async def _analyze_brightness(self, video_path: str) -> float:
        """Analyze percentage of dark scenes (0-1 scale)."""
        
        cap = cv2.VideoCapture(video_path)
        
        # Sample frames
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        sample_interval = max(1, total_frames // 20)
        
        dark_count = 0
        samples = 0
        
        for i in range(0, total_frames, sample_interval):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            
            if not ret:
                break
            
            # Calculate average brightness
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            avg_brightness = np.mean(gray)
            
            # Consider dark if below threshold
            if avg_brightness < 50:  # 0-255 scale
                dark_count += 1
            
            samples += 1
        
        cap.release()
        
        return dark_count / samples if samples > 0 else 0.0
    
    async def _detect_scene_changes(self, video_path: str) -> List[float]:
        """Detect scene changes in video."""
        
        # Use FFmpeg scene detection
        cmd = [
            'ffmpeg', '-i', video_path,
            '-filter:v', 'select=\'gt(scene,0.4)\',showinfo',
            '-f', 'null', '-'
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        _, stderr = await process.communicate()
        
        # Parse scene change timestamps
        scene_changes = []
        for line in stderr.decode().split('\n'):
            if 'showinfo' in line and 'pts_time' in line:
                # Extract timestamp
                parts = line.split()
                for part in parts:
                    if part.startswith('pts_time:'):
                        timestamp = float(part.split(':')[1])
                        scene_changes.append(timestamp)
                        break
        
        return scene_changes
    
    def _determine_content_type(
        self,
        motion_score: float,
        complexity_score: float,
        scene_changes: List[float],
        info: Dict[str, Any]
    ) -> ContentType:
        """Determine video content type based on analysis."""
        
        # Scene change frequency
        scene_change_rate = len(scene_changes) / info['duration'] if info['duration'] > 0 else 0
        
        # Decision logic
        if motion_score < 0.1 and scene_change_rate < 0.1:
            return ContentType.SLIDESHOW
        elif motion_score < 0.2 and complexity_score < 0.3:
            return ContentType.TALKING_HEAD
        elif motion_score > 0.5 and scene_change_rate > 0.5:
            return ContentType.ACTION
        elif complexity_score > 0.6 and motion_score > 0.3:
            return ContentType.GAMING
        elif complexity_score < 0.2:
            return ContentType.ANIMATION
        elif scene_change_rate > 1.0:
            return ContentType.MUSIC_VIDEO
        else:
            return ContentType.NATURE
    
    def get_optimization_profile(
        self,
        analysis: VideoAnalysis,
        quality_preset: QualityPreset,
        target_platform: Optional[str] = None
    ) -> OptimizationProfile:
        """Get optimal encoding profile based on analysis."""
        
        # Base profiles for different quality presets
        base_profiles = {
            QualityPreset.ULTRA: {
                'crf': 16,
                'preset': 'slower',
                'b_frames': 3,
                'ref_frames': 4,
                'profile': 'high',
                'level': '5.1'
            },
            QualityPreset.HIGH: {
                'crf': 20,
                'preset': 'slow',
                'b_frames': 2,
                'ref_frames': 3,
                'profile': 'high',
                'level': '4.1'
            },
            QualityPreset.MEDIUM: {
                'crf': 23,
                'preset': 'medium',
                'b_frames': 2,
                'ref_frames': 2,
                'profile': 'main',
                'level': '4.0'
            },
            QualityPreset.LOW: {
                'crf': 28,
                'preset': 'fast',
                'b_frames': 1,
                'ref_frames': 1,
                'profile': 'main',
                'level': '3.1'
            },
            QualityPreset.STREAMING: {
                'crf': 23,
                'preset': 'faster',
                'b_frames': 0,
                'ref_frames': 1,
                'profile': 'main',
                'level': '4.0'
            },
            QualityPreset.MOBILE: {
                'crf': 25,
                'preset': 'fast',
                'b_frames': 1,
                'ref_frames': 1,
                'profile': 'baseline',
                'level': '3.0'
            }
        }
        
        base = base_profiles[quality_preset]
        
        # Adjust based on content type
        if analysis.content_type == ContentType.TALKING_HEAD:
            # Less motion, can use higher compression
            base['crf'] += 2
            base['ref_frames'] = min(base['ref_frames'] + 1, 5)
        
        elif analysis.content_type == ContentType.ACTION:
            # High motion, need better quality
            base['crf'] = max(base['crf'] - 2, 15)
            base['b_frames'] = min(base['b_frames'] + 1, 3)
        
        elif analysis.content_type == ContentType.ANIMATION:
            # Can use higher compression for flat colors
            base['crf'] += 1
            
        elif analysis.content_type == ContentType.SCREENCAST:
            # Need sharp text
            base['crf'] = max(base['crf'] - 1, 16)
        
        # Adjust for dark scenes
        if analysis.dark_scenes > 0.5:
            # Dark scenes need lower compression
            base['crf'] = max(base['crf'] - 2, 15)
        
        # Determine codec
        if self.use_gpu:
            codec = self.gpu_ffmpeg.get_gpu_encoder('h264') or 'libx264'
        else:
            codec = 'libx264'
        
        # GOP size based on scene changes
        avg_scene_duration = analysis.duration / max(len(analysis.scene_changes), 1)
        gop_size = min(int(avg_scene_duration * analysis.fps), 250)
        
        # Bitrate constraints for streaming
        bitrate = None
        maxrate = None
        bufsize = None
        
        if quality_preset == QualityPreset.STREAMING:
            # Set bitrate constraints
            if analysis.resolution[1] >= 2160:  # 4K
                bitrate = '15M'
                maxrate = '20M'
            elif analysis.resolution[1] >= 1080:  # 1080p
                bitrate = '5M'
                maxrate = '8M'
            elif analysis.resolution[1] >= 720:  # 720p
                bitrate = '2.5M'
                maxrate = '4M'
            else:  # SD
                bitrate = '1M'
                maxrate = '1.5M'
            
            bufsize = maxrate  # Buffer size = max rate for streaming
        
        # Audio settings
        audio_bitrate = '192k' if quality_preset in [QualityPreset.ULTRA, QualityPreset.HIGH] else '128k'
        
        # Filters
        filters = []
        
        # Denoising for high compression
        if base['crf'] > 25 and analysis.complexity_score > 0.5:
            filters.append('hqdn3d=4:3:6:4.5')
        
        # Sharpening for low bitrate
        if base['crf'] > 23:
            filters.append('unsharp=5:5:0.5:3:3:0.0')
        
        return OptimizationProfile(
            codec=codec,
            preset=base['preset'],
            crf=base['crf'],
            bitrate=bitrate,
            maxrate=maxrate,
            bufsize=bufsize,
            gop_size=gop_size,
            b_frames=base['b_frames'],
            ref_frames=base['ref_frames'],
            profile=base['profile'],
            level=base['level'],
            pixel_format='yuv420p',
            audio_codec='aac',
            audio_bitrate=audio_bitrate,
            two_pass=quality_preset == QualityPreset.ULTRA and not self.use_gpu,
            filters=filters
        )
    
    async def optimize_video(
        self,
        input_path: str,
        output_path: str,
        quality_preset: QualityPreset = QualityPreset.HIGH,
        target_platform: Optional[str] = None,
        custom_analysis: Optional[VideoAnalysis] = None
    ) -> Dict[str, Any]:
        """Optimize video with adaptive encoding."""
        
        # Analyze video if not provided
        if custom_analysis:
            analysis = custom_analysis
        else:
            logger.info("Analyzing video content...")
            analysis = await self.analyze_video(input_path)
        
        logger.info(f"Content type: {analysis.content_type.value}")
        logger.info(f"Motion score: {analysis.motion_score:.2f}")
        logger.info(f"Complexity score: {analysis.complexity_score:.2f}")
        
        # Get optimization profile
        profile = self.get_optimization_profile(analysis, quality_preset, target_platform)
        
        # Build FFmpeg command
        cmd = [self.ffmpeg_path if hasattr(self, 'ffmpeg_path') else 'ffmpeg', '-y']
        
        # Input
        cmd.extend(['-i', input_path])
        
        # Video encoding
        cmd.extend(['-c:v', profile.codec])
        
        if 'nvenc' in profile.codec:
            # NVIDIA specific options
            cmd.extend([
                '-preset', profile.preset,
                '-rc', 'vbr',
                '-cq', str(profile.crf),
                '-profile:v', profile.profile,
                '-level', profile.level,
                '-b_ref_mode', 'middle',
                '-temporal-aq', '1',
                '-spatial-aq', '1',
                '-rc-lookahead', '32'
            ])
        elif profile.codec == 'libx264':
            # x264 options
            cmd.extend([
                '-preset', profile.preset,
                '-crf', str(profile.crf),
                '-profile:v', profile.profile,
                '-level', profile.level,
                '-g', str(profile.gop_size),
                '-bf', str(profile.b_frames),
                '-refs', str(profile.ref_frames)
            ])
        
        # Bitrate constraints if specified
        if profile.bitrate:
            cmd.extend(['-b:v', profile.bitrate])
        if profile.maxrate:
            cmd.extend(['-maxrate', profile.maxrate])
        if profile.bufsize:
            cmd.extend(['-bufsize', profile.bufsize])
        
        # Filters
        if profile.filters:
            cmd.extend(['-vf', ','.join(profile.filters)])
        
        # Audio encoding
        if analysis.has_audio:
            cmd.extend([
                '-c:a', profile.audio_codec,
                '-b:a', profile.audio_bitrate
            ])
        
        # Output format options
        cmd.extend([
            '-pix_fmt', profile.pixel_format,
            '-movflags', '+faststart',  # Web optimization
            output_path
        ])
        
        # Execute encoding
        logger.info(f"Optimizing video with profile: {quality_preset.value}")
        
        if profile.two_pass:
            # Two-pass encoding for best quality
            success = await self._two_pass_encode(cmd, input_path, output_path)
        else:
            # Single pass
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            success = process.returncode == 0
        
        if not success:
            logger.error(f"Video optimization failed")
            raise RuntimeError("Video optimization failed")
        
        # Calculate optimization results
        input_size = os.path.getsize(input_path)
        output_size = os.path.getsize(output_path)
        compression_ratio = (1 - output_size / input_size) * 100
        
        results = {
            'input_size': input_size,
            'output_size': output_size,
            'compression_ratio': compression_ratio,
            'profile_used': profile,
            'content_type': analysis.content_type.value,
            'quality_preset': quality_preset.value
        }
        
        logger.info(f"Optimization complete: {compression_ratio:.1f}% size reduction")
        
        return results
    
    async def _two_pass_encode(
        self,
        base_cmd: List[str],
        input_path: str,
        output_path: str
    ) -> bool:
        """Perform two-pass encoding."""
        
        # First pass
        pass1_cmd = base_cmd.copy()
        pass1_cmd[pass1_cmd.index('-y')] = '-y'
        pass1_cmd.extend(['-pass', '1', '-f', 'null', 'NUL' if os.name == 'nt' else '/dev/null'])
        
        process = await asyncio.create_subprocess_exec(
            *pass1_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        await process.communicate()
        
        if process.returncode != 0:
            return False
        
        # Second pass
        pass2_cmd = base_cmd.copy()
        pass2_idx = len(pass2_cmd) - 1
        pass2_cmd.insert(pass2_idx, '-pass')
        pass2_cmd.insert(pass2_idx + 1, '2')
        
        process = await asyncio.create_subprocess_exec(
            *pass2_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        await process.communicate()
        
        return process.returncode == 0
    
    def get_platform_recommendations(self, platform: str) -> Dict[str, Any]:
        """Get platform-specific encoding recommendations."""
        
        recommendations = {
            'youtube': {
                'quality_preset': QualityPreset.HIGH,
                'resolution_max': (3840, 2160),  # 4K
                'fps_max': 60,
                'audio_bitrate': '192k',
                'format': 'mp4'
            },
            'instagram': {
                'quality_preset': QualityPreset.MEDIUM,
                'resolution_max': (1080, 1920),  # Vertical
                'fps_max': 30,
                'audio_bitrate': '128k',
                'format': 'mp4',
                'duration_max': 60  # seconds
            },
            'tiktok': {
                'quality_preset': QualityPreset.MEDIUM,
                'resolution_max': (1080, 1920),
                'fps_max': 30,
                'audio_bitrate': '128k',
                'format': 'mp4',
                'duration_max': 180
            },
            'twitter': {
                'quality_preset': QualityPreset.MEDIUM,
                'resolution_max': (1920, 1080),
                'fps_max': 30,
                'audio_bitrate': '128k',
                'format': 'mp4',
                'duration_max': 140
            },
            'web': {
                'quality_preset': QualityPreset.STREAMING,
                'resolution_max': (1920, 1080),
                'fps_max': 30,
                'audio_bitrate': '128k',
                'format': 'mp4'
            }
        }
        
        return recommendations.get(platform, recommendations['web'])
    
    async def batch_optimize(
        self,
        video_paths: List[str],
        output_dir: str,
        quality_preset: QualityPreset = QualityPreset.HIGH,
        parallel: int = 2
    ) -> List[Dict[str, Any]]:
        """Optimize multiple videos in batch."""
        
        results = []
        
        # Process in batches
        for i in range(0, len(video_paths), parallel):
            batch = video_paths[i:i + parallel]
            
            # Process batch in parallel
            tasks = []
            for video_path in batch:
                output_path = os.path.join(
                    output_dir,
                    f"optimized_{os.path.basename(video_path)}"
                )
                
                task = self.optimize_video(
                    video_path, output_path, quality_preset
                )
                tasks.append(task)
            
            # Wait for batch to complete
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch optimization error: {result}")
                    results.append({'error': str(result)})
                else:
                    results.append(result)
        
        return results