"""
MoviePy Wrapper Service for programmatic video editing.

This service provides a clean interface to MoviePy functionality,
optimized for the AI video editor's needs.
"""

import os
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
import tempfile

try:
    from moviepy.editor import (
        VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip,
        CompositeAudioClip, concatenate_videoclips, concatenate_audioclips,
        vfx, afx, ColorClip
    )
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    logging.warning("MoviePy not available. Install with: pip install moviepy")

logger = logging.getLogger(__name__)

class MoviePyWrapper:
    """
    Wrapper service for MoviePy video editing operations.
    
    Provides high-level video editing functions that can be called
    programmatically by the AI video editor.
    """
    
    def __init__(self):
        """Initialize MoviePy wrapper."""
        if not MOVIEPY_AVAILABLE:
            raise ImportError("MoviePy is required but not installed. Install with: pip install moviepy")
        
        # Default settings
        self.default_fps = 24
        self.default_audio_fps = 44100
        self.temp_dir = Path(tempfile.gettempdir()) / "moviepy_temp"
        self.temp_dir.mkdir(exist_ok=True)
        
        logger.info("Initialized MoviePy wrapper service")
    
    def trim_video(self, 
                   input_path: str, 
                   output_path: str,
                   start_time: Optional[float] = None,
                   duration: Optional[float] = None,
                   end_time: Optional[float] = None) -> str:
        """
        Trim video to specified time range.
        
        Args:
            input_path: Input video file path
            output_path: Output video file path
            start_time: Start time in seconds
            duration: Duration in seconds
            end_time: End time in seconds
            
        Returns:
            Path to output file
        """
        try:
            with VideoFileClip(input_path) as clip:
                # Calculate time parameters
                if start_time is None:
                    start_time = 0
                
                if end_time is None and duration is not None:
                    end_time = start_time + duration
                elif end_time is None:
                    end_time = clip.duration
                
                # Trim the clip
                trimmed = clip.subclip(start_time, end_time)
                
                # Write the result
                trimmed.write_videofile(
                    output_path,
                    fps=self.default_fps,
                    audio_codec='aac',
                    verbose=False,
                    logger=None
                )
                
                logger.info(f"Trimmed video: {input_path} -> {output_path}")
                return output_path
                
        except Exception as e:
            logger.error(f"Error trimming video: {e}")
            raise
    
    def change_speed(self, 
                     input_path: str, 
                     output_path: str,
                     speed_factor: float) -> str:
        """
        Change video playback speed.
        
        Args:
            input_path: Input video file path
            output_path: Output video file path
            speed_factor: Speed multiplier (2.0 = 2x faster, 0.5 = 2x slower)
            
        Returns:
            Path to output file
        """
        try:
            with VideoFileClip(input_path) as clip:
                # Apply speed change
                if speed_factor > 1.0:
                    # Speed up
                    sped_up = clip.fx(vfx.speedx, speed_factor)
                else:
                    # Slow down
                    sped_up = clip.fx(vfx.speedx, speed_factor)
                
                # Write the result
                sped_up.write_videofile(
                    output_path,
                    fps=self.default_fps,
                    audio_codec='aac',
                    verbose=False,
                    logger=None
                )
                
                logger.info(f"Changed speed by {speed_factor}x: {input_path} -> {output_path}")
                return output_path
                
        except Exception as e:
            logger.error(f"Error changing video speed: {e}")
            raise
    
    def add_fade_effect(self, 
                        input_path: str, 
                        output_path: str,
                        fade_type: str = "in",
                        duration: float = 1.0) -> str:
        """
        Add fade in/out effect to video.
        
        Args:
            input_path: Input video file path
            output_path: Output video file path
            fade_type: "in", "out", or "both"
            duration: Fade duration in seconds
            
        Returns:
            Path to output file
        """
        try:
            with VideoFileClip(input_path) as clip:
                result_clip = clip
                
                if fade_type in ["in", "both"]:
                    result_clip = result_clip.fx(vfx.fadein, duration)
                
                if fade_type in ["out", "both"]:
                    result_clip = result_clip.fx(vfx.fadeout, duration)
                
                # Write the result
                result_clip.write_videofile(
                    output_path,
                    fps=self.default_fps,
                    audio_codec='aac',
                    verbose=False,
                    logger=None
                )
                
                logger.info(f"Added fade {fade_type} effect: {input_path} -> {output_path}")
                return output_path
                
        except Exception as e:
            logger.error(f"Error adding fade effect: {e}")
            raise
    
    def add_text_overlay(self, 
                         input_path: str, 
                         output_path: str,
                         text: str,
                         position: str = "center",
                         font_size: int = 50,
                         color: str = "white",
                         duration: Optional[float] = None) -> str:
        """
        Add text overlay to video.
        
        Args:
            input_path: Input video file path
            output_path: Output video file path
            text: Text to overlay
            position: "center", "top", "bottom", "left", "right"
            font_size: Font size in pixels
            color: Text color
            duration: Text duration (None = full video)
            
        Returns:
            Path to output file
        """
        try:
            with VideoFileClip(input_path) as video:
                # Create text clip
                text_duration = duration or video.duration
                
                text_clip = TextClip(
                    text,
                    fontsize=font_size,
                    color=color,
                    font='Arial-Bold'
                ).set_duration(text_duration)
                
                # Set position
                if position == "center":
                    text_clip = text_clip.set_position('center')
                elif position == "top":
                    text_clip = text_clip.set_position(('center', 'top'))
                elif position == "bottom":
                    text_clip = text_clip.set_position(('center', 'bottom'))
                elif position == "left":
                    text_clip = text_clip.set_position(('left', 'center'))
                elif position == "right":
                    text_clip = text_clip.set_position(('right', 'center'))
                
                # Composite video with text
                result = CompositeVideoClip([video, text_clip])
                
                # Write the result
                result.write_videofile(
                    output_path,
                    fps=self.default_fps,
                    audio_codec='aac',
                    verbose=False,
                    logger=None
                )
                
                logger.info(f"Added text overlay '{text}': {input_path} -> {output_path}")
                return output_path
                
        except Exception as e:
            logger.error(f"Error adding text overlay: {e}")
            raise
    
    def adjust_audio_volume(self, 
                            input_path: str, 
                            output_path: str,
                            volume_factor: float) -> str:
        """
        Adjust audio volume of video.
        
        Args:
            input_path: Input video file path
            output_path: Output video file path
            volume_factor: Volume multiplier (1.0 = no change, 0.5 = half volume, 2.0 = double)
            
        Returns:
            Path to output file
        """
        try:
            with VideoFileClip(input_path) as clip:
                # Adjust audio volume
                adjusted = clip.fx(afx.volumex, volume_factor)
                
                # Write the result
                adjusted.write_videofile(
                    output_path,
                    fps=self.default_fps,
                    audio_codec='aac',
                    verbose=False,
                    logger=None
                )
                
                logger.info(f"Adjusted audio volume by {volume_factor}x: {input_path} -> {output_path}")
                return output_path
                
        except Exception as e:
            logger.error(f"Error adjusting audio volume: {e}")
            raise
    
    def add_transitions_between_clips(self, 
                                      clip_paths: List[str], 
                                      output_path: str,
                                      transition_type: str = "fade",
                                      duration: float = 1.0) -> str:
        """
        Add transitions between multiple video clips.
        
        Args:
            clip_paths: List of video file paths
            output_path: Output video file path
            transition_type: "fade", "crossfade", "slide"
            duration: Transition duration in seconds
            
        Returns:
            Path to output file
        """
        try:
            clips = []
            
            # Load all clips
            for path in clip_paths:
                clip = VideoFileClip(path)
                clips.append(clip)
            
            if len(clips) < 2:
                raise ValueError("Need at least 2 clips for transitions")
            
            # Create transitions between clips
            result_clips = [clips[0]]
            
            for i in range(1, len(clips)):
                prev_clip = result_clips[-1]
                current_clip = clips[i]
                
                if transition_type == "fade":
                    # Add fade out to previous clip and fade in to current clip
                    prev_with_fadeout = prev_clip.fx(vfx.fadeout, duration)
                    current_with_fadein = current_clip.fx(vfx.fadein, duration)
                    
                    # Remove the previous clip and add the modified ones
                    result_clips[-1] = prev_with_fadeout
                    result_clips.append(current_with_fadein)
                    
                elif transition_type == "crossfade":
                    # Crossfade transition
                    crossfade_duration = min(duration, prev_clip.duration, current_clip.duration)
                    
                    # Trim clips for crossfade
                    prev_trimmed = prev_clip.subclip(0, prev_clip.duration - crossfade_duration/2)
                    current_start = current_clip.subclip(crossfade_duration/2, current_clip.duration)
                    
                    # Create crossfade section
                    prev_fade_section = prev_clip.subclip(
                        prev_clip.duration - crossfade_duration, 
                        prev_clip.duration
                    ).fx(vfx.fadeout, crossfade_duration)
                    
                    current_fade_section = current_clip.subclip(
                        0, 
                        crossfade_duration
                    ).fx(vfx.fadein, crossfade_duration)
                    
                    crossfade_section = CompositeVideoClip([prev_fade_section, current_fade_section])
                    
                    # Update result clips
                    result_clips[-1] = prev_trimmed
                    result_clips.append(crossfade_section)
                    result_clips.append(current_start)
                else:
                    # Simple concatenation for unsupported transition types
                    result_clips.append(current_clip)
            
            # Concatenate all clips
            final_video = concatenate_videoclips(result_clips, method="compose")
            
            # Write the result
            final_video.write_videofile(
                output_path,
                fps=self.default_fps,
                audio_codec='aac',
                verbose=False,
                logger=None
            )
            
            # Cleanup
            for clip in clips:
                clip.close()
            final_video.close()
            
            logger.info(f"Added {transition_type} transitions between {len(clip_paths)} clips: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error adding transitions: {e}")
            raise
    
    def concatenate_clips(self, 
                          clip_paths: List[str], 
                          output_path: str) -> str:
        """
        Concatenate multiple video clips without transitions.
        
        Args:
            clip_paths: List of video file paths
            output_path: Output video file path
            
        Returns:
            Path to output file
        """
        try:
            clips = []
            
            # Load all clips
            for path in clip_paths:
                clip = VideoFileClip(path)
                clips.append(clip)
            
            # Concatenate clips
            final_video = concatenate_videoclips(clips, method="compose")
            
            # Write the result
            final_video.write_videofile(
                output_path,
                fps=self.default_fps,
                audio_codec='aac',
                verbose=False,
                logger=None
            )
            
            # Cleanup
            for clip in clips:
                clip.close()
            final_video.close()
            
            logger.info(f"Concatenated {len(clip_paths)} clips: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error concatenating clips: {e}")
            raise
    
    def split_clip(self, 
                   input_path: str, 
                   split_times: List[float],
                   output_dir: str,
                   name_prefix: str = "segment") -> List[str]:
        """
        Split a video clip into multiple segments.
        
        Args:
            input_path: Input video file path
            split_times: List of times (in seconds) where to split
            output_dir: Directory for output segments
            name_prefix: Prefix for output file names
            
        Returns:
            List of output file paths
        """
        try:
            output_paths = []
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            with VideoFileClip(input_path) as clip:
                # Add start and end times
                all_times = [0] + sorted(split_times) + [clip.duration]
                
                # Create segments
                for i in range(len(all_times) - 1):
                    start_time = all_times[i]
                    end_time = all_times[i + 1]
                    
                    # Skip very short segments
                    if end_time - start_time < 0.1:
                        continue
                    
                    # Create segment
                    segment = clip.subclip(start_time, end_time)
                    
                    # Generate output path
                    output_path = output_dir / f"{name_prefix}_{i+1:02d}.mp4"
                    
                    # Write segment
                    segment.write_videofile(
                        str(output_path),
                        fps=self.default_fps,
                        audio_codec='aac',
                        verbose=False,
                        logger=None
                    )
                    
                    output_paths.append(str(output_path))
                    segment.close()
            
            logger.info(f"Split clip into {len(output_paths)} segments")
            return output_paths
            
        except Exception as e:
            logger.error(f"Error splitting clip: {e}")
            raise
    
    def add_color_correction(self, 
                             input_path: str, 
                             output_path: str,
                             brightness: float = 1.0,
                             contrast: float = 1.0,
                             saturation: float = 1.0) -> str:
        """
        Apply color correction to video.
        
        Args:
            input_path: Input video file path
            output_path: Output video file path
            brightness: Brightness factor (1.0 = no change)
            contrast: Contrast factor (1.0 = no change)
            saturation: Saturation factor (1.0 = no change)
            
        Returns:
            Path to output file
        """
        try:
            with VideoFileClip(input_path) as clip:
                result = clip
                
                # Apply brightness
                if brightness != 1.0:
                    result = result.fx(vfx.colorx, brightness)
                
                # Apply gamma for contrast (MoviePy approximation)
                if contrast != 1.0:
                    gamma = 1.0 / contrast
                    result = result.fx(vfx.gamma_corr, gamma)
                
                # Write the result
                result.write_videofile(
                    output_path,
                    fps=self.default_fps,
                    audio_codec='aac',
                    verbose=False,
                    logger=None
                )
                
                logger.info(f"Applied color correction: {input_path} -> {output_path}")
                return output_path
                
        except Exception as e:
            logger.error(f"Error applying color correction: {e}")
            raise
    
    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """
        Get video file information.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary with video information
        """
        try:
            with VideoFileClip(video_path) as clip:
                info = {
                    'duration': clip.duration,
                    'fps': clip.fps,
                    'size': clip.size,
                    'width': clip.w,
                    'height': clip.h,
                    'has_audio': clip.audio is not None
                }
                
                if clip.audio:
                    info.update({
                        'audio_fps': clip.audio.fps,
                        'audio_duration': clip.audio.duration
                    })
                
                return info
                
        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            raise
    
    def extract_audio(self, 
                      video_path: str, 
                      audio_path: str) -> str:
        """
        Extract audio from video file.
        
        Args:
            video_path: Input video file path
            audio_path: Output audio file path
            
        Returns:
            Path to output audio file
        """
        try:
            with VideoFileClip(video_path) as video:
                if video.audio is None:
                    raise ValueError("Video has no audio track")
                
                audio = video.audio
                audio.write_audiofile(
                    audio_path,
                    fps=self.default_audio_fps,
                    verbose=False,
                    logger=None
                )
            
            logger.info(f"Extracted audio: {video_path} -> {audio_path}")
            return audio_path
            
        except Exception as e:
            logger.error(f"Error extracting audio: {e}")
            raise
    
    def replace_audio(self, 
                      video_path: str, 
                      audio_path: str, 
                      output_path: str) -> str:
        """
        Replace audio track in video.
        
        Args:
            video_path: Input video file path
            audio_path: New audio file path
            output_path: Output video file path
            
        Returns:
            Path to output file
        """
        try:
            with VideoFileClip(video_path) as video:
                with AudioFileClip(audio_path) as audio:
                    # Set the audio to the video
                    final_video = video.set_audio(audio)
                    
                    # Write the result
                    final_video.write_videofile(
                        output_path,
                        fps=self.default_fps,
                        audio_codec='aac',
                        verbose=False,
                        logger=None
                    )
            
            logger.info(f"Replaced audio: {video_path} + {audio_path} -> {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error replacing audio: {e}")
            raise