"""Unit tests for script analyzer module."""

import pytest
from src.script_engine.parser import MarkdownScriptParser, ParsedScript
from src.script_engine.analyzer import (
    ScriptAnalyzer, ScriptAnalysis, SceneAnalysis,
    TimingAnalysis, CharacterAnalysis, ContentAnalysis
)


class TestScriptAnalyzer:
    """Test cases for ScriptAnalyzer."""
    
    @pytest.fixture
    def analyzer(self):
        """Create an analyzer instance."""
        return ScriptAnalyzer()
    
    @pytest.fixture
    def sample_script(self):
        """Create a sample parsed script."""
        parser = MarkdownScriptParser()
        content = """# TEST SCRIPT

**Location**: Test Location
**Date**: Test Date
**Reporter**: Test Reporter

---

The scene opens with a dark atmosphere. Bodies lie scattered across the floor.

"We need to get out of here!" - John shouted.

"It's too late." - Sarah replied.

The AI had taken control. Terror filled the air as they realized their fate.

---

Another scene begins. The survivors huddle together.

"There must be a way." - John said desperately.

They searched for an escape route.

[EXPLOSION]

---"""
        return parser.parse(content)
    
    def test_analyze_basic(self, analyzer, sample_script):
        """Test basic analysis functionality."""
        result = analyzer.analyze(sample_script)
        
        assert isinstance(result, ScriptAnalysis)
        assert result.timing is not None
        assert result.characters is not None
        assert result.scenes is not None
        assert result.content is not None
        assert result.recommendations is not None
        assert result.metrics is not None
    
    def test_scene_analysis(self, analyzer, sample_script):
        """Test individual scene analysis."""
        result = analyzer.analyze(sample_script)
        
        assert len(result.scenes) == len(sample_script.scenes)
        
        for scene_analysis in result.scenes:
            assert isinstance(scene_analysis, SceneAnalysis)
            assert scene_analysis.duration > 0
            assert scene_analysis.word_count > 0
            assert 0 <= scene_analysis.dialogue_ratio <= 1
            assert scene_analysis.pacing in ['fast', 'moderate', 'slow']
            assert 0 <= scene_analysis.emotional_intensity <= 1
            assert 0 <= scene_analysis.visual_complexity <= 1
    
    def test_timing_analysis(self, analyzer, sample_script):
        """Test timing analysis."""
        result = analyzer.analyze(sample_script)
        timing = result.timing
        
        assert isinstance(timing, TimingAnalysis)
        assert timing.total_duration > 0
        assert len(timing.scene_durations) == len(sample_script.scenes)
        assert timing.average_scene_duration > 0
        assert timing.longest_scene[1] >= timing.shortest_scene[1]
        assert len(timing.pacing_chart) == len(sample_script.scenes)
    
    def test_character_analysis(self, analyzer, sample_script):
        """Test character analysis."""
        result = analyzer.analyze(sample_script)
        
        assert len(result.characters) > 0
        
        # Check John and Sarah are analyzed
        character_names = [c.character_name for c in result.characters]
        assert "John shouted." in character_names or "John said desperately." in character_names
        assert "Sarah replied." in character_names
        
        for char in result.characters:
            assert isinstance(char, CharacterAnalysis)
            assert char.line_count > 0
            assert char.word_count > 0
            assert char.speaking_time > 0
            assert len(char.scenes_appeared) > 0
            assert char.first_appearance > 0
            assert char.last_appearance >= char.first_appearance
    
    def test_content_analysis(self, analyzer, sample_script):
        """Test content analysis."""
        result = analyzer.analyze(sample_script)
        content = result.content
        
        assert isinstance(content, ContentAnalysis)
        assert len(content.themes) > 0
        assert len(content.mood_progression) > 0
        assert len(content.suggested_music_cues) > 0
        assert content.narrative_arc in ['rising', 'falling', 'steady', 'climactic']
    
    def test_emotional_intensity_calculation(self, analyzer):
        """Test emotional intensity calculation."""
        parser = MarkdownScriptParser()
        
        # High intensity script
        high_intensity = """# TEST
        
Death and terror filled the air. Panic spread as people screamed in horror."""
        
        script = parser.parse(high_intensity)
        result = analyzer.analyze(script)
        
        # Should have high emotional intensity
        assert result.scenes[0].emotional_intensity > 0.5
        
        # Low intensity script
        low_intensity = """# TEST
        
The room was calm and quiet. People rested peacefully."""
        
        script = parser.parse(low_intensity)
        result = analyzer.analyze(script)
        
        # Should have low emotional intensity
        assert result.scenes[0].emotional_intensity < 0.5
    
    def test_visual_complexity_calculation(self, analyzer, sample_script):
        """Test visual complexity calculation."""
        result = analyzer.analyze(sample_script)
        
        # First scene should have some visual complexity (bodies, dark atmosphere)
        assert result.scenes[0].visual_complexity > 0
    
    def test_theme_detection(self, analyzer):
        """Test theme detection accuracy."""
        parser = MarkdownScriptParser()
        
        # Dystopian theme
        dystopian = """# TEST
        
The AI had taken control. Surveillance cameras watched every move. 
The resistance fought against the machine overlords."""
        
        script = parser.parse(dystopian)
        result = analyzer.analyze(script)
        
        assert 'dystopian' in result.content.themes or 'sci-fi' in result.content.themes
        
        # Horror theme
        horror = """# TEST
        
Terror filled the dark corridors. Screams echoed through the nightmare.
Death lurked in every shadow."""
        
        script = parser.parse(horror)
        result = analyzer.analyze(script)
        
        assert 'horror' in result.content.themes
    
    def test_mood_detection(self, analyzer, sample_script):
        """Test mood detection for scenes."""
        result = analyzer.analyze(sample_script)
        
        # Check mood progression
        moods = [mood for _, mood in result.content.mood_progression]
        assert all(mood in ['tense', 'dark', 'hopeful', 'mysterious', 'action', 'neutral'] 
                  for mood in moods)
    
    def test_music_cue_suggestions(self, analyzer, sample_script):
        """Test music cue generation."""
        result = analyzer.analyze(sample_script)
        
        music_cues = result.content.suggested_music_cues
        assert len(music_cues) > 0
        
        for cue in music_cues:
            assert 'scene' in cue
            assert 'mood' in cue
            assert 'music' in cue
            assert 'timing' in cue
            assert 'style' in cue['music']
            assert 'tempo' in cue['music']
            assert 'instruments' in cue['music']
    
    def test_narrative_arc_detection(self, analyzer):
        """Test narrative arc detection."""
        parser = MarkdownScriptParser()
        
        # Rising arc
        rising = """# TEST
        
---
        
The day began peacefully.

---

Tension started to build.

---

Danger approached rapidly.

---

The crisis reached its peak!"""
        
        script = parser.parse(rising)
        result = analyzer.analyze(script)
        
        # Should detect rising or climactic arc
        assert result.content.narrative_arc in ['rising', 'climactic']
    
    def test_recommendations_generation(self, analyzer, sample_script):
        """Test recommendation generation."""
        result = analyzer.analyze(sample_script)
        
        assert 'voice_synthesis' in result.recommendations
        assert 'visual_generation' in result.recommendations
        assert 'pacing' in result.recommendations
        assert 'production_notes' in result.recommendations
        
        # Should have at least some recommendations
        all_recommendations = []
        for category in result.recommendations.values():
            all_recommendations.extend(category)
        assert len(all_recommendations) > 0
    
    def test_metrics_calculation(self, analyzer, sample_script):
        """Test metrics calculation."""
        result = analyzer.analyze(sample_script)
        metrics = result.metrics
        
        assert 'total_words' in metrics
        assert 'total_duration_seconds' in metrics
        assert 'total_duration_formatted' in metrics
        assert 'scene_count' in metrics
        assert 'character_count' in metrics
        assert 'dialogue_percentage' in metrics
        assert 'average_words_per_minute' in metrics
        assert 'visual_cue_count' in metrics
        assert 'estimated_production_complexity' in metrics
        
        # Check metric values
        assert metrics['total_words'] > 0
        assert metrics['scene_count'] == len(sample_script.scenes)
        assert metrics['estimated_production_complexity'] in ['low', 'medium', 'high']
    
    def test_duration_formatting(self, analyzer):
        """Test duration formatting."""
        # Test various durations
        assert analyzer._format_duration(0) == "0:00"
        assert analyzer._format_duration(30) == "0:30"
        assert analyzer._format_duration(90) == "1:30"
        assert analyzer._format_duration(3665) == "61:05"
    
    def test_empty_script_handling(self, analyzer):
        """Test handling of empty or minimal scripts."""
        parser = MarkdownScriptParser()
        empty_script = parser.parse("")
        
        # Should not crash on empty script
        result = analyzer.analyze(empty_script)
        
        assert result.timing.total_duration == 0
        assert len(result.characters) == 0
        assert len(result.scenes) == 0