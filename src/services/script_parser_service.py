"""
Script Parser Service

Handles parsing of LOG script format for video generation with proper error handling
and validation.
"""

import re
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

import structlog

logger = structlog.get_logger()


@dataclass
class ScriptSegment:
    """Represents a parsed script segment."""
    timestamp: str
    timestamp_seconds: int
    title: str
    visual_descriptions: List[str]
    narration: List[str]
    onscreen_text: List[str]
    raw_content: str


class ScriptParserService:
    """Service for parsing script content into structured data."""
    
    def __init__(self):
        """Initialize the script parser with regex patterns."""
        self.timestamp_pattern = re.compile(r'\[(\d+:\d+)[^\]]*\]')
        self.visual_pattern = re.compile(
            r'Visual:\s*(.+?)(?=\n(?:Audio|Narration|ON-SCREEN|Visual|\[|$))',
            re.DOTALL | re.MULTILINE
        )
        self.narration_pattern = re.compile(
            r'(?:Narration|Audio)\s*\([^)]+\):\s*(.+?)(?=\n(?:Audio|Narration|Visual|ON-SCREEN|\[|$))',
            re.DOTALL | re.MULTILINE
        )
        self.onscreen_pattern = re.compile(
            r'ON-SCREEN[^:]*:\s*(.+?)(?=\n(?:Audio|Narration|Visual|ON-SCREEN|\[|$))',
            re.DOTALL | re.MULTILINE
        )
        
        logger.info("Script parser service initialized")
    
    async def parse_script(self, script_content: str) -> Dict[str, Any]:
        """
        Parse script content into structured data.
        
        Args:
            script_content: Raw script content string
            
        Returns:
            Parsed script data with scenes and metadata
            
        Raises:
            ValueError: If script content is invalid or empty
            Exception: For other parsing errors
        """
        if not script_content or not script_content.strip():
            raise ValueError("Script content is empty or invalid")
        
        logger.info("Starting script parsing", content_length=len(script_content))
        
        try:
            # Extract basic metadata
            title = self._extract_title(script_content)
            
            # Split script into timestamp sections
            sections = self.timestamp_pattern.split(script_content)
            
            if len(sections) < 3:  # At least header + one timestamp + content
                raise ValueError("No valid timestamp sections found in script")
            
            scenes = []
            total_duration = 0
            
            # Process each timestamp section
            for i in range(1, len(sections), 2):
                if i + 1 < len(sections):
                    timestamp = sections[i]
                    content = sections[i + 1]
                    
                    try:
                        scene = self._parse_scene(timestamp, content)
                        scenes.append(scene)
                        
                        # Update total duration
                        scene_end = scene.timestamp_seconds + 30  # Default scene length
                        total_duration = max(total_duration, scene_end)
                        
                    except Exception as e:
                        logger.warning(
                            "Failed to parse scene",
                            timestamp=timestamp,
                            error=str(e)
                        )
                        continue
            
            if not scenes:
                raise ValueError("No valid scenes found in script")
            
            result = {
                "title": title,
                "scenes": [self._scene_to_dict(scene) for scene in scenes],
                "total_duration": total_duration,
                "scene_count": len(scenes),
                "metadata": {
                    "parsed_at": "now",
                    "parser_version": "2.0",
                    "content_length": len(script_content)
                }
            }
            
            logger.info(
                "Script parsing completed successfully",
                title=title,
                scenes=len(scenes),
                duration=total_duration
            )
            
            return result
            
        except Exception as e:
            logger.error("Script parsing failed", error=str(e), exc_info=True)
            raise
    
    def _extract_title(self, script_content: str) -> str:
        """Extract script title from content."""
        title_match = re.search(r'SCRIPT:\s*(.+)', script_content)
        if title_match:
            return title_match.group(1).strip()
        
        # Fallback: use first non-empty line
        lines = script_content.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('['):
                return line[:50]  # Limit title length
        
        return "Unknown Script"
    
    def _parse_scene(self, timestamp: str, content: str) -> ScriptSegment:
        """
        Parse individual scene content.
        
        Args:
            timestamp: Scene timestamp (e.g., "0:00")
            content: Scene content
            
        Returns:
            Parsed scene segment
        """
        # Extract scene title/description
        content_lines = content.split('\n')
        first_line = content_lines[0] if content_lines else ""
        
        # Clean up the title
        title_match = re.search(r'([^|]+)', first_line)
        title = title_match.group(1).strip() if title_match else f"Scene {timestamp}"
        
        # Remove common prefixes
        title = re.sub(r'^(Scene|SCENE)\s*\d*:?\s*', '', title, flags=re.IGNORECASE)
        title = title.strip() or f"Scene {timestamp}"
        
        # Extract visual descriptions
        visual_matches = self.visual_pattern.findall(content)
        visual_descriptions = [
            self._clean_text(v) for v in visual_matches if v.strip()
        ]
        
        # Extract narration/audio
        narration_matches = self.narration_pattern.findall(content)
        narration_text = [
            self._clean_text(n) for n in narration_matches if n.strip()
        ]
        
        # Extract on-screen text
        onscreen_matches = self.onscreen_pattern.findall(content)
        onscreen_elements = [
            self._clean_text(t) for t in onscreen_matches if t.strip()
        ]
        
        return ScriptSegment(
            timestamp=timestamp,
            timestamp_seconds=self._timestamp_to_seconds(timestamp),
            title=title,
            visual_descriptions=visual_descriptions,
            narration=narration_text,
            onscreen_text=onscreen_elements,
            raw_content=content.strip()
        )
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        # Remove extra whitespace and newlines
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove common markdown artifacts
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*(.+?)\*', r'\1', text)      # Italic
        text = re.sub(r'`(.+?)`', r'\1', text)        # Code
        
        return text
    
    def _timestamp_to_seconds(self, timestamp: str) -> int:
        """
        Convert MM:SS timestamp to seconds.
        
        Args:
            timestamp: Timestamp string (e.g., "1:30")
            
        Returns:
            Timestamp in seconds
        """
        try:
            parts = timestamp.split(':')
            if len(parts) == 2:
                minutes, seconds = map(int, parts)
                return minutes * 60 + seconds
            elif len(parts) == 3:
                hours, minutes, seconds = map(int, parts)
                return hours * 3600 + minutes * 60 + seconds
            else:
                # Single number, assume seconds
                return int(parts[0])
        except (ValueError, IndexError):
            logger.warning("Invalid timestamp format", timestamp=timestamp)
            return 0
    
    def _scene_to_dict(self, scene: ScriptSegment) -> Dict[str, Any]:
        """Convert ScriptSegment to dictionary for JSON serialization."""
        return {
            "timestamp": scene.timestamp,
            "timestamp_seconds": scene.timestamp_seconds,
            "title": scene.title,
            "visual_descriptions": scene.visual_descriptions,
            "narration": scene.narration,
            "onscreen_text": scene.onscreen_text,
            "raw_content": scene.raw_content
        }
    
    def validate_script(self, script_content: str) -> List[Dict[str, Any]]:
        """
        Validate script content and return warnings/errors.
        
        Args:
            script_content: Script content to validate
            
        Returns:
            List of validation issues
        """
        issues = []
        
        if not script_content or not script_content.strip():
            issues.append({
                "type": "error",
                "message": "Script content is empty",
                "line": 0
            })
            return issues
        
        # Check for timestamp format
        timestamps = self.timestamp_pattern.findall(script_content)
        if not timestamps:
            issues.append({
                "type": "error",
                "message": "No valid timestamps found (format: [MM:SS])",
                "line": 0
            })
        
        # Check for duplicate timestamps
        timestamp_counts = {}
        for ts in timestamps:
            timestamp_counts[ts] = timestamp_counts.get(ts, 0) + 1
        
        for ts, count in timestamp_counts.items():
            if count > 1:
                issues.append({
                    "type": "warning",
                    "message": f"Duplicate timestamp: {ts}",
                    "timestamp": ts
                })
        
        # Check for content in scenes
        sections = self.timestamp_pattern.split(script_content)
        for i in range(1, len(sections), 2):
            if i + 1 < len(sections):
                timestamp = sections[i]
                content = sections[i + 1].strip()
                
                if not content:
                    issues.append({
                        "type": "warning",
                        "message": f"Empty scene content",
                        "timestamp": timestamp
                    })
                
                # Check for required elements
                has_visual = bool(self.visual_pattern.search(content))
                has_narration = bool(self.narration_pattern.search(content))
                
                if not has_visual and not has_narration:
                    issues.append({
                        "type": "warning",
                        "message": f"Scene has no visual or narration content",
                        "timestamp": timestamp
                    })
        
        return issues
    
    def health_check(self) -> Dict[str, Any]:
        """Return service health status."""
        return {
            "status": "healthy",
            "service": "script_parser",
            "patterns_loaded": 4,
            "version": "2.0"
        }