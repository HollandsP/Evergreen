"""
Script parser module for processing markdown and screenplay format scripts.
"""

import re
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


@dataclass
class ScriptMetadata:
    """Metadata for a script."""
    title: str = ""
    location: str = ""
    date: str = ""
    reporter: str = ""
    duration: str = ""
    corruption: str = ""
    recovery_status: str = ""
    raw_metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class SceneElement:
    """Base class for scene elements."""
    type: str
    content: str
    line_number: int
    timing_estimate: float = 0.0  # in seconds


@dataclass
class Narrative(SceneElement):
    """Narrative text element."""
    type: str = "narrative"
    visual_cues: List[str] = field(default_factory=list)
    emotional_tone: str = ""


@dataclass
class Dialogue(SceneElement):
    """Dialogue element."""
    type: str = "dialogue"
    speaker: str = ""
    direction: Optional[str] = None
    

@dataclass
class SceneDescription(SceneElement):
    """Scene description element."""
    type: str = "scene_description"
    location: Optional[str] = None
    time_of_day: Optional[str] = None
    mood: Optional[str] = None


@dataclass
class Scene:
    """Represents a scene in the script."""
    id: str
    number: int
    elements: List[SceneElement] = field(default_factory=list)
    total_duration: float = 0.0
    visual_prompts: List[str] = field(default_factory=list)


@dataclass
class ParsedScript:
    """Complete parsed script data."""
    metadata: ScriptMetadata
    scenes: List[Scene]
    characters: List[str]
    total_duration: float
    word_count: int
    visual_cues: List[str]
    narrative_segments: List[Narrative]
    dialogue_segments: List[Dialogue]


class BaseScriptParser(ABC):
    """Abstract base class for script parsers."""
    
    # Average reading speeds
    WORDS_PER_MINUTE_NARRATION = 150  # Slower for dramatic effect
    WORDS_PER_MINUTE_DIALOGUE = 180   # Natural speech pace
    
    def __init__(self):
        """Initialize the parser."""
        self.reset()
    
    def reset(self):
        """Reset parser state."""
        self.metadata = ScriptMetadata()
        self.scenes = []
        self.characters = set()
        self.visual_cues = []
        self.narrative_segments = []
        self.dialogue_segments = []
        
    @abstractmethod
    def parse(self, content: str) -> ParsedScript:
        """Parse script content."""
        pass
    
    def calculate_timing(self, text: str, is_dialogue: bool = False) -> float:
        """
        Calculate timing estimate for text.
        
        Args:
            text: Text to calculate timing for
            is_dialogue: Whether this is dialogue (affects reading speed)
            
        Returns:
            Estimated duration in seconds
        """
        word_count = len(text.split())
        wpm = self.WORDS_PER_MINUTE_DIALOGUE if is_dialogue else self.WORDS_PER_MINUTE_NARRATION
        return (word_count / wpm) * 60
    
    def extract_visual_cues(self, text: str) -> List[str]:
        """
        Extract visual cues from text for video generation.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of visual cues/prompts
        """
        visual_cues = []
        
        # Look for descriptive phrases
        descriptive_patterns = [
            r'(?:bodies?|people?|figures?)\s+(?:on|in|at)\s+(?:the\s+)?(\w+)',
            r'(?:wearing|dressed in|wore)\s+(\w+(?:\s+\w+)*)',
            r'(?:arranged|positioned|placed)\s+(?:in\s+)?(\w+(?:\s+\w+)*)',
            r'(\d+)\s+(?:programmers?|scientists?|people)',
            r'(?:facility|building|room|center)\s+(?:with\s+)?(\w+(?:\s+\w+)*)',
            r'(?:screens?|monitors?|displays?)\s+(?:showing|displaying)\s+(\w+(?:\s+\w+)*)',
            r'(?:jumped|fell|dropped)\s+(?:from\s+)?(?:the\s+)?(\w+)',
        ]
        
        for pattern in descriptive_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                visual_cues.append(match.group(0))
        
        # Look for emotional/atmospheric descriptions
        atmospheric_keywords = [
            'dark', 'bright', 'gloomy', 'empty', 'crowded', 'abandoned',
            'destroyed', 'burning', 'frozen', 'silent', 'chaotic'
        ]
        
        for keyword in atmospheric_keywords:
            if keyword in text.lower():
                visual_cues.append(f"atmosphere: {keyword}")
        
        return visual_cues
    
    def detect_emotional_tone(self, text: str) -> str:
        """
        Detect emotional tone of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Emotional tone description
        """
        # Simple keyword-based detection
        emotions = {
            'despair': ['suicide', 'death', 'lost', 'jumped', 'bodies'],
            'fear': ['terror', 'afraid', 'scared', 'horror', 'nightmare'],
            'urgency': ['attempt', 'trying', 'must', 'now', 'immediately'],
            'hopeless': ['can\'t', 'impossible', 'failed', 'futile'],
            'determined': ['will', 'must', 'fight', 'resist', 'attempt']
        }
        
        text_lower = text.lower()
        detected_emotions = []
        
        for emotion, keywords in emotions.items():
            if any(keyword in text_lower for keyword in keywords):
                detected_emotions.append(emotion)
        
        return ', '.join(detected_emotions) if detected_emotions else 'neutral'


