"""
Script parser for processing screenplay-format scripts.
"""

import re
from typing import Dict, List, Any, Optional, Tuple

class ScriptParser:
    """Parser for screenplay-format scripts."""
    
    def __init__(self):
        """Initialize the script parser."""
        self.scene_heading_pattern = re.compile(
            r'^(INT\.|EXT\.|INT/EXT\.|I/E\.)?\s*(.+?)(?:\s*[-–]\s*(.+))?$',
            re.IGNORECASE | re.MULTILINE
        )
        self.character_pattern = re.compile(
            r'^[A-Z][A-Z\s\.\'-]+(?:\s*\([^\)]+\))?$',
            re.MULTILINE
        )
        self.dialogue_pattern = re.compile(
            r'^.+$',
            re.MULTILINE
        )
        self.parenthetical_pattern = re.compile(
            r'^\s*\([^\)]+\)\s*$',
            re.MULTILINE
        )
        self.action_pattern = re.compile(
            r'^.+$',
            re.MULTILINE
        )
        self.transition_pattern = re.compile(
            r'^(?:FADE IN:|FADE OUT:|FADE TO:|CUT TO:|DISSOLVE TO:)\s*$',
            re.IGNORECASE | re.MULTILINE
        )
    
    def parse(self, script_content: str) -> Dict[str, Any]:
        """
        Parse a screenplay script.
        
        Args:
            script_content: Raw script text
            
        Returns:
            Parsed script data with scenes, dialogue, and actions
        """
        lines = script_content.split('\n')
        parsed_data = {
            'scenes': [],
            'characters': set(),
            'total_pages': self._estimate_pages(script_content)
        }
        
        current_scene = None
        current_character = None
        in_dialogue = False
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines
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
                
            # Check for character name
            elif self._is_character_name(line):
                current_character = self._parse_character_name(line)
                parsed_data['characters'].add(current_character['name'])
                in_dialogue = True
                
            # Check for parenthetical
            elif in_dialogue and self._is_parenthetical(line):
                if current_character and current_scene:
                    current_character['direction'] = line.strip('()')
                    
            # Check for dialogue
            elif in_dialogue and current_character and line:
                if current_scene:
                    dialogue_entry = {
                        'character': current_character['name'],
                        'text': line,
                        'direction': current_character.get('direction')
                    }
                    current_scene['dialogue'].append(dialogue_entry)
                current_character['direction'] = None
                
            # Check for transition
            elif self._is_transition(line):
                if current_scene:
                    current_scene['transition'] = line
                in_dialogue = False
                current_character = None
                
            # Otherwise it's action
            else:
                if current_scene:
                    current_scene['action'].append(line)
                in_dialogue = False
                current_character = None
            
            i += 1
        
        # Add the last scene
        if current_scene:
            parsed_data['scenes'].append(current_scene)
        
        # Convert character set to list
        parsed_data['characters'] = list(parsed_data['characters'])
        
        # Add scene numbers
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
        # Character names are usually in all caps and centered
        return bool(self.character_pattern.match(line)) and line.isupper()
    
    def _parse_character_name(self, line: str) -> Dict[str, str]:
        """Parse character name and any direction."""
        # Remove any parenthetical from character name
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


class ScriptValidator:
    """Validator for screenplay scripts."""
    
    def validate(self, script_content: str) -> Dict[str, Any]:
        """
        Validate script format and content.
        
        Args:
            script_content: Raw script text
            
        Returns:
            Validation result with errors if any
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        if not script_content or not script_content.strip():
            result['valid'] = False
            result['errors'].append("Script content is empty")
            return result
        
        lines = script_content.split('\n')
        
        # Check for basic structure
        has_scene_heading = False
        has_dialogue = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check for scene headings
            if re.match(r'^(INT\.|EXT\.|INT/EXT\.|I/E\.)', line, re.IGNORECASE):
                has_scene_heading = True
                
            # Check for dialogue (character names in caps)
            if line.isupper() and len(line.split()) <= 3:
                has_dialogue = True
        
        if not has_scene_heading:
            result['warnings'].append("No scene headings found (INT./EXT.)")
            
        if not has_dialogue:
            result['warnings'].append("No dialogue found (character names should be in CAPS)")
        
        # Check minimum length
        if len(lines) < 10:
            result['warnings'].append("Script seems too short (less than 10 lines)")
        
        return result