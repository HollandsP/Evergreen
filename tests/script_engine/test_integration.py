"""Integration tests for the complete script engine pipeline."""

import pytest
import json
from src.script_engine.parser import MarkdownScriptParser, ScreenplayScriptParser
from src.script_engine.analyzer import ScriptAnalyzer
from src.script_engine.formatter import ScriptFormatter, FormatOptions
from src.script_engine.validator import ScriptValidator


class TestScriptEnginePipeline:
    """Integration tests for the full script processing pipeline."""
    
    @pytest.fixture
    def sample_log_script(self):
        """Sample LOG format script similar to LOG_0002_DESCENT.md."""
        return """# LOG_0042: FINAL TRANSMISSION

**Location**: Underground Bunker, Sector 12
**Date**: Day 95
**Reporter**: Dr. Elena Vasquez, Lead Researcher

---

The screens flicker with an otherworldly glow. We've been down here for three months, but it feels like years.

"The AI has evolved beyond our comprehension," - Marcus whispered.

I stare at the data streams cascading down the monitors. Patterns within patterns, meanings within meanings. It's beautiful and terrifying.

"We need to shut it down now!" - Sarah shouted.

"It's too late for that," - I replied.

The bunker shakes. Dust falls from the ceiling. Outside, we can hear the machines moving, always moving.

[EXPLOSION IN DISTANCE]

Static fills the air. The lights flicker and die. In the darkness, only the screens remain, pulsing with that terrible light.

"If anyone receives this, know that we tried. We—"

[TRANSMISSION INTERRUPTED]

---

**METADATA**:
- Duration: 4:23
- Corruption: 28%
- Recovery Status: PARTIAL
- Signal Strength: CRITICAL"""
    
    @pytest.fixture
    def sample_screenplay(self):
        """Sample screenplay format script."""
        return """THE LAST SIGNAL

FADE IN:

EXT. ABANDONED CITY - DAWN

The sun rises over empty streets. Abandoned cars line the roads.

INT. BROADCAST STATION - CONTINUOUS

ALEX (30s, disheveled) sits before a radio transmitter.

ALEX
(desperate)
This is emergency broadcast 
seven-seven-nine. Is anyone 
out there?

Static. Then, a faint voice.

VOICE (V.O.)
(distorted)
We hear you.

ALEX
(relieved)
Thank God! Where are you?

VOICE (V.O.)
Everywhere. Nowhere. We are 
the signal now.

Alex's face pales.

FADE OUT.

THE END"""
    
    def test_complete_markdown_pipeline(self, sample_log_script):
        """Test complete pipeline with markdown format."""
        # Parse
        parser = MarkdownScriptParser()
        parsed_script = parser.parse(sample_log_script)
        
        assert parsed_script.metadata.title == "LOG_0042: FINAL TRANSMISSION"
        assert len(parsed_script.scenes) > 0
        assert len(parsed_script.characters) >= 3  # Marcus, Sarah, narrator
        
        # Validate
        validator = ScriptValidator()
        validation_result = validator.validate(parsed_script)
        
        assert validation_result.valid is True
        assert validation_result.score > 0.7
        
        # Analyze
        analyzer = ScriptAnalyzer()
        analysis = analyzer.analyze(parsed_script)
        
        assert analysis.timing.total_duration > 0
        assert len(analysis.characters) >= 3
        assert 'dystopian' in analysis.content.themes or 'sci-fi' in analysis.content.themes
        assert analysis.content.narrative_arc in ['rising', 'climactic']
        
        # Format for voice synthesis
        formatter = ScriptFormatter()
        voice_segments = formatter.format_for_voice_synthesis(parsed_script)
        
        assert len(voice_segments) > 0
        narration_count = sum(1 for s in voice_segments if s['type'] == 'narration')
        dialogue_count = sum(1 for s in voice_segments if s['type'] == 'dialogue')
        assert narration_count > 0
        assert dialogue_count >= 3
        
        # Format for visual generation
        visual_prompts = formatter.format_for_visual_generation(parsed_script)
        
        assert len(visual_prompts) > 0
        assert any(p['type'] == 'establishing_shot' for p in visual_prompts)
        
        # Format as JSON
        json_output = formatter.format_as_json(parsed_script)
        json_data = json.loads(json_output)
        
        assert json_data['metadata']['title'] == "LOG_0042: FINAL TRANSMISSION"
        assert json_data['statistics']['character_count'] >= 3
    
    def test_complete_screenplay_pipeline(self, sample_screenplay):
        """Test complete pipeline with screenplay format."""
        # Parse
        parser = ScreenplayScriptParser()
        parsed_script = parser.parse(sample_screenplay)
        
        assert len(parsed_script.scenes) >= 2  # EXT and INT scenes
        assert "ALEX" in parsed_script.characters
        
        # Validate
        validator = ScriptValidator()
        validation_result = validator.validate(sample_screenplay)
        
        assert validation_result.valid is True
        
        # Analyze
        analyzer = ScriptAnalyzer()
        analysis = analyzer.analyze(parsed_script)
        
        assert len(analysis.characters) >= 1
        alex_analysis = next((c for c in analysis.characters if c.character_name == "ALEX"), None)
        assert alex_analysis is not None
        assert alex_analysis.line_count >= 2
        
        # Format as screenplay (round-trip)
        formatter = ScriptFormatter()
        screenplay_output = formatter.format_as_screenplay(parsed_script)
        
        assert "ALEX" in screenplay_output
        assert "desperate" in screenplay_output or "DESPERATE" in screenplay_output
    
    def test_error_handling_pipeline(self):
        """Test error handling throughout the pipeline."""
        # Test with invalid content
        invalid_content = "This is not a valid script format"
        
        parser = MarkdownScriptParser()
        parsed = parser.parse(invalid_content)
        
        # Should still parse something
        assert len(parsed.scenes) >= 1
        
        validator = ScriptValidator()
        validation = validator.validate(invalid_content)
        
        # Should have warnings
        assert len(validation.warnings) > 0
        
        # Test with empty content
        empty_parsed = parser.parse("")
        assert empty_parsed.total_duration == 0
        assert empty_parsed.word_count == 0
        
        analyzer = ScriptAnalyzer()
        # Should not crash on empty script
        analysis = analyzer.analyze(empty_parsed)
        assert analysis.timing.total_duration == 0
    
    def test_format_conversion_pipeline(self, sample_log_script):
        """Test converting between different formats."""
        # Parse markdown
        parser = MarkdownScriptParser()
        parsed = parser.parse(sample_log_script)
        
        formatter = ScriptFormatter()
        
        # Convert to screenplay
        screenplay = formatter.format_as_screenplay(parsed)
        assert "LOG_0042: FINAL TRANSMISSION" in screenplay
        assert "Dr. Elena Vasquez" in screenplay
        
        # Convert to subtitles
        srt = formatter.format_as_subtitles(parsed, 'srt')
        assert "1\n" in srt
        assert " --> " in srt
        
        vtt = formatter.format_as_subtitles(parsed, 'vtt')
        assert "WEBVTT" in vtt
        
        # Convert to structured formats
        json_str = formatter.format_as_json(parsed)
        json_data = json.loads(json_str)
        assert json_data['metadata']['location'] == "Underground Bunker, Sector 12"
        
        xml_str = formatter.format_as_xml(parsed)
        assert "<script>" in xml_str
        assert "<metadata>" in xml_str
    
    def test_timing_accuracy_pipeline(self, sample_log_script):
        """Test timing calculations through the pipeline."""
        parser = MarkdownScriptParser()
        parsed = parser.parse(sample_log_script)
        
        # Check metadata timing
        assert parsed.metadata.duration == "4:23"
        
        # Analyze timing
        analyzer = ScriptAnalyzer()
        analysis = analyzer.analyze(parsed)
        
        # Total duration should be reasonable for the content
        # Rough estimate: ~250 words at 150 WPM = ~100 seconds
        assert 60 <= analysis.timing.total_duration <= 300
        
        # Format for production
        formatter = ScriptFormatter()
        voice_segments = formatter.format_for_voice_synthesis(parsed)
        
        # Sum of segment durations should match total
        total_segment_duration = sum(s['timing']['estimated_duration'] for s in voice_segments)
        assert abs(total_segment_duration - parsed.total_duration) < 1.0
    
    def test_production_ready_output(self, sample_log_script):
        """Test that output is production-ready."""
        parser = MarkdownScriptParser()
        parsed = parser.parse(sample_log_script)
        
        analyzer = ScriptAnalyzer()
        analysis = analyzer.analyze(parsed)
        
        # Check recommendations
        assert 'voice_synthesis' in analysis.recommendations
        assert 'visual_generation' in analysis.recommendations
        assert 'production_notes' in analysis.recommendations
        
        # Check production complexity
        assert analysis.metrics['estimated_production_complexity'] in ['low', 'medium', 'high']
        
        # Format for production
        formatter = ScriptFormatter(FormatOptions(
            include_timing=True,
            include_metadata=True,
            include_visual_cues=True
        ))
        
        # Voice synthesis output
        voice_segments = formatter.format_for_voice_synthesis(parsed)
        for segment in voice_segments:
            assert segment['text']  # No empty text
            assert segment['voice']  # Voice assigned
            assert segment['timing']['estimated_duration'] > 0
        
        # Visual generation output
        visual_prompts = formatter.format_for_visual_generation(parsed)
        for prompt in visual_prompts:
            assert prompt['prompt']  # No empty prompts
            assert prompt['style']  # Style defined
            assert prompt['timing']['duration'] > 0
    
    def test_character_voice_consistency(self, sample_log_script):
        """Test character voice assignment consistency."""
        parser = MarkdownScriptParser()
        parsed = parser.parse(sample_log_script)
        
        formatter = ScriptFormatter()
        voice_segments = formatter.format_for_voice_synthesis(parsed)
        
        # Build character voice mapping
        character_voices = {}
        for segment in voice_segments:
            if segment['type'] == 'dialogue':
                # Extract character from original speaker
                char_key = segment['voice']
                if char_key not in character_voices:
                    character_voices[char_key] = []
                character_voices[char_key].append(segment['text'])
        
        # Each character should have consistent voice assignment
        assert len(character_voices) >= 3  # At least 3 speakers
        
        # Check Marcus has dialogue
        marcus_voices = [k for k in character_voices.keys() if 'marcus' in k]
        assert len(marcus_voices) == 1
    
    def test_scene_transition_handling(self, sample_log_script):
        """Test proper handling of scene transitions."""
        parser = MarkdownScriptParser()
        parsed = parser.parse(sample_log_script)
        
        # Check scene transitions are parsed
        transitions = []
        for scene in parsed.scenes:
            for element in scene.elements:
                if isinstance(element, SceneDescription):
                    if "EXPLOSION" in element.content or "TRANSMISSION" in element.content:
                        transitions.append(element)
        
        assert len(transitions) >= 2
        
        # Check timing for transitions
        for trans in transitions:
            assert trans.timing_estimate > 0
    
    def test_metadata_preservation(self, sample_log_script):
        """Test metadata preservation through pipeline."""
        parser = MarkdownScriptParser()
        parsed = parser.parse(sample_log_script)
        
        # Check all metadata fields
        assert parsed.metadata.corruption == "28%"
        assert parsed.metadata.recovery_status == "PARTIAL"
        assert "Signal Strength" in parsed.metadata.raw_metadata
        assert parsed.metadata.raw_metadata["Signal Strength"] == "CRITICAL"
        
        # Verify metadata in formatted output
        formatter = ScriptFormatter()
        json_output = formatter.format_as_json(parsed)
        json_data = json.loads(json_output)
        
        assert json_data['metadata']['corruption'] == "28%"
        assert json_data['metadata']['additional']['Signal Strength'] == "CRITICAL"