class MarkdownScriptParser(BaseScriptParser):
    """Parser for markdown format scripts like LOG files."""
    
    def __init__(self):
        """Initialize the markdown parser."""
        super().__init__()
        self.metadata_pattern = re.compile(r'^\*\*(.+?)\*\*:\s*(.+)$', re.MULTILINE)
        self.dialogue_pattern = re.compile(r'^"(.+?)"(?:\s*[-—]\s*(.+))?$', re.MULTILINE)
        self.scene_break_pattern = re.compile(r'^(?:---+|\*\*\*+|___+)\s*$', re.MULTILINE)
        
    def parse(self, content: str) -> ParsedScript:
        """
        Parse markdown format script.
        
        Args:
            content: Raw markdown content
            
        Returns:
            Parsed script data
        """
        self.reset()
        
        lines = content.split('\n')
        current_scene_elements = []
        current_scene_number = 1
        in_metadata_section = False
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
            
            # Check for title (H1 heading)
            if line.startswith('# '):
                self.metadata.title = line[2:].strip()
                i += 1
                continue
            
            # Check for metadata section
            if self.metadata_pattern.match(line):
                self._parse_metadata_line(line)
                in_metadata_section = True
                i += 1
                continue
            
            # Check for scene break
            if self.scene_break_pattern.match(line):
                if current_scene_elements:
                    scene = self._create_scene(
                        f"scene_{current_scene_number}",
                        current_scene_number,
                        current_scene_elements
                    )
                    self.scenes.append(scene)
                    current_scene_elements = []
                    current_scene_number += 1
                in_metadata_section = False
                i += 1
                continue
            
            # Check for metadata list items
            if line.startswith('- ') and in_metadata_section:
                key_value = line[2:].strip()
                if ':' in key_value:
                    key, value = key_value.split(':', 1)
                    self.metadata.raw_metadata[key.strip()] = value.strip()
                i += 1
                continue
            
            # Check for dialogue
            dialogue_match = self.dialogue_pattern.match(line)
            if dialogue_match:
                dialogue = Dialogue(
                    content=dialogue_match.group(1),
                    line_number=i + 1,
                    speaker=dialogue_match.group(2) or "Unknown"
                )
                dialogue.timing_estimate = self.calculate_timing(dialogue.content, True)
                current_scene_elements.append(dialogue)
                self.dialogue_segments.append(dialogue)
                
                # Add speaker to characters
                if dialogue.speaker != "Unknown":
                    self.characters.add(dialogue.speaker)
                i += 1
                continue
            
            # Check for bracketed sections (scene transitions, technical notes)
            if line.startswith('[') and line.endswith(']'):
                scene_desc = SceneDescription(
                    content=line[1:-1],
                    line_number=i + 1
                )
                scene_desc.timing_estimate = 2.0  # Fixed timing for transitions
                current_scene_elements.append(scene_desc)
                i += 1
                continue
            
            # Otherwise it's narrative text
            narrative = Narrative(
                content=line,
                line_number=i + 1
            )
            narrative.timing_estimate = self.calculate_timing(narrative.content)
            narrative.visual_cues = self.extract_visual_cues(narrative.content)
            narrative.emotional_tone = self.detect_emotional_tone(narrative.content)
            
            current_scene_elements.append(narrative)
            self.narrative_segments.append(narrative)
            self.visual_cues.extend(narrative.visual_cues)
            
            i += 1
        
        # Add final scene if exists
        if current_scene_elements:
            scene = self._create_scene(
                f"scene_{current_scene_number}",
                current_scene_number,
                current_scene_elements
            )
            self.scenes.append(scene)
        
        # Calculate totals
        total_duration = sum(scene.total_duration for scene in self.scenes)
        word_count = sum(len(elem.content.split()) for scene in self.scenes for elem in scene.elements)
        
        return ParsedScript(
            metadata=self.metadata,
            scenes=self.scenes,
            characters=list(self.characters),
            total_duration=total_duration,
            word_count=word_count,
            visual_cues=self.visual_cues,
            narrative_segments=self.narrative_segments,
            dialogue_segments=self.dialogue_segments
        )
    
    def _parse_metadata_line(self, line: str):
        """Parse a metadata line."""
        match = self.metadata_pattern.match(line)
        if match:
            key = match.group(1).lower()
            value = match.group(2)
            
            if key == 'location':
                self.metadata.location = value
            elif key == 'date':
                self.metadata.date = value
            elif key == 'reporter':
                self.metadata.reporter = value
            elif key == 'duration':
                self.metadata.duration = value
            elif key == 'corruption':
                self.metadata.corruption = value
            elif key == 'recovery status':
                self.metadata.recovery_status = value
            else:
                self.metadata.raw_metadata[key] = value
    
    def _create_scene(self, scene_id: str, number: int, elements: List[SceneElement]) -> Scene:
        """Create a scene from elements."""
        scene = Scene(
            id=scene_id,
            number=number,
            elements=elements
        )
        
        # Calculate total duration
        scene.total_duration = sum(elem.timing_estimate for elem in elements)
        
        # Extract visual prompts
        for elem in elements:
            if isinstance(elem, Narrative) and elem.visual_cues:
                scene.visual_prompts.extend(elem.visual_cues)
        
        return scene


