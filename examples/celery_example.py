#!/usr/bin/env python3
"""
Example script demonstrating how to use Celery tasks for video generation.
"""

import os
import sys
import time
import json
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workers.tasks.script_tasks import parse_script, analyze_scene_requirements, prepare_voice_script
from workers.tasks.voice_tasks import synthesize_voice
from workers.tasks.video_tasks import generate_video
from workers.tasks.assembly_tasks import assemble_final_video
from workers.utils import redis_client

def get_progress(job_id: str):
    """Get current progress for a job."""
    progress_key = f"job:progress:{job_id}"
    progress_data = redis_client.get(progress_key)
    if progress_data:
        return json.loads(progress_data)
    return None

def wait_for_task(task, job_id: str, task_name: str):
    """Wait for a task to complete and show progress."""
    print(f"\n{task_name} started...")
    
    while not task.ready():
        progress = get_progress(job_id)
        if progress:
            print(f"\r{task_name}: {progress['percentage']:.1f}% - {progress['message']}", end='', flush=True)
        time.sleep(1)
    
    if task.successful():
        print(f"\n{task_name} completed successfully!")
        return task.result
    else:
        print(f"\n{task_name} failed: {task.info}")
        raise Exception(f"{task_name} failed")

def main():
    """Run example video generation pipeline."""
    
    # Example script content
    script_content = """
    FADE IN:
    
    INT. COFFEE SHOP - DAY
    
    A cozy coffee shop with warm lighting. SARAH (30s, writer) sits at a corner table with her laptop.
    
    JOHN (35, businessman) enters, looking around nervously.
    
    SARAH
    (looking up)
    John? Is that you?
    
    JOHN
    (surprised)
    Sarah! I can't believe it's really you.
    
    They share an awkward moment before John approaches.
    
    SARAH
    It's been... what, five years?
    
    JOHN
    (sitting down)
    Five years, three months, and twelve days. But who's counting?
    
    Sarah laughs, the tension breaking.
    
    FADE OUT.
    """
    
    # Generate unique job ID
    job_id = f"demo_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    print(f"Starting video generation pipeline for job: {job_id}")
    
    try:
        # Step 1: Parse the script
        parse_task = parse_script.delay(
            job_id=job_id,
            script_content=script_content,
            metadata={"title": "Coffee Shop Reunion", "genre": "Drama"}
        )
        
        parsed_result = wait_for_task(parse_task, job_id, "Script parsing")
        print(f"Found {len(parsed_result['scenes'])} scenes and {len(parsed_result['characters'])} characters")
        
        # Step 2: Analyze scene requirements
        scene_tasks = []
        for scene in parsed_result['scenes']:
            task = analyze_scene_requirements.delay(
                job_id=f"{job_id}_scene_{scene['id']}",
                scene_data=scene
            )
            scene_tasks.append(task)
        
        print(f"\nAnalyzing {len(scene_tasks)} scenes...")
        scene_requirements = []
        for i, task in enumerate(scene_tasks):
            result = wait_for_task(task, f"{job_id}_scene_{i}", f"Scene {i+1} analysis")
            scene_requirements.append(result)
        
        # Step 3: Prepare voice script
        voice_prep_task = prepare_voice_script.delay(
            job_id=f"{job_id}_voice_prep",
            dialogue_data=parsed_result['dialogue'],
            voice_settings={
                "SARAH": {"voice_id": "female_1", "stability": 0.7},
                "JOHN": {"voice_id": "male_1", "stability": 0.6}
            }
        )
        
        voice_script = wait_for_task(voice_prep_task, f"{job_id}_voice_prep", "Voice script preparation")
        print(f"Prepared {len(voice_script['voice_script'])} dialogue lines")
        
        # Step 4: Synthesize voices
        voice_task = synthesize_voice.delay(
            job_id=f"{job_id}_voice",
            voice_script=voice_script
        )
        
        voice_result = wait_for_task(voice_task, f"{job_id}_voice", "Voice synthesis")
        print(f"Synthesized {voice_result['success_count']} audio files")
        
        # Step 5: Generate video segments
        video_tasks = []
        for req in scene_requirements:
            task = generate_video.delay(
                job_id=f"{job_id}_video_{req['scene_id']}",
                scene_data=req,
                generation_settings={
                    "resolution": "1920x1080",
                    "fps": 30,
                    "style": "cinematic"
                }
            )
            video_tasks.append(task)
        
        print(f"\nGenerating {len(video_tasks)} video segments...")
        video_segments = []
        for i, task in enumerate(video_tasks):
            result = wait_for_task(task, f"{job_id}_video_{i}", f"Video segment {i+1}")
            video_segments.extend(result['video_segments'])
        
        # Step 6: Assemble final video
        assembly_task = assemble_final_video.delay(
            job_id=f"{job_id}_final",
            assembly_data={
                "video_segments": video_segments,
                "audio_files": voice_result['audio_files'],
                "transitions": []
            },
            output_settings={
                "format": "mp4",
                "quality": "high",
                "resolution": "1920x1080"
            }
        )
        
        final_result = wait_for_task(assembly_task, f"{job_id}_final", "Final video assembly")
        
        print("\n" + "="*50)
        print("VIDEO GENERATION COMPLETE!")
        print("="*50)
        print(f"Output file: {final_result['final_video_path']}")
        print(f"Duration: {final_result['duration']:.1f} seconds")
        print(f"Resolution: {final_result['resolution']}")
        print(f"File size: {final_result['file_size'] / (1024*1024):.1f} MB")
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()