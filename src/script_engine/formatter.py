"""
Script formatter for converting parsed scripts to various output formats.
"""

from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
import re
import logging
from .parser import ParsedScript, Scene, SceneElement, Narrative, Dialogue, SceneDescription

logger = logging.getLogger(__name__)


@dataclass
class FormatOptions:
    """Options for formatting output."""
    include_timing: bool = True
    include_metadata: bool = True
    include_visual_cues: bool = True
    include_speaker_directions: bool = True
    max_line_length: int = 80
    time_format: str = "seconds"  # 'seconds', 'timecode', 'minutes'


class ScriptFormatter:
    """Formats parsed scripts for different output formats."""
    
    def __init__(self, options: Optional[FormatOptions] = None):
        """
        Initialize the formatter.
        
        Args:
            options: Formatting options
        """
        self.options = options or FormatOptions()
    
    def format_for_voice_synthesis(self, script: ParsedScript) -> List[Dict[str, Any]]:
        """
        Format script for voice synthesis services.
        
        Args:
            script: Parsed script data
            
        Returns:
            List of voice synthesis segments
        """
        segments = []
        segment_id = 0
        
        for scene in script.scenes:
            for element in scene.elements:
                if isinstance(element, Narrative):
                    segment = {
                        'id': f"segment_{segment_id}",
                        'type': 'narration',
                        'text': self._clean_text_for_speech(element.content),
                        'voice': 'narrator',
                        'scene_id': scene.id,
                        'timing': {
                            'estimated_duration': element.timing_estimate,
                            'start_time': None  # To be filled during assembly
                        }
                    }
                    
                    if element.emotional_tone and self.options.include_metadata:
                        segment['emotion'] = element.emotional_tone
                    
                    segments.append(segment)
                    segment_id += 1
                    
                elif isinstance(element, Dialogue):
                    segment = {
                        'id': f"segment_{segment_id}",
                        'type': 'dialogue',
                        'text': self._clean_text_for_speech(element.content),
                        'voice': self._normalize_speaker_name(element.speaker),
                        'scene_id': scene.id,
                        'timing': {
                            'estimated_duration': element.timing_estimate,
                            'start_time': None
                        }
                    }
                    
                    if element.direction and self.options.include_speaker_directions:
                        segment['direction'] = element.direction
                    
                    segments.append(segment)
                    segment_id += 1
        
        return segments
    
    def format_for_visual_generation(self, script: ParsedScript) -> List[Dict[str, Any]]:
        """
        Format script for visual generation services.
        
        Args:
            script: Parsed script data
            
        Returns:
            List of visual generation prompts
        """
        visual_prompts = []
        prompt_id = 0
        
        for scene in script.scenes:
            # Create scene establishing shot
            scene_prompt = {
                'id': f"visual_{prompt_id}",
                'type': 'establishing_shot',
                'scene_id': scene.id,
                'timing': {
                    'start_time': None,
                    'duration': 3.0  # Default establishing shot duration
                }
            }
            
            # Build prompt from scene elements
            prompt_elements = []
            
            # Add location/setting from scene description
            for element in scene.elements:
                if isinstance(element, SceneDescription):
                    if element.location:
                        prompt_elements.append(f"Location: {element.location}")
                    if element.time_of_day:
                        prompt_elements.append(f"Time: {element.time_of_day}")
                    break
            
            # Add visual cues from narratives
            if self.options.include_visual_cues:
                for visual_cue in scene.visual_prompts[:3]:  # Limit to top 3
                    prompt_elements.append(visual_cue)
            
            # Determine mood/style
            mood = self._determine_scene_mood(scene)
            if mood:
                prompt_elements.append(f"Mood: {mood}")
            
            scene_prompt['prompt'] = self._create_visual_prompt(prompt_elements)
            scene_prompt['style'] = self._determine_visual_style(script, mood)
            
            visual_prompts.append(scene_prompt)
            prompt_id += 1
            
            # Create additional prompts for key moments
            key_visuals = self._extract_key_visual_moments(scene)
            for visual in key_visuals:
                moment_prompt = {
                    'id': f"visual_{prompt_id}",
                    'type': 'key_moment',
                    'scene_id': scene.id,
                    'prompt': visual['prompt'],
                    'style': visual.get('style', scene_prompt['style']),
                    'timing': {
                        'start_time': None,
                        'duration': visual.get('duration', 2.0)
                    }
                }
                visual_prompts.append(moment_prompt)
                prompt_id += 1
        
        return visual_prompts
    
    def format_as_subtitles(self, script: ParsedScript, format_type: str = 'srt') -> str:
        """
        Format script as subtitles.
        
        Args:
            script: Parsed script data
            format_type: Subtitle format ('srt', 'vtt', 'ass')
            
        Returns:
            Formatted subtitle content
        """
        if format_type == 'srt':
            return self._format_as_srt(script)
        elif format_type == 'vtt':
            return self._format_as_vtt(script)
        elif format_type == 'ass':
            return self._format_as_ass(script)
        else:
            raise ValueError(f"Unsupported subtitle format: {format_type}")
    
    def format_as_screenplay(self, script: ParsedScript) -> str:
        """
        Format script in traditional screenplay format.
        
        Args:
            script: Parsed script data
            
        Returns:
            Screenplay formatted text
        """
        output = []
        
        # Add title page
        if script.metadata.title:
            output.append(script.metadata.title.upper())
            output.append("")
            
            if script.metadata.reporter:
                output.append(f"by {script.metadata.reporter}")
                output.append("")
            
            output.append("")
            output.append("")
        
        # Add scenes
        for scene in script.scenes:
            # Scene heading
            scene_heading = self._format_scene_heading(scene)
            if scene_heading:
                output.append(scene_heading)
                output.append("")
            
            # Scene elements
            for element in scene.elements:
                if isinstance(element, SceneDescription) and element.content:
                    # Action lines
                    wrapped = self._wrap_text(element.content, self.options.max_line_length)
                    output.extend(wrapped)
                    output.append("")
                    
                elif isinstance(element, Narrative):
                    # Action/description
                    wrapped = self._wrap_text(element.content, self.options.max_line_length)
                    output.extend(wrapped)
                    output.append("")
                    
                elif isinstance(element, Dialogue):
                    # Character name (centered)
                    char_name = element.speaker.upper()
                    if element.direction:
                        char_name += f" ({element.direction})"
                    output.append(self._center_text(char_name, self.options.max_line_length))
                    
                    # Dialogue (indented)
                    dialogue_lines = self._wrap_text(element.content, 
                                                   self.options.max_line_length - 20)
                    for line in dialogue_lines:
                        output.append(" " * 10 + line)
                    output.append("")
        
        return "\n".join(output)
    
    def format_as_json(self, script: ParsedScript) -> str:
        """
        Format script as structured JSON.
        
        Args:
            script: Parsed script data
            
        Returns:
            JSON string
        """
        data = {
            'metadata': {
                'title': script.metadata.title,
                'location': script.metadata.location,
                'date': script.metadata.date,
                'reporter': script.metadata.reporter,
                'duration': script.metadata.duration,
                'corruption': script.metadata.corruption,
                'recovery_status': script.metadata.recovery_status,
                'additional': script.metadata.raw_metadata
            },
            'statistics': {
                'total_duration': script.total_duration,
                'word_count': script.word_count,
                'scene_count': len(script.scenes),
                'character_count': len(script.characters)
            },
            'characters': script.characters,
            'scenes': []
        }
        
        for scene in script.scenes:
            scene_data = {
                'id': scene.id,
                'number': scene.number,
                'duration': scene.total_duration,
                'elements': []
            }
            
            for element in scene.elements:
                elem_data = {
                    'type': element.type,
                    'content': element.content,
                    'timing': element.timing_estimate
                }
                
                if isinstance(element, Dialogue):
                    elem_data['speaker'] = element.speaker
                    if element.direction:
                        elem_data['direction'] = element.direction
                        
                elif isinstance(element, Narrative):
                    if self.options.include_visual_cues and element.visual_cues:
                        elem_data['visual_cues'] = element.visual_cues
                    if element.emotional_tone:
                        elem_data['emotional_tone'] = element.emotional_tone
                        
                elif isinstance(element, SceneDescription):
                    if element.location:
                        elem_data['location'] = element.location
                    if element.time_of_day:
                        elem_data['time_of_day'] = element.time_of_day
                
                scene_data['elements'].append(elem_data)
            
            if self.options.include_visual_cues and scene.visual_prompts:
                scene_data['visual_prompts'] = scene.visual_prompts
            
            data['scenes'].append(scene_data)
        
        return json.dumps(data, indent=2)
    
    def format_as_xml(self, script: ParsedScript) -> str:
        """
        Format script as XML.
        
        Args:
            script: Parsed script data
            
        Returns:
            XML string
        """
        root = ET.Element('script')
        
        # Add metadata
        metadata = ET.SubElement(root, 'metadata')
        for field in ['title', 'location', 'date', 'reporter', 'duration', 
                      'corruption', 'recovery_status']:
            value = getattr(script.metadata, field)
            if value:
                elem = ET.SubElement(metadata, field)
                elem.text = str(value)
        
        # Add statistics
        stats = ET.SubElement(root, 'statistics')
        stats.set('total_duration', str(script.total_duration))
        stats.set('word_count', str(script.word_count))
        stats.set('scene_count', str(len(script.scenes)))
        stats.set('character_count', str(len(script.characters)))
        
        # Add characters
        chars = ET.SubElement(root, 'characters')
        for char in script.characters:
            char_elem = ET.SubElement(chars, 'character')
            char_elem.text = char
        
        # Add scenes
        scenes = ET.SubElement(root, 'scenes')
        for scene in script.scenes:
            scene_elem = ET.SubElement(scenes, 'scene')
            scene_elem.set('id', scene.id)
            scene_elem.set('number', str(scene.number))
            scene_elem.set('duration', str(scene.total_duration))
            
            # Add elements
            for element in scene.elements:
                elem_node = ET.SubElement(scene_elem, element.type)
                elem_node.set('timing', str(element.timing_estimate))
                
                content_node = ET.SubElement(elem_node, 'content')
                content_node.text = element.content
                
                if isinstance(element, Dialogue):
                    elem_node.set('speaker', element.speaker)
                    if element.direction:
                        dir_node = ET.SubElement(elem_node, 'direction')
                        dir_node.text = element.direction
        
        # Pretty print
        xml_str = ET.tostring(root, encoding='unicode')
        dom = minidom.parseString(xml_str)
        return dom.toprettyxml(indent='  ')
    
    # Helper methods
    
    def _clean_text_for_speech(self, text: str) -> str:
        """Clean text for voice synthesis."""
        # Remove special characters that might confuse TTS
        text = re.sub(r'[*_~`]', '', text)
        
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Ensure proper spacing around punctuation
        text = re.sub(r'\s*([.,!?;:])\s*', r'\1 ', text)
        
        # Remove trailing spaces
        text = text.strip()
        
        return text
    
    def _normalize_speaker_name(self, name: str) -> str:
        """Normalize speaker name for voice assignment."""
        # Convert to lowercase and remove special characters
        normalized = re.sub(r'[^a-zA-Z0-9]', '_', name.lower())
        
        # Remove multiple underscores
        normalized = re.sub(r'_+', '_', normalized)
        
        # Remove leading/trailing underscores
        normalized = normalized.strip('_')
        
        return normalized or 'unknown'
    
    def _determine_scene_mood(self, scene: Scene) -> str:
        """Determine the mood of a scene."""
        mood_keywords = {
            'dark': ['death', 'bodies', 'suicide', 'horror'],
            'tense': ['urgent', 'escape', 'desperate', 'attack'],
            'mysterious': ['unknown', 'strange', 'discovered'],
            'action': ['running', 'fighting', 'chase', 'explosion']
        }
        
        scene_text = ' '.join(elem.content.lower() for elem in scene.elements)
        
        mood_scores = {}
        for mood, keywords in mood_keywords.items():
            score = sum(1 for keyword in keywords if keyword in scene_text)
            if score > 0:
                mood_scores[mood] = score
        
        if mood_scores:
            return max(mood_scores.items(), key=lambda x: x[1])[0]
        
        return 'neutral'
    
    def _determine_visual_style(self, script: ParsedScript, mood: str) -> str:
        """Determine visual style based on script and mood."""
        style_map = {
            'dark': 'dark, gritty, high contrast, desaturated colors',
            'tense': 'dynamic angles, sharp focus, intense lighting',
            'mysterious': 'soft focus, atmospheric, moody lighting',
            'action': 'fast motion, dynamic composition, high energy',
            'neutral': 'cinematic, balanced composition, natural lighting'
        }
        
        base_style = style_map.get(mood, style_map['neutral'])
        
        # Add genre-specific style elements
        if 'dystopian' in str(script.metadata.title).lower():
            base_style += ', dystopian aesthetic, industrial'
        elif 'sci-fi' in str(script.metadata.title).lower():
            base_style += ', futuristic, technological'
        
        return base_style
    
    def _create_visual_prompt(self, elements: List[str]) -> str:
        """Create a visual generation prompt from elements."""
        # Filter out empty elements
        elements = [e for e in elements if e and e.strip()]
        
        # Join with commas
        prompt = ', '.join(elements)
        
        # Add default if empty
        if not prompt:
            prompt = "Cinematic scene, atmospheric lighting"
        
        return prompt
    
    def _extract_key_visual_moments(self, scene: Scene) -> List[Dict[str, Any]]:
        """Extract key visual moments from a scene."""
        moments = []
        
        # Look for specific visual triggers
        triggers = [
            (r'(?:bodies|corpses)\s+(?:on|in|at)', 'dark, somber composition', 3.0),
            (r'(?:explosion|blast|fire)', 'dynamic action shot, explosive effects', 2.0),
            (r'(?:chase|running|escape)', 'motion blur, dynamic movement', 2.5),
            (r'(?:reveal|discover|find)', 'dramatic reveal, focused lighting', 3.0)
        ]
        
        for element in scene.elements:
            if isinstance(element, Narrative):
                for pattern, style, duration in triggers:
                    if re.search(pattern, element.content, re.IGNORECASE):
                        moments.append({
                            'prompt': self._create_visual_prompt([element.content[:100]]),
                            'style': style,
                            'duration': duration
                        })
                        break
        
        return moments[:2]  # Limit to 2 key moments per scene
    
    def _format_scene_heading(self, scene: Scene) -> Optional[str]:
        """Format a scene heading for screenplay format."""
        for element in scene.elements:
            if isinstance(element, SceneDescription):
                location = element.location or "UNKNOWN"
                time = element.time_of_day or "DAY"
                return f"INT. {location.upper()} - {time.upper()}"
        
        return f"SCENE {scene.number}"
    
    def _wrap_text(self, text: str, max_length: int) -> List[str]:
        """Wrap text to specified line length."""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            if len(' '.join(current_line + [word])) <= max_length:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def _center_text(self, text: str, width: int) -> str:
        """Center text within specified width."""
        return text.center(width)
    
    def _format_as_srt(self, script: ParsedScript) -> str:
        """Format as SRT subtitles."""
        output = []
        subtitle_num = 1
        current_time = 0.0
        
        for scene in script.scenes:
            for element in scene.elements:
                if isinstance(element, (Narrative, Dialogue)):
                    start_time = current_time
                    end_time = current_time + element.timing_estimate
                    
                    # Format times
                    start_str = self._format_srt_time(start_time)
                    end_str = self._format_srt_time(end_time)
                    
                    # Add subtitle
                    output.append(str(subtitle_num))
                    output.append(f"{start_str} --> {end_str}")
                    
                    # Add speaker name for dialogue
                    if isinstance(element, Dialogue):
                        output.append(f"[{element.speaker}]")
                    
                    # Wrap text
                    lines = self._wrap_text(element.content, 45)
                    output.extend(lines)
                    output.append("")  # Empty line between subtitles
                    
                    subtitle_num += 1
                    current_time = end_time
        
        return "\n".join(output)
    
    def _format_as_vtt(self, script: ParsedScript) -> str:
        """Format as WebVTT subtitles."""
        output = ["WEBVTT", ""]
        
        current_time = 0.0
        for scene in script.scenes:
            for element in scene.elements:
                if isinstance(element, (Narrative, Dialogue)):
                    start_time = current_time
                    end_time = current_time + element.timing_estimate
                    
                    # Format times
                    start_str = self._format_vtt_time(start_time)
                    end_str = self._format_vtt_time(end_time)
                    
                    output.append(f"{start_str} --> {end_str}")
                    
                    # Add speaker name for dialogue
                    if isinstance(element, Dialogue):
                        output.append(f"<v {element.speaker}>")
                    
                    # Add text
                    lines = self._wrap_text(element.content, 45)
                    output.extend(lines)
                    output.append("")
                    
                    current_time = end_time
        
        return "\n".join(output)
    
    def _format_as_ass(self, script: ParsedScript) -> str:
        """Format as Advanced SubStation Alpha subtitles."""
        # This is a simplified ASS format
        output = [
            "[Script Info]",
            "Title: " + (script.metadata.title or "Unknown"),
            "ScriptType: v4.00+",
            "",
            "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
            "Style: Default,Arial,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,2,2,10,10,10,1",
            "Style: Narrator,Arial,20,&H00FFFF00,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,2,2,10,10,10,1",
            "",
            "[Events]",
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
        ]
        
        current_time = 0.0
        for scene in script.scenes:
            for element in scene.elements:
                if isinstance(element, (Narrative, Dialogue)):
                    start_time = current_time
                    end_time = current_time + element.timing_estimate
                    
                    # Format times
                    start_str = self._format_ass_time(start_time)
                    end_str = self._format_ass_time(end_time)
                    
                    # Determine style
                    style = "Default" if isinstance(element, Dialogue) else "Narrator"
                    name = element.speaker if isinstance(element, Dialogue) else "Narrator"
                    
                    # Clean text
                    text = element.content.replace('\n', '\\N')
                    
                    output.append(f"Dialogue: 0,{start_str},{end_str},{style},{name},0,0,0,,{text}")
                    
                    current_time = end_time
        
        return "\n".join(output)
    
    def _format_srt_time(self, seconds: float) -> str:
        """Format time for SRT (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def _format_vtt_time(self, seconds: float) -> str:
        """Format time for WebVTT (HH:MM:SS.mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
    
    def _format_ass_time(self, seconds: float) -> str:
        """Format time for ASS (H:MM:SS.CC)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centis = int((seconds % 1) * 100)
        return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"