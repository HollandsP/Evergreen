"""
Media assembly tasks using FFmpeg for final video composition.
"""

import os
import json
import subprocess
import tempfile
from typing import Dict, List, Any, Optional, Tuple
from celery import Task, group, chain
from celery.utils.log import get_task_logger
from workers.celery_app import app
from workers.utils import (
    ProgressReporter, update_job_status, exponential_backoff_retry,
    TaskMetrics, estimate_processing_time
)
from src.core.database.models import JobStatus
from src.services.ffmpeg_service import FFmpegService

logger = get_task_logger(__name__)

class AssemblyTask(Task):
    """Base class for media assembly tasks."""
    
    def __init__(self):
        self.ffmpeg = None
        
    def __call__(self, *args, **kwargs):
        """Initialize FFmpeg service on first call."""
        if self.ffmpeg is None:
            self.ffmpeg = FFmpegService()
        return self.run(*args, **kwargs)

@app.task(bind=True, base=AssemblyTask, name='workers.tasks.assembly_tasks.assemble_final_video',
          max_retries=3, default_retry_delay=60)
def assemble_final_video(self, job_id: str, assembly_data: Dict[str, Any],
                        output_settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Assemble final video from all components (video segments, audio, effects).
    
    Args:
        job_id: Unique job identifier
        assembly_data: Data containing paths to all media components
        output_settings: Optional output format settings
    
    Returns:
        Final video file path and metadata
    """
    logger.info(f"Starting final video assembly for job {job_id}")
    progress = ProgressReporter(job_id, total_steps=100)
    metrics = TaskMetrics('assemble_final_video')
    
    try:
        update_job_status(job_id, JobStatus.PROCESSING)
        progress.update(5, "Preparing media components")
        
        # Default output settings
        output_settings = output_settings or {
            'format': 'mp4',
            'codec': 'h264',
            'quality': 'high',
            'resolution': '1920x1080',
            'fps': 30,
            'audio_codec': 'aac',
            'audio_bitrate': '192k'
        }
        
        # Validate all input files exist
        validate_media_files(assembly_data)
        
        # Step 1: Concatenate video segments
        progress.update(20, "Concatenating video segments")
        concatenated_video = concatenate_videos(
            self.ffmpeg,
            assembly_data['video_segments'],
            job_id
        )
        
        # Step 2: Sync audio with video
        progress.update(40, "Synchronizing audio tracks")
        video_with_audio = sync_audio_video(
            self.ffmpeg,
            concatenated_video,
            assembly_data['audio_files'],
            job_id
        )
        
        # Step 3: Add transitions
        if assembly_data.get('transitions'):
            progress.update(60, "Applying transitions")
            video_with_transitions = apply_transitions(
                self.ffmpeg,
                video_with_audio,
                assembly_data['transitions'],
                job_id
            )
        else:
            video_with_transitions = video_with_audio
        
        # Step 4: Apply final encoding and optimization
        progress.update(80, "Encoding final video")
        final_video = encode_final_output(
            self.ffmpeg,
            video_with_transitions,
            output_settings,
            job_id
        )
        
        # Generate metadata
        video_info = self.ffmpeg.get_media_info(final_video)
        
        result = {
            'job_id': job_id,
            'final_video_path': final_video,
            'duration': video_info['duration'],
            'file_size': os.path.getsize(final_video),
            'resolution': f"{video_info['width']}x{video_info['height']}",
            'fps': video_info['fps'],
            'codec': video_info['codec'],
            'bitrate': video_info['bitrate']
        }
        
        progress.complete("Video assembly completed successfully")
        metrics.record_execution(success=True, duration=progress.current_step)
        
        return result
        
    except Exception as e:
        logger.error(f"Video assembly failed for job {job_id}: {str(e)}")
        metrics.record_execution(success=False, duration=0)
        
        # Retry with exponential backoff
        countdown = 60 * (2 ** self.request.retries)
        raise self.retry(exc=e, countdown=countdown)

@app.task(bind=True, base=AssemblyTask, name='workers.tasks.assembly_tasks.merge_audio_tracks',
          max_retries=3)
def merge_audio_tracks(self, job_id: str, audio_tracks: List[Dict[str, Any]],
                      merge_settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Merge multiple audio tracks (dialogue, music, SFX) into a single track.
    
    Args:
        job_id: Unique job identifier
        audio_tracks: List of audio track information
        merge_settings: Optional merge settings
    
    Returns:
        Merged audio file path and metadata
    """
    logger.info(f"Merging audio tracks for job {job_id}")
    progress = ProgressReporter(job_id, total_steps=100)
    
    try:
        progress.update(10, "Analyzing audio tracks")
        
        # Default merge settings
        merge_settings = merge_settings or {
            'normalize': True,
            'dialogue_volume': 1.0,
            'music_volume': 0.3,
            'sfx_volume': 0.5
        }
        
        # Group tracks by type
        dialogue_tracks = [t for t in audio_tracks if t['type'] == 'dialogue']
        music_tracks = [t for t in audio_tracks if t['type'] == 'music']
        sfx_tracks = [t for t in audio_tracks if t['type'] == 'sfx']
        
        # Process each track type
        progress.update(30, "Processing dialogue tracks")
        dialogue_mix = None
        if dialogue_tracks:
            dialogue_mix = mix_audio_tracks(
                self.ffmpeg,
                dialogue_tracks,
                merge_settings['dialogue_volume'],
                job_id,
                'dialogue'
            )
        
        progress.update(50, "Processing music tracks")
        music_mix = None
        if music_tracks:
            music_mix = mix_audio_tracks(
                self.ffmpeg,
                music_tracks,
                merge_settings['music_volume'],
                job_id,
                'music'
            )
        
        progress.update(70, "Processing SFX tracks")
        sfx_mix = None
        if sfx_tracks:
            sfx_mix = mix_audio_tracks(
                self.ffmpeg,
                sfx_tracks,
                merge_settings['sfx_volume'],
                job_id,
                'sfx'
            )
        
        # Final merge
        progress.update(85, "Creating final audio mix")
        final_tracks = [t for t in [dialogue_mix, music_mix, sfx_mix] if t]
        
        if len(final_tracks) == 0:
            raise ValueError("No audio tracks to merge")
        elif len(final_tracks) == 1:
            final_audio = final_tracks[0]
        else:
            final_audio = self.ffmpeg.merge_audio(
                input_files=final_tracks,
                output_path=get_output_path(job_id, 'final_audio', 'wav'),
                normalize=merge_settings['normalize']
            )
        
        # Get audio info
        audio_info = self.ffmpeg.get_media_info(final_audio)
        
        result = {
            'job_id': job_id,
            'merged_audio_path': final_audio,
            'duration': audio_info['duration'],
            'channels': audio_info['channels'],
            'sample_rate': audio_info['sample_rate'],
            'track_count': {
                'dialogue': len(dialogue_tracks),
                'music': len(music_tracks),
                'sfx': len(sfx_tracks)
            }
        }
        
        progress.complete("Audio merge completed")
        return result
        
    except Exception as e:
        logger.error(f"Audio merge failed for job {job_id}: {str(e)}")
        raise self.retry(exc=e)

@app.task(bind=True, base=AssemblyTask, name='workers.tasks.assembly_tasks.add_subtitles',
          max_retries=2)
def add_subtitles(self, job_id: str, video_path: str,
                 subtitle_data: List[Dict[str, Any]],
                 style_settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Add subtitles to video.
    
    Args:
        job_id: Unique job identifier
        video_path: Path to video file
        subtitle_data: List of subtitle entries with timing
        style_settings: Optional subtitle styling
    
    Returns:
        Video with subtitles path and metadata
    """
    logger.info(f"Adding subtitles to video for job {job_id}")
    progress = ProgressReporter(job_id, total_steps=100)
    
    try:
        progress.update(10, "Generating subtitle file")
        
        # Default style settings
        style_settings = style_settings or {
            'font': 'Arial',
            'font_size': 24,
            'color': 'white',
            'outline_color': 'black',
            'outline_width': 2,
            'position': 'bottom',
            'margin': 20
        }
        
        # Create SRT file
        srt_path = create_srt_file(subtitle_data, job_id)
        
        progress.update(30, "Applying subtitles to video")
        
        # Apply subtitles using FFmpeg
        output_path = get_output_path(job_id, 'video_with_subtitles', 'mp4')
        
        subtitle_filter = create_subtitle_filter(style_settings)
        
        subtitled_video = self.ffmpeg.add_subtitles(
            video_path=video_path,
            subtitle_path=srt_path,
            output_path=output_path,
            subtitle_filter=subtitle_filter
        )
        
        result = {
            'job_id': job_id,
            'original_video': video_path,
            'subtitled_video': subtitled_video,
            'subtitle_count': len(subtitle_data),
            'subtitle_file': srt_path,
            'style_applied': style_settings
        }
        
        progress.complete("Subtitles added successfully")
        return result
        
    except Exception as e:
        logger.error(f"Subtitle addition failed: {str(e)}")
        raise self.retry(exc=e)

@app.task(bind=True, base=AssemblyTask, name='workers.tasks.assembly_tasks.create_preview',
          max_retries=2)
def create_preview(self, job_id: str, video_path: str,
                  preview_settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Create a preview/trailer version of the video.
    
    Args:
        job_id: Unique job identifier
        video_path: Path to full video
        preview_settings: Optional preview settings
    
    Returns:
        Preview video path and metadata
    """
    logger.info(f"Creating preview for job {job_id}")
    progress = ProgressReporter(job_id, total_steps=100)
    
    try:
        progress.update(10, "Analyzing video for key moments")
        
        # Default preview settings
        preview_settings = preview_settings or {
            'duration': 30,  # 30 second preview
            'include_intro': True,
            'include_highlights': True,
            'fade_in': 1,
            'fade_out': 1
        }
        
        # Get video info
        video_info = self.ffmpeg.get_media_info(video_path)
        total_duration = video_info['duration']
        
        # Select key moments for preview
        progress.update(30, "Selecting preview segments")
        segments = select_preview_segments(
            total_duration,
            preview_settings['duration'],
            preview_settings
        )
        
        # Extract segments
        progress.update(50, "Extracting preview segments")
        segment_files = []
        for idx, segment in enumerate(segments):
            segment_path = self.ffmpeg.extract_segment(
                input_path=video_path,
                output_path=get_output_path(job_id, f'preview_segment_{idx}', 'mp4'),
                start_time=segment['start'],
                duration=segment['duration']
            )
            segment_files.append(segment_path)
        
        # Concatenate segments
        progress.update(70, "Assembling preview")
        preview_path = self.ffmpeg.concatenate(
            input_files=segment_files,
            output_path=get_output_path(job_id, 'preview', 'mp4'),
            video_fade_in=preview_settings['fade_in'],
            video_fade_out=preview_settings['fade_out']
        )
        
        # Clean up temporary segment files
        for segment_file in segment_files:
            os.unlink(segment_file)
        
        result = {
            'job_id': job_id,
            'preview_path': preview_path,
            'preview_duration': preview_settings['duration'],
            'segments_used': len(segments),
            'source_video': video_path
        }
        
        progress.complete("Preview created successfully")
        return result
        
    except Exception as e:
        logger.error(f"Preview creation failed: {str(e)}")
        raise self.retry(exc=e)

@app.task(bind=True, name='workers.tasks.assembly_tasks.optimize_for_platform',
          max_retries=2)
def optimize_for_platform(self, job_id: str, video_path: str,
                         platform: str, optimization_settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Optimize video for specific platform (YouTube, TikTok, Instagram, etc.).
    
    Args:
        job_id: Unique job identifier
        video_path: Path to source video
        platform: Target platform name
        optimization_settings: Optional platform-specific settings
    
    Returns:
        Optimized video path and metadata
    """
    logger.info(f"Optimizing video for {platform} - job {job_id}")
    progress = ProgressReporter(job_id, total_steps=100)
    
    try:
        ffmpeg = FFmpegService()
        progress.update(10, f"Applying {platform} optimization settings")
        
        # Platform-specific presets
        platform_presets = {
            'youtube': {
                'format': 'mp4',
                'codec': 'h264',
                'resolution': '1920x1080',
                'fps': 30,
                'bitrate': '8M',
                'audio_codec': 'aac',
                'audio_bitrate': '192k',
                'aspect_ratio': '16:9'
            },
            'tiktok': {
                'format': 'mp4',
                'codec': 'h264',
                'resolution': '1080x1920',  # Vertical
                'fps': 30,
                'bitrate': '6M',
                'audio_codec': 'aac',
                'audio_bitrate': '128k',
                'aspect_ratio': '9:16',
                'max_duration': 60
            },
            'instagram': {
                'format': 'mp4',
                'codec': 'h264',
                'resolution': '1080x1080',  # Square
                'fps': 30,
                'bitrate': '5M',
                'audio_codec': 'aac',
                'audio_bitrate': '128k',
                'aspect_ratio': '1:1',
                'max_duration': 60
            },
            'twitter': {
                'format': 'mp4',
                'codec': 'h264',
                'resolution': '1280x720',
                'fps': 30,
                'bitrate': '5M',
                'audio_codec': 'aac',
                'audio_bitrate': '128k',
                'max_duration': 140
            }
        }
        
        # Get platform settings
        settings = platform_presets.get(platform.lower(), platform_presets['youtube'])
        if optimization_settings:
            settings.update(optimization_settings)
        
        progress.update(30, "Analyzing source video")
        
        # Get source video info
        video_info = ffmpeg.get_media_info(video_path)
        
        # Check if duration adjustment needed
        output_path = get_output_path(job_id, f'{platform}_optimized', 'mp4')
        
        if 'max_duration' in settings and video_info['duration'] > settings['max_duration']:
            progress.update(40, f"Trimming video to {settings['max_duration']} seconds")
            # Trim video to platform limit
            video_path = ffmpeg.trim_video(
                input_path=video_path,
                output_path=get_output_path(job_id, f'{platform}_trimmed', 'mp4'),
                duration=settings['max_duration']
            )
        
        progress.update(60, "Applying platform optimization")
        
        # Apply platform optimization
        optimized_video = ffmpeg.transcode(
            input_path=video_path,
            output_path=output_path,
            video_codec=settings['codec'],
            video_bitrate=settings['bitrate'],
            resolution=settings['resolution'],
            fps=settings['fps'],
            audio_codec=settings['audio_codec'],
            audio_bitrate=settings['audio_bitrate']
        )
        
        # Get optimized video info
        optimized_info = ffmpeg.get_media_info(optimized_video)
        
        result = {
            'job_id': job_id,
            'platform': platform,
            'optimized_video': optimized_video,
            'original_size': os.path.getsize(video_path),
            'optimized_size': os.path.getsize(optimized_video),
            'size_reduction': f"{(1 - os.path.getsize(optimized_video) / os.path.getsize(video_path)) * 100:.1f}%",
            'resolution': settings['resolution'],
            'duration': optimized_info['duration'],
            'settings_applied': settings
        }
        
        progress.complete(f"Video optimized for {platform}")
        return result
        
    except Exception as e:
        logger.error(f"Platform optimization failed: {str(e)}")
        raise self.retry(exc=e)

# Helper functions
def validate_media_files(assembly_data: Dict[str, Any]):
    """Validate that all required media files exist."""
    missing_files = []
    
    # Check video segments
    for segment in assembly_data.get('video_segments', []):
        if not os.path.exists(segment['video_path']):
            missing_files.append(segment['video_path'])
    
    # Check audio files
    for audio in assembly_data.get('audio_files', []):
        if not os.path.exists(audio['audio_path']):
            missing_files.append(audio['audio_path'])
    
    if missing_files:
        raise FileNotFoundError(f"Missing media files: {missing_files}")

def concatenate_videos(ffmpeg: FFmpegService, video_segments: List[Dict[str, Any]],
                      job_id: str) -> str:
    """Concatenate multiple video segments."""
    # Sort segments by sequence
    sorted_segments = sorted(video_segments, key=lambda x: x.get('sequence', 0))
    
    # Extract file paths
    video_paths = [s['video_path'] for s in sorted_segments]
    
    # Concatenate
    output_path = get_output_path(job_id, 'concatenated', 'mp4')
    return ffmpeg.concatenate(video_paths, output_path)

def sync_audio_video(ffmpeg: FFmpegService, video_path: str,
                    audio_files: List[Dict[str, Any]], job_id: str) -> str:
    """Synchronize audio tracks with video."""
    # Sort audio by timestamp
    sorted_audio = sorted(audio_files, key=lambda x: x['timing']['start'])
    
    # Create a complex filter for audio positioning
    output_path = get_output_path(job_id, 'video_with_audio', 'mp4')
    
    return ffmpeg.add_audio_to_video(
        video_path=video_path,
        audio_tracks=sorted_audio,
        output_path=output_path,
        sync_mode='timestamp'
    )

def apply_transitions(ffmpeg: FFmpegService, video_path: str,
                     transitions: List[Dict[str, Any]], job_id: str) -> str:
    """Apply transitions between scenes."""
    # This is simplified - real implementation would be more complex
    output_path = get_output_path(job_id, 'video_with_transitions', 'mp4')
    
    # Apply transitions using FFmpeg filters
    transition_filters = []
    for transition in transitions:
        filter_str = create_transition_filter(
            transition['type'],
            transition.get('duration', 1.0),
            transition.get('position')
        )
        transition_filters.append(filter_str)
    
    return ffmpeg.apply_filters(
        input_path=video_path,
        output_path=output_path,
        filters=transition_filters
    )

def encode_final_output(ffmpeg: FFmpegService, video_path: str,
                       output_settings: Dict[str, Any], job_id: str) -> str:
    """Encode final video with specified settings."""
    output_path = get_output_path(job_id, 'final', output_settings['format'])
    
    return ffmpeg.transcode(
        input_path=video_path,
        output_path=output_path,
        video_codec=output_settings['codec'],
        video_bitrate=f"{output_settings.get('bitrate', '8M')}",
        resolution=output_settings['resolution'],
        fps=output_settings['fps'],
        audio_codec=output_settings['audio_codec'],
        audio_bitrate=output_settings['audio_bitrate'],
        preset=output_settings.get('preset', 'medium')
    )

def mix_audio_tracks(ffmpeg: FFmpegService, tracks: List[Dict[str, Any]],
                    volume: float, job_id: str, track_type: str) -> str:
    """Mix multiple audio tracks of the same type."""
    if len(tracks) == 1:
        return tracks[0]['audio_path']
    
    output_path = get_output_path(job_id, f'{track_type}_mix', 'wav')
    
    # Apply volume adjustment
    adjusted_tracks = []
    for track in tracks:
        track_copy = track.copy()
        track_copy['volume'] = volume
        adjusted_tracks.append(track_copy)
    
    return ffmpeg.mix_audio(
        input_tracks=adjusted_tracks,
        output_path=output_path,
        normalize=True
    )

def create_srt_file(subtitle_data: List[Dict[str, Any]], job_id: str) -> str:
    """Create SRT subtitle file from subtitle data."""
    output_dir = f"/mnt/c/Users/holla/OneDrive/Desktop/CodeProjects/Evergreen/output/projects/{job_id}"
    os.makedirs(output_dir, exist_ok=True)
    
    srt_path = os.path.join(output_dir, 'subtitles.srt')
    
    with open(srt_path, 'w', encoding='utf-8') as f:
        for idx, subtitle in enumerate(subtitle_data, 1):
            # SRT format
            f.write(f"{idx}\n")
            f.write(f"{format_timestamp(subtitle['start'])} --> {format_timestamp(subtitle['end'])}\n")
            f.write(f"{subtitle['text']}\n\n")
    
    return srt_path

def format_timestamp(seconds: float) -> str:
    """Format seconds to SRT timestamp format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace('.', ',')

def create_subtitle_filter(style_settings: Dict[str, Any]) -> str:
    """Create FFmpeg subtitle filter string."""
    return (f"subtitles=filename='%s':"
            f"force_style='FontName={style_settings['font']},"
            f"FontSize={style_settings['font_size']},"
            f"PrimaryColour=&H{color_to_hex(style_settings['color'])},"
            f"OutlineColour=&H{color_to_hex(style_settings['outline_color'])},"
            f"BorderStyle=1,Outline={style_settings['outline_width']},"
            f"MarginV={style_settings['margin']}'")

def color_to_hex(color_name: str) -> str:
    """Convert color name to hex for FFmpeg."""
    colors = {
        'white': 'FFFFFF',
        'black': '000000',
        'red': '0000FF',
        'blue': 'FF0000',
        'green': '00FF00',
        'yellow': '00FFFF'
    }
    return colors.get(color_name.lower(), 'FFFFFF')

def create_transition_filter(transition_type: str, duration: float,
                           position: Optional[float] = None) -> str:
    """Create FFmpeg filter for transitions."""
    if transition_type == 'fade':
        return f"fade=t=in:d={duration}"
    elif transition_type == 'dissolve':
        return f"xfade=transition=dissolve:duration={duration}"
    elif transition_type == 'wipe':
        return f"xfade=transition=wipeleft:duration={duration}"
    else:
        return f"fade=t=in:d={duration}"  # Default to fade

def select_preview_segments(total_duration: float, preview_duration: float,
                          settings: Dict[str, Any]) -> List[Dict[str, float]]:
    """Select key segments for preview."""
    segments = []
    
    if settings.get('include_intro'):
        # First 5 seconds
        segments.append({'start': 0, 'duration': min(5, preview_duration / 3)})
    
    if settings.get('include_highlights'):
        # Middle section
        middle_start = total_duration * 0.4
        segments.append({
            'start': middle_start,
            'duration': min(10, preview_duration / 3)
        })
        
        # Climax (around 75% mark)
        climax_start = total_duration * 0.75
        segments.append({
            'start': climax_start,
            'duration': min(10, preview_duration / 3)
        })
    
    # Ensure we don't exceed preview duration
    total_segment_duration = sum(s['duration'] for s in segments)
    if total_segment_duration > preview_duration:
        scale_factor = preview_duration / total_segment_duration
        for segment in segments:
            segment['duration'] *= scale_factor
    
    return segments

def get_output_path(job_id: str, name: str, extension: str) -> str:
    """Generate output file path."""
    output_dir = f"/mnt/c/Users/holla/OneDrive/Desktop/CodeProjects/Evergreen/output/projects/{job_id}"
    os.makedirs(output_dir, exist_ok=True)
    return os.path.join(output_dir, f"{name}.{extension}")