"""
Voice synthesis tasks using ElevenLabs API.
"""

import os
import json
import tempfile
from typing import Dict, List, Any, Optional
from celery import Task, group, chain
from celery.utils.log import get_task_logger
from workers.celery_app import app
from workers.utils import (
    ProgressReporter, update_job_status, exponential_backoff_retry,
    TaskMetrics, chunk_list, get_redis_lock, release_redis_lock
)
from src.core.database.models import JobStatus
from src.services.elevenlabs_client import ElevenLabsClient

logger = get_task_logger(__name__)

class VoiceTask(Task):
    """Base class for voice synthesis tasks."""
    
    def __init__(self):
        self.client = None
        
    def __call__(self, *args, **kwargs):
        """Initialize ElevenLabs client on first call."""
        if self.client is None:
            self.client = ElevenLabsClient()
        return self.run(*args, **kwargs)

@app.task(bind=True, base=VoiceTask, name='workers.tasks.voice_tasks.synthesize_voice',
          max_retries=5, default_retry_delay=60)
def synthesize_voice(self, job_id: str, voice_script: Dict[str, Any],
                    output_settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Synthesize voice for dialogue using ElevenLabs API.
    
    Args:
        job_id: Unique job identifier
        voice_script: Prepared voice script with dialogue and settings
        output_settings: Optional output format settings
    
    Returns:
        Paths to generated audio files and metadata
    """
    logger.info(f"Starting voice synthesis for job {job_id}")
    progress = ProgressReporter(job_id, total_steps=100)
    metrics = TaskMetrics('synthesize_voice')
    
    try:
        update_job_status(job_id, JobStatus.PROCESSING)
        progress.update(5, "Initializing voice synthesis")
        
        # Default output settings
        output_settings = output_settings or {
            'format': 'mp3',
            'quality': 'high',
            'sample_rate': 44100
        }
        
        # Process each dialogue entry
        audio_files = []
        total_entries = len(voice_script['voice_script'])
        
        for idx, entry in enumerate(voice_script['voice_script']):
            progress_pct = 5 + (90 * idx // total_entries)
            progress.update(progress_pct, f"Synthesizing line {idx + 1}/{total_entries}")
            
            try:
                # Synthesize individual dialogue
                audio_result = synthesize_dialogue_line(
                    self.client,
                    entry,
                    output_settings,
                    job_id
                )
                audio_files.append(audio_result)
                
            except Exception as e:
                logger.error(f"Error synthesizing line {idx}: {str(e)}")
                # Continue with other lines, but mark this one as failed
                audio_files.append({
                    'id': entry['id'],
                    'status': 'failed',
                    'error': str(e)
                })
        
        # Compile results
        successful_files = [f for f in audio_files if f.get('status') != 'failed']
        result = {
            'job_id': job_id,
            'audio_files': audio_files,
            'success_count': len(successful_files),
            'failure_count': len(audio_files) - len(successful_files),
            'total_duration': sum(f.get('duration', 0) for f in successful_files),
            'output_format': output_settings['format']
        }
        
        progress.complete("Voice synthesis completed")
        metrics.record_execution(success=True, duration=progress.current_step)
        
        return result
        
    except Exception as e:
        logger.error(f"Voice synthesis failed for job {job_id}: {str(e)}")
        metrics.record_execution(success=False, duration=0)
        
        # Retry with exponential backoff
        countdown = 60 * (2 ** self.request.retries)
        raise self.retry(exc=e, countdown=countdown)

@app.task(bind=True, base=VoiceTask, name='workers.tasks.voice_tasks.batch_synthesize',
          max_retries=3)
def batch_synthesize(self, job_id: str, voice_scripts: List[Dict[str, Any]],
                    batch_size: int = 5) -> Dict[str, Any]:
    """
    Batch process multiple voice synthesis requests.
    
    Args:
        job_id: Unique job identifier
        voice_scripts: List of voice scripts to process
        batch_size: Number of concurrent synthesis tasks
    
    Returns:
        Aggregated results from all batches
    """
    logger.info(f"Starting batch voice synthesis for job {job_id}")
    progress = ProgressReporter(job_id, total_steps=100)
    
    try:
        # Split into batches
        batches = chunk_list(voice_scripts, batch_size)
        all_results = []
        
        for batch_idx, batch in enumerate(batches):
            progress_pct = (batch_idx / len(batches)) * 100
            progress.update(progress_pct, f"Processing batch {batch_idx + 1}/{len(batches)}")
            
            # Create a group of parallel tasks
            job = group(
                synthesize_voice.s(
                    f"{job_id}_batch{batch_idx}_item{idx}",
                    script
                ) for idx, script in enumerate(batch)
            )
            
            # Execute batch and wait for results
            batch_results = job.apply_async().get()
            all_results.extend(batch_results)
        
        # Aggregate results
        result = {
            'job_id': job_id,
            'total_processed': len(voice_scripts),
            'batch_count': len(batches),
            'results': all_results,
            'success_rate': calculate_success_rate(all_results)
        }
        
        progress.complete("Batch synthesis completed")
        return result
        
    except Exception as e:
        logger.error(f"Batch synthesis failed for job {job_id}: {str(e)}")
        raise self.retry(exc=e)

@app.task(bind=True, base=VoiceTask, name='workers.tasks.voice_tasks.clone_voice',
          max_retries=3)
def clone_voice(self, job_id: str, voice_sample_path: str, 
               voice_name: str, description: str = "") -> Dict[str, Any]:
    """
    Clone a voice from audio samples using ElevenLabs.
    
    Args:
        job_id: Unique job identifier
        voice_sample_path: Path to voice sample audio file
        voice_name: Name for the cloned voice
        description: Optional description
    
    Returns:
        Voice clone information including voice_id
    """
    logger.info(f"Starting voice cloning for job {job_id}")
    progress = ProgressReporter(job_id, total_steps=100)
    
    try:
        progress.update(10, "Validating voice sample")
        
        # Validate audio file
        if not os.path.exists(voice_sample_path):
            raise FileNotFoundError(f"Voice sample not found: {voice_sample_path}")
        
        progress.update(30, "Uploading voice sample")
        
        # Clone voice using ElevenLabs
        with exponential_backoff_retry(max_retries=3):
            voice_data = self.client.clone_voice(
                name=voice_name,
                files=[voice_sample_path],
                description=description
            )
        
        progress.update(80, "Voice clone created successfully")
        
        result = {
            'job_id': job_id,
            'voice_id': voice_data['voice_id'],
            'voice_name': voice_name,
            'status': 'created',
            'preview_url': voice_data.get('preview_url')
        }
        
        progress.complete("Voice cloning completed")
        return result
        
    except Exception as e:
        logger.error(f"Voice cloning failed for job {job_id}: {str(e)}")
        raise self.retry(exc=e)

@app.task(bind=True, name='workers.tasks.voice_tasks.generate_voice_preview',
          max_retries=3)
def generate_voice_preview(self, voice_id: str, preview_text: str,
                          voice_settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Generate a preview of a voice with sample text.
    
    Args:
        voice_id: ElevenLabs voice ID
        preview_text: Text to use for preview
        voice_settings: Optional voice settings
    
    Returns:
        Preview audio file path and metadata
    """
    logger.info(f"Generating voice preview for voice {voice_id}")
    
    try:
        client = ElevenLabsClient()
        
        # Default settings
        voice_settings = voice_settings or {
            'stability': 0.5,
            'similarity_boost': 0.5,
            'style': 0.0,
            'use_speaker_boost': True
        }
        
        # Generate preview
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
            audio_data = client.text_to_speech(
                text=preview_text,
                voice_id=voice_id,
                voice_settings=voice_settings
            )
            
            tmp_file.write(audio_data)
            preview_path = tmp_file.name
        
        return {
            'voice_id': voice_id,
            'preview_path': preview_path,
            'duration': estimate_audio_duration(preview_path),
            'settings_used': voice_settings
        }
        
    except Exception as e:
        logger.error(f"Voice preview generation failed: {str(e)}")
        raise

@app.task(bind=True, name='workers.tasks.voice_tasks.optimize_voice_settings',
          max_retries=2)
def optimize_voice_settings(self, job_id: str, voice_id: str,
                           sample_texts: List[str]) -> Dict[str, Any]:
    """
    Optimize voice settings for best quality.
    
    Args:
        job_id: Unique job identifier
        voice_id: ElevenLabs voice ID
        sample_texts: List of sample texts to test
    
    Returns:
        Optimized voice settings
    """
    logger.info(f"Optimizing voice settings for job {job_id}")
    progress = ProgressReporter(job_id, total_steps=100)
    
    try:
        client = ElevenLabsClient()
        
        # Test different setting combinations
        test_settings = [
            {'stability': 0.3, 'similarity_boost': 0.7},
            {'stability': 0.5, 'similarity_boost': 0.5},
            {'stability': 0.7, 'similarity_boost': 0.3},
            {'stability': 0.5, 'similarity_boost': 0.8, 'style': 0.2},
        ]
        
        best_settings = None
        best_score = 0
        
        for idx, settings in enumerate(test_settings):
            progress.update(20 + (60 * idx // len(test_settings)), 
                          f"Testing settings combination {idx + 1}")
            
            # Generate test audio
            test_results = []
            for text in sample_texts[:3]:  # Limit to 3 samples
                try:
                    audio = client.text_to_speech(
                        text=text,
                        voice_id=voice_id,
                        voice_settings=settings
                    )
                    
                    # Simple quality score based on file size and generation success
                    score = len(audio) / 1000  # Basic metric
                    test_results.append(score)
                except:
                    test_results.append(0)
            
            avg_score = sum(test_results) / len(test_results) if test_results else 0
            
            if avg_score > best_score:
                best_score = avg_score
                best_settings = settings
        
        result = {
            'job_id': job_id,
            'voice_id': voice_id,
            'optimized_settings': best_settings,
            'quality_score': best_score,
            'tests_performed': len(test_settings)
        }
        
        progress.complete("Voice optimization completed")
        return result
        
    except Exception as e:
        logger.error(f"Voice optimization failed: {str(e)}")
        raise self.retry(exc=e)

# Helper functions
def synthesize_dialogue_line(client: ElevenLabsClient, entry: Dict[str, Any],
                           output_settings: Dict[str, Any], job_id: str) -> Dict[str, Any]:
    """Synthesize a single dialogue line."""
    try:
        # Get voice settings
        voice_settings = entry.get('voice_settings', {})
        voice_id = voice_settings.get('voice_id', 'default')
        
        # Apply emotion adjustments
        emotion = entry.get('emotion', 'neutral')
        adjusted_settings = adjust_voice_for_emotion(voice_settings, emotion)
        
        # Generate audio
        audio_data = client.text_to_speech(
            text=entry['text'],
            voice_id=voice_id,
            voice_settings=adjusted_settings,
            output_format=output_settings.get('format', 'mp3')
        )
        
        # Save audio file
        output_path = save_audio_file(
            audio_data,
            job_id,
            entry['id'],
            output_settings['format']
        )
        
        return {
            'id': entry['id'],
            'character': entry['character'],
            'audio_path': output_path,
            'duration': entry['timing']['duration'],
            'status': 'success',
            'file_size': len(audio_data),
            'voice_id': voice_id,
            'emotion': emotion
        }
        
    except Exception as e:
        logger.error(f"Failed to synthesize dialogue {entry['id']}: {str(e)}")
        raise

def adjust_voice_for_emotion(base_settings: Dict[str, Any], emotion: str) -> Dict[str, Any]:
    """Adjust voice settings based on emotion."""
    settings = base_settings.copy()
    
    emotion_adjustments = {
        'excited': {'stability': 0.3, 'similarity_boost': 0.8, 'style': 0.3},
        'sad': {'stability': 0.7, 'similarity_boost': 0.4, 'style': 0.1},
        'angry': {'stability': 0.2, 'similarity_boost': 0.9, 'style': 0.4},
        'calm': {'stability': 0.8, 'similarity_boost': 0.5, 'style': 0.0},
        'questioning': {'stability': 0.5, 'similarity_boost': 0.6, 'style': 0.2},
    }
    
    if emotion in emotion_adjustments:
        settings.update(emotion_adjustments[emotion])
    
    return settings

def save_audio_file(audio_data: bytes, job_id: str, dialogue_id: str, 
                   format: str = 'mp3') -> str:
    """Save audio data to file."""
    output_dir = f"/mnt/c/Users/holla/OneDrive/Desktop/CodeProjects/Evergreen/output/projects/{job_id}/audio"
    os.makedirs(output_dir, exist_ok=True)
    
    file_path = os.path.join(output_dir, f"{dialogue_id}.{format}")
    
    with open(file_path, 'wb') as f:
        f.write(audio_data)
    
    return file_path

def estimate_audio_duration(file_path: str) -> float:
    """Estimate audio duration from file."""
    # This is a placeholder - in production, use a library like mutagen
    # to get actual audio duration
    file_size = os.path.getsize(file_path)
    # Rough estimate: 1MB = 1 minute for MP3 at 128kbps
    return (file_size / (128 * 1024 / 8)) / 60

def calculate_success_rate(results: List[Dict[str, Any]]) -> float:
    """Calculate success rate from batch results."""
    if not results:
        return 0.0
    
    successful = sum(1 for r in results if r.get('success_count', 0) > 0)
    return (successful / len(results)) * 100