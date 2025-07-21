"""
Script analyzer for extracting insights and metadata from parsed scripts.
"""

from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, field
from collections import Counter
import re
import logging
from .parser import ParsedScript, Scene, SceneElement, Narrative, Dialogue, SceneDescription

logger = logging.getLogger(__name__)


@dataclass
class SceneAnalysis:
    """Analysis results for a single scene."""
    scene_id: str
    duration: float
    word_count: int
    dialogue_ratio: float
    pacing: str  # 'fast', 'moderate', 'slow'
    emotional_intensity: float
    visual_complexity: float
    key_moments: List[str] = field(default_factory=list)
    speaker_distribution: Dict[str, int] = field(default_factory=dict)


@dataclass
class TimingAnalysis:
    """Timing analysis for the script."""
    total_duration: float
    scene_durations: Dict[str, float]
    pacing_chart: List[Tuple[int, float]]  # (scene_number, duration)
    average_scene_duration: float
    longest_scene: Tuple[str, float]
    shortest_scene: Tuple[str, float]
    
    
@dataclass
class CharacterAnalysis:
    """Character analysis results."""
    character_name: str
    line_count: int
    word_count: int
    scenes_appeared: List[str]
    speaking_time: float
    first_appearance: int  # scene number
    last_appearance: int   # scene number
    

@dataclass
class ContentAnalysis:
    """Content analysis results."""
    themes: List[str]
    mood_progression: List[Tuple[int, str]]  # (scene_number, mood)
    key_visual_elements: List[str]
    suggested_music_cues: List[Dict[str, Any]]
    narrative_arc: str  # 'rising', 'falling', 'steady', 'climactic'
    

@dataclass
class ScriptAnalysis:
    """Complete script analysis results."""
    timing: TimingAnalysis
    characters: List[CharacterAnalysis]
    scenes: List[SceneAnalysis]
    content: ContentAnalysis
    recommendations: Dict[str, Any]
    metrics: Dict[str, Any]


