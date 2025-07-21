"""
Video generation tasks using Runway API (or similar services).
"""

import os
import json
import time
import tempfile
from typing import Dict, List, Any, Optional
from celery import Task, chord
from celery.utils.log import get_task_logger
from workers.celery_app import app
from workers.utils import (
    ProgressReporter, update_job_status, exponential_backoff_retry,
    TaskMetrics, get_redis_lock, release_redis_lock
)
from src.core.database.models import JobStatus
from src.services.runway_client import RunwayClient

logger = get_task_logger(__name__)

class VideoTask(Task):
    """Base class for video generation tasks."""
    
    def __init__(self):
        self.client = None
        
    def __call__(self, *args, **kwargs):
        """Initialize Runway client on first call."""
        if self.client is None:
            self.client = RunwayClient()
        return self.run(*args, **kwargs)

@app.task(bind=True, base=VideoTask, name='workers.tasks.video_tasks.generate_video',
          max_retries=3, default_retry_delay=120, time_limit=3600, soft_time_limit=3000)
def generate_video(self, job_id: str, scene_data: Dict[str, Any],
                  generation_settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Generate video for a scene using AI video generation service.
    
    Args:
        job_id: Unique job identifier
        scene_data: Scene requirements and metadata
        generation_settings: Optional generation settings
    
    Returns:
        Generated video file path and metadata
    """
    logger.info(f"Starting video generation for job {job_id}")
    progress = ProgressReporter(job_id, total_steps=100)
    metrics = TaskMetrics('generate_video')
    
    try:
        update_job_status(job_id, JobStatus.PROCESSING)
        progress.update(5, "Initializing video generation")
        
        # Default generation settings
        generation_settings = generation_settings or {
            'resolution': '1920x1080',
            'fps': 30,
            'duration': scene_data.get('duration_estimate', 10),
            'style': 'cinematic',
            'quality': 'high'
        }
        
        # Prepare prompts from scene data
        progress.update(10, "Preparing generation prompts")
        prompts = prepare_video_prompts(scene_data)
        
        # Generate video segments
        video_segments = []
        total_prompts = len(prompts)
        
        for idx, prompt in enumerate(prompts):
            progress_pct = 10 + (80 * idx // total_prompts)
            progress.update(progress_pct, f"Generating segment {idx + 1}/{total_prompts}")
            
            try:
                # Generate video segment
                segment_result = generate_video_segment(
                    self.client,
                    prompt,
                    generation_settings,
                    job_id,
                    idx
                )
                video_segments.append(segment_result)
                
                # Poll for completion if async
                if segment_result.get('status') == 'processing':
                    segment_result = wait_for_video_completion(
                        self.client,
                        segment_result['generation_id'],
                        progress,
                        progress_pct
                    )
                    video_segments[-1] = segment_result
                    
            except Exception as e:
                logger.error(f"Error generating segment {idx}: {str(e)}")
                video_segments.append({
                    'id': f"segment_{idx}",
                    'status': 'failed',
                    'error': str(e)
                })
        
        # Compile results
        successful_segments = [s for s in video_segments if s.get('status') == 'completed']
        
        result = {
            'job_id': job_id,
            'scene_id': scene_data.get('scene_id'),
            'video_segments': video_segments,
            'success_count': len(successful_segments),
            'failure_count': len(video_segments) - len(successful_segments),
            'total_duration': sum(s.get('duration', 0) for s in successful_segments),
            'generation_settings': generation_settings
        }
        
        progress.complete("Video generation completed")
        metrics.record_execution(success=True, duration=progress.current_step)
        
        return result
        
    except Exception as e:
        logger.error(f"Video generation failed for job {job_id}: {str(e)}")
        metrics.record_execution(success=False, duration=0)
        
        # Check if we hit the soft time limit
        if 'SoftTimeLimitExceeded' in str(e):
            logger.warning(f"Video generation timed out for job {job_id}")
            update_job_status(job_id, JobStatus.FAILED, 
                            error_message="Video generation timed out")
            return {
                'job_id': job_id,
                'status': 'timeout',
                'error': 'Generation exceeded time limit'
            }
        
        # Retry with exponential backoff
        countdown = 120 * (2 ** self.request.retries)
        raise self.retry(exc=e, countdown=countdown)

@app.task(bind=True, base=VideoTask, name='workers.tasks.video_tasks.generate_transition',
          max_retries=3)
def generate_transition(self, job_id: str, from_scene: Dict[str, Any],
                       to_scene: Dict[str, Any], transition_type: str = 'dissolve') -> Dict[str, Any]:
    """
    Generate transition video between scenes.
    
    Args:
        job_id: Unique job identifier
        from_scene: Source scene data
        to_scene: Target scene data
        transition_type: Type of transition
    
    Returns:
        Transition video file path and metadata
    """
    logger.info(f"Generating {transition_type} transition for job {job_id}")
    progress = ProgressReporter(job_id, total_steps=100)
    
    try:
        progress.update(10, "Preparing transition parameters")
        
        # Prepare transition settings
        transition_settings = {
            'type': transition_type,
            'duration': 1.0,  # Default 1 second
            'from_frame': from_scene.get('last_frame'),
            'to_frame': to_scene.get('first_frame')
        }
        
        progress.update(30, "Generating transition effect")
        
        # Generate transition using video service
        with exponential_backoff_retry(max_retries=3):
            transition_result = self.client.generate_transition(
                from_video=from_scene.get('video_path'),
                to_video=to_scene.get('video_path'),
                transition_settings=transition_settings
            )
        
        progress.update(80, "Saving transition video")
        
        # Save transition video
        output_path = save_video_file(
            transition_result['video_data'],
            job_id,
            f"transition_{from_scene['id']}_{to_scene['id']}",
            'mp4'
        )
        
        result = {
            'job_id': job_id,
            'transition_path': output_path,
            'duration': transition_settings['duration'],
            'type': transition_type,
            'from_scene': from_scene['id'],
            'to_scene': to_scene['id']
        }
        
        progress.complete("Transition generation completed")
        return result
        
    except Exception as e:
        logger.error(f"Transition generation failed: {str(e)}")
        raise self.retry(exc=e)

@app.task(bind=True, name='workers.tasks.video_tasks.apply_video_effects',
          max_retries=3)
def apply_video_effects(self, job_id: str, video_path: str,
                       effects: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Apply post-processing effects to video.
    
    Args:
        job_id: Unique job identifier
        video_path: Path to source video
        effects: List of effects to apply
    
    Returns:
        Processed video file path and metadata
    """
    logger.info(f"Applying effects to video for job {job_id}")
    progress = ProgressReporter(job_id, total_steps=100)
    
    try:
        client = RunwayClient()
        
        # Process each effect
        processed_path = video_path
        applied_effects = []
        
        for idx, effect in enumerate(effects):
            progress_pct = (idx / len(effects)) * 90
            progress.update(progress_pct, f"Applying {effect['type']} effect")
            
            try:
                # Apply effect
                effect_result = client.apply_effect(
                    video_path=processed_path,
                    effect_type=effect['type'],
                    parameters=effect.get('parameters', {})
                )
                
                processed_path = effect_result['output_path']
                applied_effects.append({
                    'type': effect['type'],
                    'status': 'applied',
                    'parameters': effect.get('parameters', {})
                })
                
            except Exception as e:
                logger.error(f"Failed to apply {effect['type']} effect: {str(e)}")
                applied_effects.append({
                    'type': effect['type'],
                    'status': 'failed',
                    'error': str(e)
                })
        
        result = {
            'job_id': job_id,
            'original_path': video_path,
            'processed_path': processed_path,
            'applied_effects': applied_effects,
            'success_count': sum(1 for e in applied_effects if e['status'] == 'applied')
        }
        
        progress.complete("Effects application completed")
        return result
        
    except Exception as e:
        logger.error(f"Effect application failed: {str(e)}")
        raise self.retry(exc=e)

@app.task(bind=True, name='workers.tasks.video_tasks.generate_thumbnail',
          max_retries=2)
def generate_thumbnail(self, job_id: str, video_path: str,
                      timestamp: float = None) -> Dict[str, Any]:
    """
    Generate thumbnail image from video.
    
    Args:
        job_id: Unique job identifier
        video_path: Path to video file
        timestamp: Timestamp in seconds (None for auto-select)
    
    Returns:
        Thumbnail image path and metadata
    """
    logger.info(f"Generating thumbnail for job {job_id}")
    
    try:
        client = RunwayClient()
        
        # Auto-select timestamp if not provided
        if timestamp is None:
            # Select frame at 10% of video duration
            video_info = client.get_video_info(video_path)
            timestamp = video_info['duration'] * 0.1
        
        # Generate thumbnail
        thumbnail_data = client.extract_frame(
            video_path=video_path,
            timestamp=timestamp,
            format='jpg'
        )
        
        # Save thumbnail
        output_dir = os.path.dirname(video_path)
        thumbnail_path = os.path.join(output_dir, f"thumbnail_{job_id}.jpg")
        
        with open(thumbnail_path, 'wb') as f:
            f.write(thumbnail_data)
        
        return {
            'job_id': job_id,
            'thumbnail_path': thumbnail_path,
            'timestamp': timestamp,
            'file_size': len(thumbnail_data)
        }
        
    except Exception as e:
        logger.error(f"Thumbnail generation failed: {str(e)}")
        raise

@app.task(bind=True, name='workers.tasks.video_tasks.upscale_video',
          max_retries=2, time_limit=7200)
def upscale_video(self, job_id: str, video_path: str,
                 target_resolution: str = '4K') -> Dict[str, Any]:
    """
    Upscale video to higher resolution using AI.
    
    Args:
        job_id: Unique job identifier
        video_path: Path to source video
        target_resolution: Target resolution (e.g., '4K', '1080p')
    
    Returns:
        Upscaled video file path and metadata
    """
    logger.info(f"Upscaling video to {target_resolution} for job {job_id}")
    progress = ProgressReporter(job_id, total_steps=100)
    
    try:
        client = RunwayClient()
        progress.update(10, "Analyzing source video")
        
        # Get source video info
        video_info = client.get_video_info(video_path)
        source_resolution = f"{video_info['width']}x{video_info['height']}"
        
        # Map target resolution
        resolution_map = {
            '4K': '3840x2160',
            '1080p': '1920x1080',
            '720p': '1280x720'
        }
        target_res = resolution_map.get(target_resolution, target_resolution)
        
        progress.update(20, f"Upscaling from {source_resolution} to {target_res}")
        
        # Start upscaling process
        upscale_job = client.upscale_video(
            video_path=video_path,
            target_resolution=target_res,
            enhancement_settings={
                'denoise': True,
                'sharpen': True,
                'enhance_details': True
            }
        )
        
        # Poll for completion
        upscaled_path = wait_for_processing(
            client,
            upscale_job['job_id'],
            progress,
            start_progress=20,
            end_progress=90
        )
        
        result = {
            'job_id': job_id,
            'original_path': video_path,
            'upscaled_path': upscaled_path,
            'source_resolution': source_resolution,
            'target_resolution': target_res,
            'file_size_increase': os.path.getsize(upscaled_path) / os.path.getsize(video_path)
        }
        
        progress.complete("Video upscaling completed")
        return result
        
    except Exception as e:
        logger.error(f"Video upscaling failed: {str(e)}")
        raise self.retry(exc=e)

# Helper functions
def prepare_video_prompts(scene_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Prepare video generation prompts from scene data."""
    prompts = []
    
    # Base prompt from scene description
    base_description = scene_data.get('description', '')
    visual_elements = scene_data.get('visual_elements', [])
    mood = scene_data.get('mood', {})
    
    # Create prompts for different shots in the scene
    # This is simplified - in production, this would be more sophisticated
    
    # Establishing shot
    prompts.append({
        'type': 'establishing',
        'text': f"Wide shot of {scene_data.get('location', 'scene')}. {mood.get('primary', 'neutral')} mood. Cinematic lighting.",
        'duration': 3.0,
        'camera_movement': 'slow_pan'
    })
    
    # Character/action shots
    for element in visual_elements:
        if element['type'] == 'characters':
            prompts.append({
                'type': 'character',
                'text': f"Medium shot of {element['value']}. {base_description[:100]}",
                'duration': 2.0,
                'camera_movement': 'static'
            })
    
    # Detail shots
    for element in visual_elements:
        if element['type'] == 'objects':
            prompts.append({
                'type': 'detail',
                'text': f"Close-up of {element['value']}. Sharp focus, shallow depth of field.",
                'duration': 1.5,
                'camera_movement': 'slow_zoom'
            })
    
    return prompts

def generate_video_segment(client: RunwayClient, prompt: Dict[str, Any],
                         settings: Dict[str, Any], job_id: str, segment_idx: int) -> Dict[str, Any]:
    """Generate a single video segment."""
    try:
        # Prepare generation request
        request_params = {
            'prompt': prompt['text'],
            'duration': prompt.get('duration', 3.0),
            'resolution': settings['resolution'],
            'fps': settings['fps'],
            'style': settings.get('style', 'cinematic'),
            'camera_movement': prompt.get('camera_movement', 'static'),
            'seed': None  # For reproducibility if needed
        }
        
        # Submit generation request
        generation_result = client.generate_video(**request_params)
        
        return {
            'id': f"{job_id}_segment_{segment_idx}",
            'generation_id': generation_result.get('id'),
            'status': generation_result.get('status', 'processing'),
            'prompt': prompt['text'],
            'duration': prompt['duration'],
            'type': prompt['type']
        }
        
    except Exception as e:
        logger.error(f"Failed to generate video segment: {str(e)}")
        raise

def wait_for_video_completion(client: RunwayClient, generation_id: str,
                            progress: ProgressReporter, base_progress: int) -> Dict[str, Any]:
    """Poll for video generation completion."""
    max_wait = 600  # 10 minutes
    poll_interval = 5  # 5 seconds
    elapsed = 0
    
    while elapsed < max_wait:
        try:
            # Check generation status
            status = client.get_generation_status(generation_id)
            
            if status['status'] == 'completed':
                # Download video
                video_data = client.download_video(status['video_url'])
                video_path = save_video_file(
                    video_data,
                    generation_id.split('_')[0],  # job_id
                    generation_id,
                    'mp4'
                )
                
                return {
                    'id': generation_id,
                    'status': 'completed',
                    'video_path': video_path,
                    'duration': status.get('duration', 0),
                    'file_size': len(video_data)
                }
                
            elif status['status'] == 'failed':
                return {
                    'id': generation_id,
                    'status': 'failed',
                    'error': status.get('error', 'Unknown error')
                }
            
            # Update progress
            completion_pct = status.get('progress', 0)
            progress_update = base_progress + (10 * completion_pct / 100)
            progress.update(progress_update, f"Generating video... {completion_pct}%")
            
        except Exception as e:
            logger.error(f"Error checking generation status: {str(e)}")
        
        time.sleep(poll_interval)
        elapsed += poll_interval
    
    # Timeout
    return {
        'id': generation_id,
        'status': 'timeout',
        'error': f'Generation timed out after {max_wait} seconds'
    }

def wait_for_processing(client: RunwayClient, job_id: str, progress: ProgressReporter,
                       start_progress: int = 0, end_progress: int = 100) -> str:
    """Generic wait function for async processing jobs."""
    max_wait = 1800  # 30 minutes
    poll_interval = 10
    elapsed = 0
    
    while elapsed < max_wait:
        try:
            status = client.get_job_status(job_id)
            
            if status['status'] == 'completed':
                return status['output_path']
            
            elif status['status'] == 'failed':
                raise Exception(f"Processing failed: {status.get('error', 'Unknown error')}")
            
            # Update progress
            job_progress = status.get('progress', 0)
            current_progress = start_progress + ((end_progress - start_progress) * job_progress / 100)
            progress.update(current_progress, f"Processing... {job_progress}%")
            
        except Exception as e:
            logger.error(f"Error checking job status: {str(e)}")
            raise
        
        time.sleep(poll_interval)
        elapsed += poll_interval
    
    raise Exception(f"Processing timed out after {max_wait} seconds")

def save_video_file(video_data: bytes, job_id: str, video_id: str,
                   format: str = 'mp4') -> str:
    """Save video data to file."""
    output_dir = f"/mnt/c/Users/holla/OneDrive/Desktop/CodeProjects/Evergreen/output/projects/{job_id}/video"
    os.makedirs(output_dir, exist_ok=True)
    
    file_path = os.path.join(output_dir, f"{video_id}.{format}")
    
    with open(file_path, 'wb') as f:
        f.write(video_data)
    
    return file_path