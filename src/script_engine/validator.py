"""
Script validator for checking script structure and content validity.
"""

from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
import re
import logging
from .parser import ParsedScript, Scene, SceneElement, Narrative, Dialogue, SceneDescription

logger = logging.getLogger(__name__)


@dataclass
class ValidationIssue:
    """Represents a validation issue."""
    severity: str  # 'error', 'warning', 'info'
    category: str  # 'structure', 'content', 'timing', 'format'
    message: str
    location: Optional[str] = None  # e.g., "Scene 3, Line 45"
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Complete validation result."""
    valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)
    score: float = 1.0  # Overall quality score (0-1)
    
    @property
    def errors(self) -> List[ValidationIssue]:
        """Get all error-level issues."""
        return [i for i in self.issues if i.severity == 'error']
    
    @property
    def warnings(self) -> List[ValidationIssue]:
        """Get all warning-level issues."""
        return [i for i in self.issues if i.severity == 'warning']
    
    @property
    def info(self) -> List[ValidationIssue]:
        """Get all info-level issues."""
        return [i for i in self.issues if i.severity == 'info']


class ScriptValidator:
    """Comprehensive validator for scripts."""
    
    # Validation thresholds
    MIN_SCRIPT_LENGTH = 10  # lines
    MIN_SCENE_DURATION = 5.0  # seconds
    MAX_SCENE_DURATION = 600.0  # 10 minutes
    MIN_WORD_COUNT = 50
    MAX_LINE_LENGTH = 200  # characters
    
    # Content patterns that might need review
    SENSITIVE_CONTENT_PATTERNS = [
        r'\b(?:suicide|death|kill|murder|violence)\b',
        r'\b(?:explicit|graphic|disturbing)\b',
    ]
    
    # Technical terms that should be consistent
    TECHNICAL_TERMS = {
        'AI': ['artificial intelligence', 'a.i.', 'machine intelligence'],
        'dataset': ['data set', 'data-set'],
        'email': ['e-mail', 'electronic mail'],
        'website': ['web site', 'web-site']
    }
    
    def __init__(self):
        """Initialize the validator."""
        self.reset()
    
    def reset(self):
        """Reset validator state."""
        self.issues = []
        self.stats = {}
    
    def validate(self, content: Union[str, ParsedScript]) -> ValidationResult:
        """
        Validate script content or parsed script.
        
        Args:
            content: Either raw script text or parsed script object
            
        Returns:
            Validation result with issues and score
        """
        self.reset()
        
        # Handle different input types
        if isinstance(content, str):
            return self._validate_raw_content(content)
        elif isinstance(content, ParsedScript):
            return self._validate_parsed_script(content)
        else:
            return ValidationResult(
                valid=False,
                issues=[ValidationIssue(
                    severity='error',
                    category='format',
                    message='Invalid input type - expected string or ParsedScript'
                )],
                score=0.0
            )
    
    def _validate_raw_content(self, content: str) -> ValidationResult:
        """Validate raw script content."""
        result = ValidationResult(valid=True)
        
        # Check if content is empty
        if not content or not content.strip():
            result.valid = False
            result.issues.append(ValidationIssue(
                severity='error',
                category='content',
                message='Script content is empty'
            ))
            result.score = 0.0
            return result
        
        lines = content.split('\n')
        
        # Basic structure checks
        self._check_basic_structure(lines, result)
        
        # Format-specific checks
        if self._is_markdown_format(content):
            self._validate_markdown_format(lines, result)
        elif self._is_screenplay_format(content):
            self._validate_screenplay_format(lines, result)
        else:
            result.issues.append(ValidationIssue(
                severity='warning',
                category='format',
                message='Script format not clearly identified as markdown or screenplay',
                suggestion='Consider using standard markdown headers or screenplay formatting'
            ))
        
        # Content checks
        self._check_content_issues(content, result)
        
        # Calculate score
        result.score = self._calculate_validation_score(result)
        
        # Set overall validity
        result.valid = len(result.errors) == 0
        
        return result
    
    def _validate_parsed_script(self, script: ParsedScript) -> ValidationResult:
        """Validate a parsed script object."""
        result = ValidationResult(valid=True)
        
        # Structure validation
        self._validate_script_structure(script, result)
        
        # Timing validation
        self._validate_timing(script, result)
        
        # Character validation
        self._validate_characters(script, result)
        
        # Scene validation
        for scene in script.scenes:
            self._validate_scene(scene, result)
        
        # Content consistency
        self._validate_content_consistency(script, result)
        
        # Production feasibility
        self._validate_production_feasibility(script, result)
        
        # Calculate statistics
        result.statistics = self._calculate_statistics(script)
        
        # Calculate score
        result.score = self._calculate_validation_score(result)
        
        # Set overall validity
        result.valid = len(result.errors) == 0
        
        return result
    
    def _check_basic_structure(self, lines: List[str], result: ValidationResult):
        """Check basic structural requirements."""
        non_empty_lines = [line for line in lines if line.strip()]
        
        # Check minimum length
        if len(non_empty_lines) < self.MIN_SCRIPT_LENGTH:
            result.issues.append(ValidationIssue(
                severity='warning',
                category='structure',
                message=f'Script is very short ({len(non_empty_lines)} lines)',
                suggestion=f'Consider expanding - minimum recommended is {self.MIN_SCRIPT_LENGTH} lines'
            ))
        
        # Check line lengths
        long_lines = []
        for i, line in enumerate(lines):
            if len(line) > self.MAX_LINE_LENGTH:
                long_lines.append(i + 1)
        
        if long_lines:
            result.issues.append(ValidationIssue(
                severity='warning',
                category='format',
                message=f'Found {len(long_lines)} lines exceeding {self.MAX_LINE_LENGTH} characters',
                location=f'Lines: {", ".join(str(l) for l in long_lines[:5])}{"..." if len(long_lines) > 5 else ""}',
                suggestion='Consider breaking long lines for better readability'
            ))
        
        # Check for title
        has_title = False
        for line in non_empty_lines[:5]:  # Check first 5 lines
            if line.startswith('#') or line.isupper():
                has_title = True
                break
        
        if not has_title:
            result.issues.append(ValidationIssue(
                severity='warning',
                category='structure',
                message='No clear title found',
                suggestion='Add a title using # heading or ALL CAPS'
            ))
    
    def _is_markdown_format(self, content: str) -> bool:
        """Check if content appears to be markdown format."""
        markers = [
            r'^#\s+',  # Markdown headers
            r'^\*\*\w+\*\*:',  # Bold metadata
            r'^---+$',  # Horizontal rules
            r'^\[.+\]$',  # Bracketed sections
        ]
        
        for marker in markers:
            if re.search(marker, content, re.MULTILINE):
                return True
        
        return False
    
    def _is_screenplay_format(self, content: str) -> bool:
        """Check if content appears to be screenplay format."""
        markers = [
            r'^(INT\.|EXT\.|INT/EXT\.)',  # Scene headings
            r'^[A-Z\s]+$',  # Character names in caps
            r'^\s*\([^\)]+\)\s*$',  # Parentheticals
            r'^(FADE IN:|FADE OUT:|CUT TO:)',  # Transitions
        ]
        
        matches = 0
        for marker in markers:
            if re.search(marker, content, re.MULTILINE):
                matches += 1
        
        return matches >= 2
    
    def _validate_markdown_format(self, lines: List[str], result: ValidationResult):
        """Validate markdown-specific formatting."""
        has_metadata = False
        has_separator = False
        
        for line in lines:
            if re.match(r'^\*\*\w+\*\*:', line):
                has_metadata = True
            if re.match(r'^---+$', line):
                has_separator = True
        
        if not has_metadata:
            result.issues.append(ValidationIssue(
                severity='info',
                category='format',
                message='No metadata fields found (e.g., **Location**: ...)',
                suggestion='Consider adding metadata for location, date, reporter'
            ))
    
    def _validate_screenplay_format(self, lines: List[str], result: ValidationResult):
        """Validate screenplay-specific formatting."""
        has_scene_heading = False
        has_dialogue = False
        
        for line in lines:
            if re.match(r'^(INT\.|EXT\.|INT/EXT\.)', line, re.IGNORECASE):
                has_scene_heading = True
            if line.strip() and line.isupper() and len(line.split()) <= 4:
                has_dialogue = True
        
        if not has_scene_heading:
            result.issues.append(ValidationIssue(
                severity='warning',
                category='format',
                message='No standard scene headings found (INT./EXT.)',
                suggestion='Use standard scene headings like "INT. LOCATION - TIME"'
            ))
        
        if not has_dialogue:
            result.issues.append(ValidationIssue(
                severity='info',
                category='format',
                message='No character dialogue detected',
                suggestion='Character names should be in ALL CAPS before dialogue'
            ))
    
    def _check_content_issues(self, content: str, result: ValidationResult):
        """Check for content-related issues."""
        # Check for sensitive content
        for pattern in self.SENSITIVE_CONTENT_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                result.issues.append(ValidationIssue(
                    severity='info',
                    category='content',
                    message=f'Script contains potentially sensitive content: {", ".join(set(matches[:3]))}',
                    suggestion='Ensure content warnings are provided if needed'
                ))
                break
        
        # Check for inconsistent terminology
        for standard, variants in self.TECHNICAL_TERMS.items():
            found_variants = []
            for variant in variants:
                if variant.lower() in content.lower():
                    found_variants.append(variant)
            
            if found_variants:
                result.issues.append(ValidationIssue(
                    severity='info',
                    category='content',
                    message=f'Inconsistent terminology found: {", ".join(found_variants)}',
                    suggestion=f'Consider using standard term: {standard}'
                ))
    
    def _validate_script_structure(self, script: ParsedScript, result: ValidationResult):
        """Validate overall script structure."""
        # Check for required elements
        if not script.scenes:
            result.valid = False
            result.issues.append(ValidationIssue(
                severity='error',
                category='structure',
                message='No scenes found in script'
            ))
        
        if script.word_count < self.MIN_WORD_COUNT:
            result.issues.append(ValidationIssue(
                severity='warning',
                category='content',
                message=f'Script is very short ({script.word_count} words)',
                suggestion=f'Consider expanding - minimum recommended is {self.MIN_WORD_COUNT} words'
            ))
        
        # Check metadata completeness
        if not script.metadata.title:
            result.issues.append(ValidationIssue(
                severity='warning',
                category='structure',
                message='Script title is missing'
            ))
    
    def _validate_timing(self, script: ParsedScript, result: ValidationResult):
        """Validate timing-related aspects."""
        # Check total duration
        if script.total_duration < 30:  # Less than 30 seconds
            result.issues.append(ValidationIssue(
                severity='warning',
                category='timing',
                message=f'Very short total duration: {script.total_duration:.1f} seconds',
                suggestion='Consider expanding content for more substantial production'
            ))
        elif script.total_duration > 1800:  # More than 30 minutes
            result.issues.append(ValidationIssue(
                severity='info',
                category='timing',
                message=f'Long total duration: {script.total_duration/60:.1f} minutes',
                suggestion='Consider breaking into episodes or parts'
            ))
        
        # Check scene durations
        for scene in script.scenes:
            if scene.total_duration < self.MIN_SCENE_DURATION:
                result.issues.append(ValidationIssue(
                    severity='warning',
                    category='timing',
                    message=f'Very short scene duration: {scene.total_duration:.1f} seconds',
                    location=f'Scene {scene.number}',
                    suggestion='Consider combining with adjacent scenes or expanding content'
                ))
            elif scene.total_duration > self.MAX_SCENE_DURATION:
                result.issues.append(ValidationIssue(
                    severity='warning',
                    category='timing',
                    message=f'Very long scene duration: {scene.total_duration/60:.1f} minutes',
                    location=f'Scene {scene.number}',
                    suggestion='Consider breaking into multiple scenes'
                ))
    
    def _validate_characters(self, script: ParsedScript, result: ValidationResult):
        """Validate character-related aspects."""
        if not script.characters:
            result.issues.append(ValidationIssue(
                severity='info',
                category='content',
                message='No named characters found',
                suggestion='Consider adding character names for dialogue'
            ))
        
        # Check for character consistency
        character_variants = {}
        for char in script.characters:
            base_name = char.upper().replace('.', '').replace(' ', '')
            if base_name not in character_variants:
                character_variants[base_name] = []
            character_variants[base_name].append(char)
        
        for base, variants in character_variants.items():
            if len(variants) > 1:
                result.issues.append(ValidationIssue(
                    severity='warning',
                    category='content',
                    message=f'Possible character name variations: {", ".join(variants)}',
                    suggestion='Use consistent character naming throughout'
                ))
    
    def _validate_scene(self, scene: Scene, result: ValidationResult):
        """Validate individual scene."""
        # Check for empty scenes
        if not scene.elements:
            result.issues.append(ValidationIssue(
                severity='error',
                category='structure',
                message='Empty scene found',
                location=f'Scene {scene.number}'
            ))
            return
        
        # Check scene composition
        has_description = any(isinstance(e, SceneDescription) for e in scene.elements)
        has_narrative = any(isinstance(e, Narrative) for e in scene.elements)
        has_dialogue = any(isinstance(e, Dialogue) for e in scene.elements)
        
        if not has_narrative and not has_dialogue:
            result.issues.append(ValidationIssue(
                severity='warning',
                category='content',
                message='Scene contains no narrative or dialogue',
                location=f'Scene {scene.number}',
                suggestion='Add descriptive narrative or character dialogue'
            ))
        
        # Check for very dialogue-heavy or narrative-heavy scenes
        dialogue_count = sum(1 for e in scene.elements if isinstance(e, Dialogue))
        narrative_count = sum(1 for e in scene.elements if isinstance(e, Narrative))
        total_count = len(scene.elements)
        
        if total_count > 5:
            if dialogue_count / total_count > 0.9:
                result.issues.append(ValidationIssue(
                    severity='info',
                    category='content',
                    message='Scene is very dialogue-heavy',
                    location=f'Scene {scene.number}',
                    suggestion='Consider adding narrative descriptions for visual variety'
                ))
            elif narrative_count / total_count > 0.9:
                result.issues.append(ValidationIssue(
                    severity='info',
                    category='content',
                    message='Scene is very narrative-heavy',
                    location=f'Scene {scene.number}',
                    suggestion='Consider adding dialogue to break up narration'
                ))
    
    def _validate_content_consistency(self, script: ParsedScript, result: ValidationResult):
        """Validate content consistency across the script."""
        # Check for unresolved plot elements
        if script.narrative_segments:
            first_half = script.narrative_segments[:len(script.narrative_segments)//2]
            second_half = script.narrative_segments[len(script.narrative_segments)//2:]
            
            # Look for questions or setups in first half
            setup_patterns = [
                r'\?(?:\s|$)',  # Questions
                r'(?:will|might|could|should)\s+\w+',  # Uncertainty
                r'(?:mysterious|unknown|strange)',  # Mystery elements
            ]
            
            unresolved_count = 0
            for pattern in setup_patterns:
                for segment in first_half:
                    if re.search(pattern, segment.content, re.IGNORECASE):
                        unresolved_count += 1
            
            if unresolved_count > 3:
                result.issues.append(ValidationIssue(
                    severity='info',
                    category='content',
                    message='Script contains multiple unresolved elements',
                    suggestion='Ensure major questions and mysteries are addressed'
                ))
    
    def _validate_production_feasibility(self, script: ParsedScript, result: ValidationResult):
        """Validate production feasibility."""
        # Check visual complexity
        unique_visuals = set(script.visual_cues)
        if len(unique_visuals) > 50:
            result.issues.append(ValidationIssue(
                severity='warning',
                category='content',
                message=f'High visual complexity: {len(unique_visuals)} unique visual elements',
                suggestion='Consider consolidating similar visual elements'
            ))
        
        # Check character count for voice production
        if len(script.characters) > 10:
            result.issues.append(ValidationIssue(
                severity='info',
                category='content',
                message=f'Large cast: {len(script.characters)} characters',
                suggestion='Consider consolidating minor characters or using voice doubling'
            ))
        
        # Check for rapid scene changes
        rapid_changes = 0
        for i in range(1, len(script.scenes)):
            if script.scenes[i].total_duration < 30 and script.scenes[i-1].total_duration < 30:
                rapid_changes += 1
        
        if rapid_changes > 3:
            result.issues.append(ValidationIssue(
                severity='warning',
                category='timing',
                message='Multiple rapid scene changes detected',
                suggestion='Consider combining short scenes for smoother flow'
            ))
    
    def _calculate_statistics(self, script: ParsedScript) -> Dict[str, Any]:
        """Calculate validation statistics."""
        stats = {
            'total_scenes': len(script.scenes),
            'total_duration': script.total_duration,
            'average_scene_duration': script.total_duration / len(script.scenes) if script.scenes else 0,
            'word_count': script.word_count,
            'character_count': len(script.characters),
            'dialogue_segments': len(script.dialogue_segments),
            'narrative_segments': len(script.narrative_segments),
            'visual_cues': len(script.visual_cues),
        }
        
        # Calculate dialogue/narrative ratio
        total_segments = len(script.dialogue_segments) + len(script.narrative_segments)
        if total_segments > 0:
            stats['dialogue_ratio'] = len(script.dialogue_segments) / total_segments
            stats['narrative_ratio'] = len(script.narrative_segments) / total_segments
        else:
            stats['dialogue_ratio'] = 0
            stats['narrative_ratio'] = 0
        
        return stats
    
    def _calculate_validation_score(self, result: ValidationResult) -> float:
        """Calculate overall validation score."""
        score = 1.0
        
        # Deduct for issues based on severity
        for issue in result.issues:
            if issue.severity == 'error':
                score -= 0.2
            elif issue.severity == 'warning':
                score -= 0.05
            elif issue.severity == 'info':
                score -= 0.01
        
        # Ensure score stays in valid range
        return max(0.0, min(1.0, score))