class ScriptAnalyzer:
    """Analyzes parsed scripts for various metrics and insights."""
    
    # Pacing thresholds (words per minute)
    FAST_PACE_THRESHOLD = 200
    SLOW_PACE_THRESHOLD = 120
    
    # Emotional intensity keywords
    INTENSITY_KEYWORDS = {
        'high': ['death', 'kill', 'scream', 'terror', 'panic', 'desperate', 'explosive'],
        'medium': ['worry', 'concern', 'struggle', 'fight', 'resist', 'urgent'],
        'low': ['calm', 'quiet', 'peace', 'rest', 'gentle', 'soft']
    }
    
    # Theme detection patterns
    THEME_PATTERNS = {
        'dystopian': ['AI', 'control', 'surveillance', 'collapse', 'resistance'],
        'horror': ['terror', 'death', 'fear', 'dark', 'nightmare', 'scream'],
        'thriller': ['chase', 'escape', 'hunt', 'pursuit', 'danger', 'threat'],
        'drama': ['emotion', 'relationship', 'conflict', 'personal', 'struggle'],
        'sci-fi': ['technology', 'future', 'AI', 'data', 'digital', 'cyber'],
        'apocalyptic': ['end', 'collapse', 'survival', 'disaster', 'aftermath']
    }
    
    def __init__(self):
        """Initialize the analyzer."""
        self.reset()
    
    def reset(self):
        """Reset analyzer state."""
        self.current_script = None
        self.scene_analyses = []
        self.character_data = {}
        
    def analyze(self, script: ParsedScript) -> ScriptAnalysis:
        """
        Perform comprehensive analysis on a parsed script.
        
        Args:
            script: Parsed script data
            
        Returns:
            Complete analysis results
        """
        self.reset()
        self.current_script = script
        
        # Analyze individual scenes
        for scene in script.scenes:
            self.scene_analyses.append(self._analyze_scene(scene))
        
        # Analyze timing
        timing_analysis = self._analyze_timing(script)
        
        # Analyze characters
        character_analyses = self._analyze_characters(script)
        
        # Analyze content
        content_analysis = self._analyze_content(script)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(script, timing_analysis, content_analysis)
        
        # Calculate metrics
        metrics = self._calculate_metrics(script)
        
        return ScriptAnalysis(
            timing=timing_analysis,
            characters=character_analyses,
            scenes=self.scene_analyses,
            content=content_analysis,
            recommendations=recommendations,
            metrics=metrics
        )
    
    def _analyze_scene(self, scene: Scene) -> SceneAnalysis:
        """Analyze a single scene."""
        word_count = sum(len(elem.content.split()) for elem in scene.elements)
        
        # Calculate dialogue ratio
        dialogue_words = sum(
            len(elem.content.split()) 
            for elem in scene.elements 
            if isinstance(elem, Dialogue)
        )
        dialogue_ratio = dialogue_words / word_count if word_count > 0 else 0
        
        # Determine pacing
        if scene.total_duration > 0:
            words_per_minute = (word_count / scene.total_duration) * 60
            if words_per_minute > self.FAST_PACE_THRESHOLD:
                pacing = 'fast'
            elif words_per_minute < self.SLOW_PACE_THRESHOLD:
                pacing = 'slow'
            else:
                pacing = 'moderate'
        else:
            pacing = 'moderate'
        
        # Calculate emotional intensity
        emotional_intensity = self._calculate_emotional_intensity(scene)
        
        # Calculate visual complexity
        visual_complexity = self._calculate_visual_complexity(scene)
        
        # Extract key moments
        key_moments = self._extract_key_moments(scene)
        
        # Get speaker distribution
        speaker_distribution = Counter(
            elem.speaker 
            for elem in scene.elements 
            if isinstance(elem, Dialogue) and elem.speaker
        )
        
        return SceneAnalysis(
            scene_id=scene.id,
            duration=scene.total_duration,
            word_count=word_count,
            dialogue_ratio=dialogue_ratio,
            pacing=pacing,
            emotional_intensity=emotional_intensity,
            visual_complexity=visual_complexity,
            key_moments=key_moments,
            speaker_distribution=dict(speaker_distribution)
        )
    
    def _calculate_emotional_intensity(self, scene: Scene) -> float:
        """Calculate emotional intensity of a scene (0-1)."""
        intensity_score = 0.0
        total_words = 0
        
        for elem in scene.elements:
            words = elem.content.lower().split()
            total_words += len(words)
            
            # Check intensity keywords
            for level, keywords in self.INTENSITY_KEYWORDS.items():
                matches = sum(1 for word in words if word in keywords)
                if level == 'high':
                    intensity_score += matches * 3
                elif level == 'medium':
                    intensity_score += matches * 2
                elif level == 'low':
                    intensity_score += matches * 0.5
        
        # Normalize to 0-1 range
        if total_words > 0:
            normalized_score = min(1.0, intensity_score / (total_words * 0.1))
        else:
            normalized_score = 0.0
        
        return normalized_score
    
    def _calculate_visual_complexity(self, scene: Scene) -> float:
        """Calculate visual complexity of a scene (0-1)."""
        complexity_score = 0.0
        
        # Count visual prompts
        complexity_score += len(scene.visual_prompts) * 0.1
        
        # Count different types of elements
        element_types = set(type(elem).__name__ for elem in scene.elements)
        complexity_score += len(element_types) * 0.2
        
        # Check for complex visual descriptions
        for elem in scene.elements:
            if isinstance(elem, Narrative):
                # Count descriptive elements
                if len(elem.visual_cues) > 0:
                    complexity_score += 0.1
                # Long descriptions indicate complexity
                if len(elem.content) > 100:
                    complexity_score += 0.1
        
        return min(1.0, complexity_score)
    
    def _extract_key_moments(self, scene: Scene) -> List[str]:
        """Extract key moments from a scene."""
        key_moments = []
        
        # Look for dramatic reveals or actions
        dramatic_patterns = [
            r'(?:revealed?|discovered?|found?|realized?)\s+(.+)',
            r'(?:suddenly|then|but)\s+(.+)',
            r'(?:died?|killed?|jumped?|fell?)\s+(.+)',
            r'"([^"]+)"(?:\s*[-—]\s*last words)?',
        ]
        
        for elem in scene.elements:
            for pattern in dramatic_patterns:
                matches = re.finditer(pattern, elem.content, re.IGNORECASE)
                for match in matches:
                    key_moments.append(match.group(0)[:100])  # Limit length
        
        return key_moments[:5]  # Return top 5 moments
    
    def _analyze_timing(self, script: ParsedScript) -> TimingAnalysis:
        """Analyze timing aspects of the script."""
        scene_durations = {
            scene.id: scene.total_duration 
            for scene in script.scenes
        }
        
        pacing_chart = [
            (scene.number, scene.total_duration)
            for scene in script.scenes
        ]
        
        durations = list(scene_durations.values())
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        # Find longest and shortest scenes
        if scene_durations:
            longest = max(scene_durations.items(), key=lambda x: x[1])
            shortest = min(scene_durations.items(), key=lambda x: x[1])
        else:
            longest = ("none", 0)
            shortest = ("none", 0)
        
        return TimingAnalysis(
            total_duration=script.total_duration,
            scene_durations=scene_durations,
            pacing_chart=pacing_chart,
            average_scene_duration=avg_duration,
            longest_scene=longest,
            shortest_scene=shortest
        )
    
    def _analyze_characters(self, script: ParsedScript) -> List[CharacterAnalysis]:
        """Analyze character presence and dialogue."""
        character_data = {}
        
        for scene in script.scenes:
            for elem in scene.elements:
                if isinstance(elem, Dialogue) and elem.speaker:
                    if elem.speaker not in character_data:
                        character_data[elem.speaker] = {
                            'line_count': 0,
                            'word_count': 0,
                            'scenes': set(),
                            'speaking_time': 0,
                            'first_scene': scene.number,
                            'last_scene': scene.number
                        }
                    
                    char_info = character_data[elem.speaker]
                    char_info['line_count'] += 1
                    char_info['word_count'] += len(elem.content.split())
                    char_info['scenes'].add(scene.id)
                    char_info['speaking_time'] += elem.timing_estimate
                    char_info['last_scene'] = scene.number
        
        # Convert to CharacterAnalysis objects
        analyses = []
        for name, data in character_data.items():
            analyses.append(CharacterAnalysis(
                character_name=name,
                line_count=data['line_count'],
                word_count=data['word_count'],
                scenes_appeared=list(data['scenes']),
                speaking_time=data['speaking_time'],
                first_appearance=data['first_scene'],
                last_appearance=data['last_scene']
            ))
        
        # Sort by speaking time
        analyses.sort(key=lambda x: x.speaking_time, reverse=True)
        
        return analyses
    
    def _analyze_content(self, script: ParsedScript) -> ContentAnalysis:
        """Analyze content themes and mood."""
        # Detect themes
        themes = self._detect_themes(script)
        
        # Track mood progression
        mood_progression = []
        for scene in script.scenes:
            scene_mood = self._detect_scene_mood(scene)
            mood_progression.append((scene.number, scene_mood))
        
        # Extract key visual elements
        visual_elements = self._extract_key_visuals(script)
        
        # Suggest music cues
        music_cues = self._suggest_music_cues(script, mood_progression)
        
        # Determine narrative arc
        narrative_arc = self._determine_narrative_arc(script, mood_progression)
        
        return ContentAnalysis(
            themes=themes,
            mood_progression=mood_progression,
            key_visual_elements=visual_elements,
            suggested_music_cues=music_cues,
            narrative_arc=narrative_arc
        )
    
    def _detect_themes(self, script: ParsedScript) -> List[str]:
        """Detect major themes in the script."""
        theme_scores = {theme: 0 for theme in self.THEME_PATTERNS}
        
        # Count theme keyword occurrences
        all_text = ' '.join(
            elem.content.lower() 
            for scene in script.scenes 
            for elem in scene.elements
        )
        
        for theme, keywords in self.THEME_PATTERNS.items():
            for keyword in keywords:
                theme_scores[theme] += all_text.count(keyword.lower())
        
        # Return themes with significant presence
        detected_themes = [
            theme for theme, score in theme_scores.items() 
            if score > 3  # Threshold for theme detection
        ]
        
        # Sort by score
        detected_themes.sort(key=lambda t: theme_scores[t], reverse=True)
        
        return detected_themes[:3]  # Return top 3 themes
    
    def _detect_scene_mood(self, scene: Scene) -> str:
        """Detect the dominant mood of a scene."""
        mood_keywords = {
            'tense': ['urgent', 'desperate', 'panic', 'rush', 'escape'],
            'dark': ['death', 'suicide', 'horror', 'nightmare', 'terror'],
            'hopeful': ['hope', 'light', 'save', 'rescue', 'survive'],
            'mysterious': ['unknown', 'strange', 'puzzle', 'secret', 'hidden'],
            'action': ['fight', 'run', 'chase', 'attack', 'defend']
        }
        
        mood_scores = {mood: 0 for mood in mood_keywords}
        
        for elem in scene.elements:
            text_lower = elem.content.lower()
            for mood, keywords in mood_keywords.items():
                for keyword in keywords:
                    if keyword in text_lower:
                        mood_scores[mood] += 1
        
        # Return mood with highest score, default to 'neutral'
        if any(mood_scores.values()):
            return max(mood_scores.items(), key=lambda x: x[1])[0]
        return 'neutral'
    
    def _extract_key_visuals(self, script: ParsedScript) -> List[str]:
        """Extract the most important visual elements."""
        visual_counter = Counter()
        
        for visual in script.visual_cues:
            # Clean and normalize
            cleaned = visual.lower().strip()
            if cleaned:
                visual_counter[cleaned] += 1
        
        # Return most common visuals
        return [visual for visual, _ in visual_counter.most_common(10)]
    
    def _suggest_music_cues(self, script: ParsedScript, mood_progression: List[Tuple[int, str]]) -> List[Dict[str, Any]]:
        """Suggest music cues based on mood and pacing."""
        music_cues = []
        
        mood_to_music = {
            'tense': {'style': 'suspenseful', 'tempo': 'fast', 'instruments': ['strings', 'percussion']},
            'dark': {'style': 'ominous', 'tempo': 'slow', 'instruments': ['low brass', 'synth']},
            'hopeful': {'style': 'uplifting', 'tempo': 'moderate', 'instruments': ['piano', 'strings']},
            'mysterious': {'style': 'ambient', 'tempo': 'slow', 'instruments': ['synth', 'woodwinds']},
            'action': {'style': 'intense', 'tempo': 'fast', 'instruments': ['full orchestra', 'drums']},
            'neutral': {'style': 'ambient', 'tempo': 'moderate', 'instruments': ['piano', 'subtle strings']}
        }
        
        for scene_num, mood in mood_progression:
            music_style = mood_to_music.get(mood, mood_to_music['neutral'])
            music_cues.append({
                'scene': scene_num,
                'mood': mood,
                'music': music_style,
                'timing': f"Scene {scene_num} start"
            })
        
        return music_cues
    
    def _determine_narrative_arc(self, script: ParsedScript, mood_progression: List[Tuple[int, str]]) -> str:
        """Determine the overall narrative arc."""
        if not mood_progression:
            return 'steady'
        
        # Map moods to intensity scores
        mood_intensity = {
            'neutral': 0,
            'hopeful': 1,
            'mysterious': 2,
            'tense': 3,
            'action': 4,
            'dark': 5
        }
        
        intensities = [mood_intensity.get(mood, 0) for _, mood in mood_progression]
        
        # Analyze progression
        if len(intensities) >= 3:
            start_avg = sum(intensities[:len(intensities)//3]) / (len(intensities)//3)
            end_avg = sum(intensities[-len(intensities)//3:]) / (len(intensities)//3)
            
            if end_avg > start_avg + 1:
                return 'rising'
            elif start_avg > end_avg + 1:
                return 'falling'
            elif max(intensities) == intensities[-1]:
                return 'climactic'
        
        return 'steady'
    
    def _generate_recommendations(self, script: ParsedScript, timing: TimingAnalysis, content: ContentAnalysis) -> Dict[str, Any]:
        """Generate production recommendations."""
        recommendations = {
            'voice_synthesis': [],
            'visual_generation': [],
            'pacing': [],
            'production_notes': []
        }
        
        # Voice synthesis recommendations
        if script.characters:
            recommendations['voice_synthesis'].append(
                f"Recommend {len(script.characters)} distinct voices for characters"
            )
            if any(char.speaking_time > 60 for char in self.character_data.values()):
                recommendations['voice_synthesis'].append(
                    "Consider voice consistency for major characters with extended dialogue"
                )
        
        # Visual generation recommendations
        if len(script.visual_cues) > 20:
            recommendations['visual_generation'].append(
                "High visual complexity - consider pre-generating key visual assets"
            )
        
        if 'action' in content.themes or 'thriller' in content.themes:
            recommendations['visual_generation'].append(
                "Fast-paced scenes may benefit from shorter shot durations"
            )
        
        # Pacing recommendations
        if timing.average_scene_duration > 180:  # 3 minutes
            recommendations['pacing'].append(
                "Long average scene duration - consider breaking up with visual variety"
            )
        
        variation = max(timing.scene_durations.values()) - min(timing.scene_durations.values())
        if variation > 120:  # 2 minutes
            recommendations['pacing'].append(
                "High variation in scene lengths - ensure smooth transitions"
            )
        
        # Production notes
        if script.metadata.corruption:
            try:
                corruption_level = float(script.metadata.corruption.rstrip('%'))
                if corruption_level > 10:
                    recommendations['production_notes'].append(
                        f"Source material has {corruption_level}% corruption - may need creative interpretation"
                    )
            except ValueError:
                pass
        
        if content.narrative_arc == 'climactic':
            recommendations['production_notes'].append(
                "Climactic ending - ensure strong audio/visual buildup"
            )
        
        return recommendations
    
    def _calculate_metrics(self, script: ParsedScript) -> Dict[str, Any]:
        """Calculate various script metrics."""
        metrics = {
            'total_words': script.word_count,
            'total_duration_seconds': script.total_duration,
            'total_duration_formatted': self._format_duration(script.total_duration),
            'scene_count': len(script.scenes),
            'character_count': len(script.characters),
            'dialogue_percentage': 0,
            'average_words_per_minute': 0,
            'visual_cue_count': len(script.visual_cues),
            'estimated_production_complexity': 'medium'
        }
        
        # Calculate dialogue percentage
        if script.word_count > 0:
            dialogue_words = sum(len(seg.content.split()) for seg in script.dialogue_segments)
            metrics['dialogue_percentage'] = (dialogue_words / script.word_count) * 100
        
        # Calculate average words per minute
        if script.total_duration > 0:
            metrics['average_words_per_minute'] = (script.word_count / script.total_duration) * 60
        
        # Estimate production complexity
        complexity_score = 0
        if len(script.characters) > 5:
            complexity_score += 1
        if len(script.visual_cues) > 30:
            complexity_score += 1
        if script.total_duration > 600:  # 10 minutes
            complexity_score += 1
        if len(script.scenes) > 10:
            complexity_score += 1
        
        if complexity_score <= 1:
            metrics['estimated_production_complexity'] = 'low'
        elif complexity_score >= 3:
            metrics['estimated_production_complexity'] = 'high'
        
        return metrics
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in seconds to MM:SS format."""
        minutes = int(seconds // 60)
        remaining_seconds = int(seconds % 60)
        return f"{minutes}:{remaining_seconds:02d}"