class ScreenplayScriptParser(BaseScriptParser):
    """Parser for traditional screenplay format scripts."""
    
    def __init__(self):
        """Initialize the screenplay parser."""
        super().__init__()
        self.scene_heading_pattern = re.compile(
            r'^(INT\.|EXT\.|INT/EXT\.|I/E\.)?\s*(.+?)(?:\s*[-–]\s*(.+))?$',
            re.IGNORECASE | re.MULTILINE
        )
        self.character_pattern = re.compile(
            r'^[A-Z][A-Z\s\.\'-]+(?:\s*\([^\)]+\))?$',
            re.MULTILINE
        )
        self.parenthetical_pattern = re.compile(
            r'^\s*\([^\)]+\)\s*$',
            re.MULTILINE
        )
        self.transition_pattern = re.compile(
            r'^(?:FADE IN:|FADE OUT:|FADE TO:|CUT TO:|DISSOLVE TO:)\s*$',
            re.IGNORECASE | re.MULTILINE
        )
    
    def parse(self, content: str) -> ParsedScript:
        """
        Parse screenplay format script.
        
        Args:
            content: Raw screenplay text
            
        Returns:
            Parsed script data
        """
        self.reset()
        
        # For now, create a simple title from content
        lines = content.split('\n')
        if lines:
            self.metadata.title = "Screenplay Script"
        
        # Use existing parsing logic
        parsed_data = self._parse_screenplay(content)
        
        # Convert to new format
        scenes = []
        for scene_data in parsed_data.get('scenes', []):
            scene_elements = []
            
            # Add scene description
            scene_desc = SceneDescription(
                content=scene_data.get('description', ''),
                line_number=0,
                location=scene_data.get('location'),
                time_of_day=scene_data.get('time')
            )
            scene_desc.timing_estimate = 3.0  # Fixed timing for scene headers
            scene_elements.append(scene_desc)
            
            # Add action lines
            for action in scene_data.get('action', []):
                narrative = Narrative(
                    content=action,
                    line_number=0
                )
                narrative.timing_estimate = self.calculate_timing(narrative.content)
                narrative.visual_cues = self.extract_visual_cues(narrative.content)
                scene_elements.append(narrative)
                self.narrative_segments.append(narrative)
            
            # Add dialogue
            for dialogue_data in scene_data.get('dialogue', []):
                dialogue = Dialogue(
                    content=dialogue_data.get('text', ''),
                    line_number=0,
                    speaker=dialogue_data.get('character', 'Unknown'),
                    direction=dialogue_data.get('direction')
                )
                dialogue.timing_estimate = self.calculate_timing(dialogue.content, True)
                scene_elements.append(dialogue)
                self.dialogue_segments.append(dialogue)
                self.characters.add(dialogue.speaker)
            
            scene = Scene(
                id=scene_data.get('id', f"scene_{len(scenes) + 1}"),
                number=scene_data.get('number', len(scenes) + 1),
                elements=scene_elements
            )
            scene.total_duration = sum(elem.timing_estimate for elem in scene_elements)
            scenes.append(scene)
        
        # Calculate totals
        total_duration = sum(scene.total_duration for scene in scenes)
        word_count = sum(len(elem.content.split()) for scene in scenes for elem in scene.elements)
        
        return ParsedScript(
            metadata=self.metadata,
            scenes=scenes,
            characters=list(self.characters),
            total_duration=total_duration,
            word_count=word_count,
            visual_cues=self.visual_cues,
            narrative_segments=self.narrative_segments,
            dialogue_segments=self.dialogue_segments
        )
    
    def _parse_screenplay(self, content: str) -> Dict[str, Any]:
        """Parse screenplay using existing logic."""
        lines = content.split('\n')
        parsed_data = {
            'scenes': [],
            'characters': set(),
            'total_pages': self._estimate_pages(content)
        }
        
        current_scene = None
        current_character = None
        in_dialogue = False
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if not line:
                i += 1
                continue
            
            # Check for scene heading
            if self._is_scene_heading(line):
                if current_scene:
                    parsed_data['scenes'].append(current_scene)
                
                current_scene = self._parse_scene_heading(line)
                current_scene['dialogue'] = []
                current_scene['action'] = []
                current_character = None
                in_dialogue = False
                
            elif self._is_character_name(line):
                current_character = self._parse_character_name(line)
                parsed_data['characters'].add(current_character['name'])
                in_dialogue = True
                
            elif in_dialogue and self._is_parenthetical(line):
                if current_character and current_scene:
                    current_character['direction'] = line.strip('()')
                    
            elif in_dialogue and current_character and line:
                if current_scene:
                    dialogue_entry = {
                        'character': current_character['name'],
                        'text': line,
                        'direction': current_character.get('direction')
                    }
                    current_scene['dialogue'].append(dialogue_entry)
                current_character['direction'] = None
                
            elif self._is_transition(line):
                if current_scene:
                    current_scene['transition'] = line
                in_dialogue = False
                current_character = None
                
            else:
                if current_scene:
                    current_scene['action'].append(line)
                in_dialogue = False
                current_character = None
            
            i += 1
        
        if current_scene:
            parsed_data['scenes'].append(current_scene)
        
        parsed_data['characters'] = list(parsed_data['characters'])
        
        for idx, scene in enumerate(parsed_data['scenes']):
            scene['id'] = f"scene_{idx + 1}"
            scene['number'] = idx + 1
        
        return parsed_data
    
    def _is_scene_heading(self, line: str) -> bool:
        """Check if line is a scene heading."""
        return bool(self.scene_heading_pattern.match(line))
    
    def _parse_scene_heading(self, line: str) -> Dict[str, Any]:
        """Parse scene heading into components."""
        match = self.scene_heading_pattern.match(line)
        if match:
            location_type = match.group(1) or ''
            location = match.group(2) or ''
            time = match.group(3) or ''
            
            return {
                'type': location_type.strip('.').upper() if location_type else 'INT',
                'location': location.strip(),
                'time': time.strip() if time else 'DAY',
                'description': line
            }
        
        return {
            'type': 'INT',
            'location': line,
            'time': 'DAY',
            'description': line
        }
    
    def _is_character_name(self, line: str) -> bool:
        """Check if line is a character name."""
        return bool(self.character_pattern.match(line)) and line.isupper()
    
    def _parse_character_name(self, line: str) -> Dict[str, str]:
        """Parse character name and any direction."""
        name_match = re.match(r'^([A-Z\s\.\'-]+)(?:\s*\(([^\)]+)\))?$', line)
        if name_match:
            return {
                'name': name_match.group(1).strip(),
                'direction': name_match.group(2)
            }
        return {'name': line.strip()}
    
    def _is_parenthetical(self, line: str) -> bool:
        """Check if line is a parenthetical direction."""
        return bool(self.parenthetical_pattern.match(line))
    
    def _is_transition(self, line: str) -> bool:
        """Check if line is a transition."""
        return bool(self.transition_pattern.match(line))
    
    def _estimate_pages(self, script_content: str) -> int:
        """Estimate number of pages (1 page ≈ 55 lines)."""
        lines = script_content.split('\n')
        return max(1, len(lines) // 55)