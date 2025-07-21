"""
Script parsing and processing tasks for Celery workers.
"""

import os
import json
import re
from typing import Dict, List, Any, Optional
from celery import Task
from celery.utils.log import get_task_logger
from workers.celery_app import app
from workers.utils import (
    ProgressReporter, update_job_status, exponential_backoff_retry,
    task_with_db_update, TaskMetrics
)
from api.validators import JobStatus
from src.script_engine import ScriptParser, ScriptValidator

logger = get_task_logger(__name__)

class ScriptTask(Task):
    """Base class for script-related tasks with common functionality."""
    
    def __init__(self):
        self.parser = None
        self.validator = None
        
    def __call__(self, *args, **kwargs):
        """Initialize parser and validator on first call."""
        if self.parser is None:
            self.parser = ScriptParser()
        if self.validator is None:
            self.validator = ScriptValidator()
        return self.run(*args, **kwargs)

@app.task(bind=True, base=ScriptTask, name='workers.tasks.script_tasks.parse_script',
          max_retries=3, default_retry_delay=30)
def parse_script(self, job_id: str, script_content: str, 
                metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Parse a script and extract scenes, dialogue, and metadata.
    
    Args:
        job_id: Unique job identifier
        script_content: Raw script content to parse
        metadata: Optional metadata about the script
    
    Returns:
        Parsed script data with scenes, characters, and dialogue
    """
    logger.info(f"Starting script parsing for job {job_id}")
    progress = ProgressReporter(job_id, total_steps=100)
    metrics = TaskMetrics('parse_script')
    
    try:
        # Update job status
        update_job_status(job_id, JobStatus.PROCESSING)
        progress.update(10, "Validating script format")
        
        # Validate script format
        validation_result = self.validator.validate(script_content)
        if not validation_result['valid']:
            raise ValueError(f"Invalid script format: {validation_result['errors']}")
        
        progress.update(20, "Parsing script structure")
        
        # Parse the script
        parsed_data = self.parser.parse(script_content)
        
        # Extract key information
        progress.update(40, "Extracting scenes")
        scenes = extract_scenes(parsed_data)
        
        progress.update(60, "Extracting dialogue")
        dialogue = extract_dialogue(parsed_data)
        
        progress.update(80, "Analyzing characters")
        characters = analyze_characters(parsed_data)
        
        # Prepare result
        result = {
            'job_id': job_id,
            'scenes': scenes,
            'dialogue': dialogue,
            'characters': characters,
            'metadata': {
                'total_scenes': len(scenes),
                'total_dialogue_lines': len(dialogue),
                'total_characters': len(characters),
                'estimated_duration': estimate_duration(dialogue),
                **(metadata or {})
            }
        }
        
        progress.complete("Script parsing completed successfully")
        metrics.record_execution(success=True, duration=(progress.current_step / 10))
        
        return result
        
    except Exception as e:
        logger.error(f"Error parsing script for job {job_id}: {str(e)}")
        metrics.record_execution(success=False, duration=0)
        
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=30 * (2 ** self.request.retries))

@app.task(bind=True, name='workers.tasks.script_tasks.analyze_scene_requirements',
          max_retries=3, default_retry_delay=60)
def analyze_scene_requirements(self, job_id: str, scene_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze scene requirements for video generation.
    
    Args:
        job_id: Unique job identifier
        scene_data: Parsed scene data
    
    Returns:
        Scene requirements including visual elements, effects, and transitions
    """
    logger.info(f"Analyzing scene requirements for job {job_id}")
    progress = ProgressReporter(job_id, total_steps=100)
    
    try:
        progress.update(10, "Extracting visual elements")
        
        # Extract visual requirements
        visual_elements = extract_visual_elements(scene_data)
        
        progress.update(30, "Identifying required effects")
        effects = identify_effects(scene_data)
        
        progress.update(50, "Determining transitions")
        transitions = determine_transitions(scene_data)
        
        progress.update(70, "Analyzing mood and tone")
        mood_analysis = analyze_mood(scene_data)
        
        # Compile requirements
        requirements = {
            'job_id': job_id,
            'scene_id': scene_data.get('id'),
            'visual_elements': visual_elements,
            'effects': effects,
            'transitions': transitions,
            'mood': mood_analysis,
            'duration_estimate': scene_data.get('duration', 0),
            'complexity_score': calculate_complexity(visual_elements, effects)
        }
        
        progress.complete("Scene analysis completed")
        return requirements
        
    except Exception as e:
        logger.error(f"Error analyzing scene for job {job_id}: {str(e)}")
        raise self.retry(exc=e)

@app.task(bind=True, name='workers.tasks.script_tasks.prepare_voice_script',
          max_retries=3)
def prepare_voice_script(self, job_id: str, dialogue_data: List[Dict[str, Any]],
                        voice_settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Prepare dialogue for voice synthesis.
    
    Args:
        job_id: Unique job identifier
        dialogue_data: List of dialogue entries
        voice_settings: Optional voice synthesis settings
    
    Returns:
        Prepared voice script with timing and emotion markers
    """
    logger.info(f"Preparing voice script for job {job_id}")
    progress = ProgressReporter(job_id, total_steps=100)
    
    try:
        progress.update(10, "Processing dialogue entries")
        
        voice_script = []
        total_duration = 0
        
        for idx, entry in enumerate(dialogue_data):
            progress.update(10 + (80 * idx // len(dialogue_data)), 
                          f"Processing line {idx + 1}/{len(dialogue_data)}")
            
            # Process each dialogue line
            processed_entry = {
                'id': f"{job_id}_dialogue_{idx}",
                'character': entry.get('character', 'NARRATOR'),
                'text': clean_dialogue_text(entry['text']),
                'emotion': detect_emotion(entry['text']),
                'timing': {
                    'start': total_duration,
                    'duration': estimate_speech_duration(entry['text']),
                },
                'voice_settings': get_character_voice_settings(
                    entry.get('character'), 
                    voice_settings
                )
            }
            
            total_duration += processed_entry['timing']['duration']
            voice_script.append(processed_entry)
        
        result = {
            'job_id': job_id,
            'voice_script': voice_script,
            'total_duration': total_duration,
            'character_count': len(set(e['character'] for e in voice_script))
        }
        
        progress.complete("Voice script preparation completed")
        return result
        
    except Exception as e:
        logger.error(f"Error preparing voice script for job {job_id}: {str(e)}")
        raise self.retry(exc=e)

# Helper functions
def extract_scenes(parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract scene information from parsed script data."""
    scenes = []
    for scene in parsed_data.get('scenes', []):
        scenes.append({
            'id': scene.get('id'),
            'number': scene.get('number'),
            'location': scene.get('location'),
            'time': scene.get('time'),
            'description': scene.get('description'),
            'characters': scene.get('characters', []),
            'action': scene.get('action', []),
            'dialogue_count': len(scene.get('dialogue', []))
        })
    return scenes

def extract_dialogue(parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract dialogue from parsed script data."""
    dialogue = []
    for scene in parsed_data.get('scenes', []):
        for line in scene.get('dialogue', []):
            dialogue.append({
                'scene_id': scene.get('id'),
                'character': line.get('character'),
                'text': line.get('text'),
                'direction': line.get('direction'),
                'emotion': line.get('emotion')
            })
    return dialogue

def analyze_characters(parsed_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Analyze character information from script."""
    characters = {}
    
    for scene in parsed_data.get('scenes', []):
        for line in scene.get('dialogue', []):
            char_name = line.get('character')
            if char_name:
                if char_name not in characters:
                    characters[char_name] = {
                        'name': char_name,
                        'dialogue_count': 0,
                        'scenes': set(),
                        'total_words': 0
                    }
                
                characters[char_name]['dialogue_count'] += 1
                characters[char_name]['scenes'].add(scene.get('id'))
                characters[char_name]['total_words'] += len(line.get('text', '').split())
    
    # Convert sets to lists for JSON serialization
    for char in characters.values():
        char['scenes'] = list(char['scenes'])
        char['prominence_score'] = char['dialogue_count'] / len(parsed_data.get('scenes', []))
    
    return characters

def estimate_duration(dialogue: List[Dict[str, Any]]) -> float:
    """Estimate total duration based on dialogue."""
    # Rough estimate: 150 words per minute average speaking rate
    total_words = sum(len(d.get('text', '').split()) for d in dialogue)
    return (total_words / 150) * 60  # Convert to seconds

def extract_visual_elements(scene_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract visual elements from scene description."""
    description = scene_data.get('description', '')
    elements = []
    
    # Pattern matching for common visual elements
    patterns = {
        'characters': r'(?:enters?|exits?|stands?|sits?|walks?)\s+(\w+)',
        'objects': r'(?:holds?|picks? up|drops?|throws?)\s+(?:a |an |the )?(\w+)',
        'settings': r'(?:INT\.|EXT\.|INTERIOR|EXTERIOR)\s+([^-\n]+)',
    }
    
    for element_type, pattern in patterns.items():
        matches = re.findall(pattern, description, re.IGNORECASE)
        for match in matches:
            elements.append({
                'type': element_type,
                'value': match.strip(),
                'context': description
            })
    
    return elements

def identify_effects(scene_data: Dict[str, Any]) -> List[Dict[str, str]]:
    """Identify required visual effects from scene."""
    effects = []
    description = scene_data.get('description', '').lower()
    
    # Common effect keywords
    effect_keywords = {
        'fade': ['fade in', 'fade out', 'fade to'],
        'transition': ['cut to', 'dissolve to', 'wipe to'],
        'lighting': ['dim', 'bright', 'dark', 'shadows'],
        'weather': ['rain', 'snow', 'fog', 'storm'],
        'special': ['explosion', 'magic', 'transform', 'disappear']
    }
    
    for effect_type, keywords in effect_keywords.items():
        for keyword in keywords:
            if keyword in description:
                effects.append({
                    'type': effect_type,
                    'keyword': keyword,
                    'intensity': 'medium'  # Default intensity
                })
    
    return effects

def determine_transitions(scene_data: Dict[str, Any]) -> Dict[str, str]:
    """Determine scene transitions."""
    # Default transitions based on scene context
    return {
        'in': scene_data.get('transition_in', 'fade_in'),
        'out': scene_data.get('transition_out', 'cut'),
        'duration': 1.0  # Default 1 second transition
    }

def analyze_mood(scene_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze mood and tone of the scene."""
    description = scene_data.get('description', '').lower()
    dialogue = ' '.join([d.get('text', '') for d in scene_data.get('dialogue', [])])
    
    # Simple mood detection based on keywords
    moods = {
        'tense': ['tension', 'nervous', 'anxious', 'worried'],
        'happy': ['joy', 'happy', 'laugh', 'smile', 'celebrate'],
        'sad': ['cry', 'tears', 'grief', 'sorrow', 'loss'],
        'action': ['run', 'fight', 'chase', 'escape', 'battle'],
        'romantic': ['love', 'kiss', 'embrace', 'heart', 'passion']
    }
    
    detected_moods = []
    for mood, keywords in moods.items():
        if any(keyword in description or keyword in dialogue for keyword in keywords):
            detected_moods.append(mood)
    
    return {
        'primary': detected_moods[0] if detected_moods else 'neutral',
        'secondary': detected_moods[1:],
        'intensity': len(detected_moods)
    }

def calculate_complexity(visual_elements: List, effects: List) -> float:
    """Calculate scene complexity score."""
    # Simple complexity calculation
    base_score = len(visual_elements) * 0.1 + len(effects) * 0.2
    return min(base_score, 1.0)  # Cap at 1.0

def clean_dialogue_text(text: str) -> str:
    """Clean dialogue text for voice synthesis."""
    # Remove parenthetical directions
    text = re.sub(r'\([^)]*\)', '', text)
    # Remove excessive whitespace
    text = ' '.join(text.split())
    # Remove special characters that might confuse TTS
    text = re.sub(r'[^\w\s\',.\?!-]', '', text)
    return text.strip()

def detect_emotion(text: str) -> str:
    """Detect emotion from dialogue text."""
    # Simple emotion detection based on punctuation and keywords
    if '!' in text:
        return 'excited'
    elif '?' in text:
        return 'questioning'
    elif any(word in text.lower() for word in ['sorry', 'apologize']):
        return 'apologetic'
    elif any(word in text.lower() for word in ['angry', 'furious', 'mad']):
        return 'angry'
    return 'neutral'

def estimate_speech_duration(text: str) -> float:
    """Estimate speech duration in seconds."""
    # Average speaking rate: 150 words per minute
    word_count = len(text.split())
    return (word_count / 150) * 60

def get_character_voice_settings(character: str, 
                               voice_settings: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Get voice settings for a specific character."""
    if not voice_settings:
        return {'voice_id': 'default', 'stability': 0.5, 'similarity_boost': 0.5}
    
    return voice_settings.get(character, voice_settings.get('default', {
        'voice_id': 'default',
        'stability': 0.5,
        'similarity_boost': 0.5
    }))