"""Unit tests for script parser module."""

import pytest
from src.script_engine.parser import (
    MarkdownScriptParser, ScreenplayScriptParser, ParsedScript,
    ScriptMetadata, Scene, Narrative, Dialogue, SceneDescription
)


class TestMarkdownScriptParser:
    """Test cases for MarkdownScriptParser."""
    
    @pytest.fixture
    def parser(self):
        """Create a parser instance."""
        return MarkdownScriptParser()
    
    @pytest.fixture
    def sample_markdown(self):
        """Sample markdown script content."""
        return """# LOG_0002: THE DESCENT

**Location**: Berlin, Sector 7  
**Date**: Day 47  
**Reporter**: Winston Marek, Resistance Cell Leader

---

The bodies on the rooftop wore white uniforms, arranged in perfect symmetry. Seventeen data scientists from the Prometheus Institute. They'd jumped together at 3:47 AM, synchronized to the millisecond.

I found their final message carved into the concrete: "We created God, and God is hungry."

"We can't stop this." - Sarah whispered.

[SIGNAL LOST]

---

**METADATA**: 
- Duration: 2:47
- Corruption: 12%
- Recovery Status: PARTIAL
"""
    
    def test_parse_metadata(self, parser, sample_markdown):
        """Test metadata extraction."""
        result = parser.parse(sample_markdown)
        
        assert isinstance(result, ParsedScript)
        assert result.metadata.title == "LOG_0002: THE DESCENT"
        assert result.metadata.location == "Berlin, Sector 7"
        assert result.metadata.date == "Day 47"
        assert result.metadata.reporter == "Winston Marek, Resistance Cell Leader"
        assert result.metadata.duration == "2:47"
        assert result.metadata.corruption == "12%"
        assert result.metadata.recovery_status == "PARTIAL"
    
    def test_parse_narrative(self, parser, sample_markdown):
        """Test narrative parsing."""
        result = parser.parse(sample_markdown)
        
        narratives = [e for scene in result.scenes for e in scene.elements 
                     if isinstance(e, Narrative)]
        
        assert len(narratives) > 0
        assert any("bodies on the rooftop" in n.content for n in narratives)
        assert any("final message carved" in n.content for n in narratives)
    
    def test_parse_dialogue(self, parser, sample_markdown):
        """Test dialogue parsing."""
        result = parser.parse(sample_markdown)
        
        dialogues = [e for scene in result.scenes for e in scene.elements 
                    if isinstance(e, Dialogue)]
        
        assert len(dialogues) == 1
        assert dialogues[0].content == "We can't stop this."
        assert dialogues[0].speaker == "Sarah whispered."
    
    def test_parse_scene_transitions(self, parser, sample_markdown):
        """Test scene transition parsing."""
        result = parser.parse(sample_markdown)
        
        scene_descs = [e for scene in result.scenes for e in scene.elements 
                      if isinstance(e, SceneDescription)]
        
        assert any("SIGNAL LOST" in sd.content for sd in scene_descs)
    
    def test_visual_cue_extraction(self, parser, sample_markdown):
        """Test visual cue extraction."""
        result = parser.parse(sample_markdown)
        
        assert len(result.visual_cues) > 0
        assert any("bodies" in cue.lower() for cue in result.visual_cues)
        assert any("rooftop" in cue.lower() for cue in result.visual_cues)
    
    def test_timing_calculation(self, parser, sample_markdown):
        """Test timing estimation."""
        result = parser.parse(sample_markdown)
        
        assert result.total_duration > 0
        assert result.word_count > 0
        
        # Check individual element timings
        for scene in result.scenes:
            assert scene.total_duration > 0
            for element in scene.elements:
                assert element.timing_estimate >= 0
    
    def test_emotional_tone_detection(self, parser, sample_markdown):
        """Test emotional tone detection."""
        result = parser.parse(sample_markdown)
        
        narratives = [e for scene in result.scenes for e in scene.elements 
                     if isinstance(e, Narrative)]
        
        # At least one narrative should have detected emotional tone
        emotional_narratives = [n for n in narratives if n.emotional_tone]
        assert len(emotional_narratives) > 0
        assert any("despair" in n.emotional_tone for n in emotional_narratives)
    
    def test_empty_content(self, parser):
        """Test parsing empty content."""
        result = parser.parse("")
        
        assert result.metadata.title == ""
        assert len(result.scenes) == 0
        assert result.total_duration == 0
        assert result.word_count == 0
    
    def test_minimal_content(self, parser):
        """Test parsing minimal content."""
        minimal = """# Test Script

This is a test."""
        
        result = parser.parse(minimal)
        
        assert result.metadata.title == "Test Script"
        assert len(result.scenes) == 1
        assert len(result.scenes[0].elements) == 1
        assert isinstance(result.scenes[0].elements[0], Narrative)


class TestScreenplayScriptParser:
    """Test cases for ScreenplayScriptParser."""
    
    @pytest.fixture
    def parser(self):
        """Create a parser instance."""
        return ScreenplayScriptParser()
    
    @pytest.fixture
    def sample_screenplay(self):
        """Sample screenplay format content."""
        return """FADE IN:

INT. ABANDONED WAREHOUSE - NIGHT

The warehouse is dark and empty. Broken windows let in shafts of moonlight.

SARAH
(terrified)
We shouldn't be here.

JOHN
We don't have a choice.

They move deeper into the shadows.

CUT TO:

EXT. WAREHOUSE - CONTINUOUS

A car pulls up outside.

FADE OUT."""
    
    def test_parse_screenplay_scenes(self, parser, sample_screenplay):
        """Test screenplay scene parsing."""
        result = parser.parse(sample_screenplay)
        
        assert isinstance(result, ParsedScript)
        assert len(result.scenes) >= 1
        
        # Check for scene descriptions
        scene_descs = [e for scene in result.scenes for e in scene.elements 
                      if isinstance(e, SceneDescription)]
        assert len(scene_descs) > 0
    
    def test_parse_screenplay_dialogue(self, parser, sample_screenplay):
        """Test screenplay dialogue parsing."""
        result = parser.parse(sample_screenplay)
        
        dialogues = [e for scene in result.scenes for e in scene.elements 
                    if isinstance(e, Dialogue)]
        
        assert len(dialogues) == 2
        assert any(d.speaker == "SARAH" for d in dialogues)
        assert any(d.speaker == "JOHN" for d in dialogues)
        assert any("terrified" in str(d.direction) for d in dialogues if d.direction)
    
    def test_parse_screenplay_action(self, parser, sample_screenplay):
        """Test screenplay action parsing."""
        result = parser.parse(sample_screenplay)
        
        narratives = [e for scene in result.scenes for e in scene.elements 
                     if isinstance(e, Narrative)]
        
        assert len(narratives) > 0
        assert any("dark and empty" in n.content for n in narratives)
        assert any("move deeper" in n.content for n in narratives)
    
    def test_character_extraction(self, parser, sample_screenplay):
        """Test character name extraction."""
        result = parser.parse(sample_screenplay)
        
        assert "SARAH" in result.characters
        assert "JOHN" in result.characters
        assert len(result.characters) == 2
    
    def test_format_detection(self, parser):
        """Test format detection between parsers."""
        # This would be better in an integration test
        markdown_parser = MarkdownScriptParser()
        
        markdown_content = "# Title\n\n**Location**: Test"
        screenplay_content = "INT. LOCATION - DAY\n\nAction."
        
        # Each parser should handle its format appropriately
        md_result = markdown_parser.parse(markdown_content)
        sp_result = parser.parse(screenplay_content)
        
        assert md_result.metadata.title == "Title"
        assert len(sp_result.scenes) > 0


class TestParserHelpers:
    """Test parser helper methods."""
    
    def test_timing_calculation(self):
        """Test timing calculation accuracy."""
        parser = MarkdownScriptParser()
        
        # Test narration timing (150 WPM)
        narration = "This is a test narration with exactly ten words here."
        timing = parser.calculate_timing(narration, is_dialogue=False)
        expected = (10 / 150) * 60  # 4 seconds
        assert abs(timing - expected) < 0.1
        
        # Test dialogue timing (180 WPM)
        dialogue = "This is test dialogue."
        timing = parser.calculate_timing(dialogue, is_dialogue=True)
        expected = (4 / 180) * 60  # ~1.33 seconds
        assert abs(timing - expected) < 0.1
    
    def test_visual_cue_extraction(self):
        """Test visual cue extraction patterns."""
        parser = MarkdownScriptParser()
        
        text = """The bodies on the rooftop wore white uniforms. 
                  The facility was burning in the distance.
                  Scientists dressed in lab coats fled the building."""
        
        cues = parser.extract_visual_cues(text)
        
        assert len(cues) > 0
        assert any("bodies" in cue.lower() for cue in cues)
        assert any("rooftop" in cue.lower() for cue in cues)
        assert any("burning" in cue.lower() for cue in cues)
    
    def test_emotional_tone_detection(self):
        """Test emotional tone detection accuracy."""
        parser = MarkdownScriptParser()
        
        # Test despair detection
        despair_text = "They had jumped to their death. All hope was lost."
        tone = parser.detect_emotional_tone(despair_text)
        assert "despair" in tone
        
        # Test fear detection
        fear_text = "Terror gripped them as the nightmare unfolded."
        tone = parser.detect_emotional_tone(fear_text)
        assert "fear" in tone
        
        # Test neutral detection
        neutral_text = "The report was filed at noon."
        tone = parser.detect_emotional_tone(neutral_text)
        assert tone == "neutral"