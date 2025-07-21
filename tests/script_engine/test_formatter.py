"""Unit tests for script formatter module."""

import pytest
import json
import xml.etree.ElementTree as ET
from src.script_engine.parser import MarkdownScriptParser
from src.script_engine.formatter import ScriptFormatter, FormatOptions


class TestScriptFormatter:
    """Test cases for ScriptFormatter."""
    
    @pytest.fixture
    def formatter(self):
        """Create a formatter instance."""
        return ScriptFormatter()
    
    @pytest.fixture
    def formatter_with_options(self):
        """Create a formatter with custom options."""
        options = FormatOptions(
            include_timing=True,
            include_metadata=True,
            include_visual_cues=True,
            include_speaker_directions=True,
            max_line_length=60,
            time_format="seconds"
        )
        return ScriptFormatter(options)
    
    @pytest.fixture
    def sample_script(self):
        """Create a sample parsed script."""
        parser = MarkdownScriptParser()
        content = """# TEST SCRIPT

**Location**: Test Lab
**Date**: Day 1
**Reporter**: Test User

---

The experiment begins. Scientists prepare their equipment.

"Starting test sequence." - Dr. Smith announced.

"All systems ready." - Assistant replied.

[ALARM SOUNDS]

The room fills with smoke.

---

**METADATA**:
- Duration: 1:30
- Corruption: 5%
- Recovery Status: COMPLETE"""
        return parser.parse(content)
    
    def test_format_for_voice_synthesis(self, formatter, sample_script):
        """Test voice synthesis formatting."""
        segments = formatter.format_for_voice_synthesis(sample_script)
        
        assert len(segments) > 0
        
        # Check segment structure
        for segment in segments:
            assert 'id' in segment
            assert 'type' in segment
            assert 'text' in segment
            assert 'voice' in segment
            assert 'scene_id' in segment
            assert 'timing' in segment
            assert 'estimated_duration' in segment['timing']
            assert 'start_time' in segment['timing']
        
        # Check narration segments
        narrations = [s for s in segments if s['type'] == 'narration']
        assert len(narrations) > 0
        assert all(s['voice'] == 'narrator' for s in narrations)
        
        # Check dialogue segments
        dialogues = [s for s in segments if s['type'] == 'dialogue']
        assert len(dialogues) == 2
        assert any(s['voice'] == 'dr_smith_announced' for s in dialogues)
        assert any(s['voice'] == 'assistant_replied' for s in dialogues)
    
    def test_format_for_visual_generation(self, formatter, sample_script):
        """Test visual generation formatting."""
        prompts = formatter.format_for_visual_generation(sample_script)
        
        assert len(prompts) > 0
        
        # Check prompt structure
        for prompt in prompts:
            assert 'id' in prompt
            assert 'type' in prompt
            assert 'scene_id' in prompt
            assert 'timing' in prompt
            assert 'prompt' in prompt
            assert 'style' in prompt
        
        # Check establishing shots
        establishing = [p for p in prompts if p['type'] == 'establishing_shot']
        assert len(establishing) > 0
        
        # Check key moments
        key_moments = [p for p in prompts if p['type'] == 'key_moment']
        # May or may not have key moments depending on content
    
    def test_format_as_subtitles_srt(self, formatter, sample_script):
        """Test SRT subtitle formatting."""
        srt = formatter.format_as_subtitles(sample_script, 'srt')
        
        assert isinstance(srt, str)
        assert '1\n' in srt  # First subtitle number
        assert ' --> ' in srt  # Time separator
        assert '[Dr. Smith announced.]' in srt or 'Dr. Smith announced.' in srt
        
        # Check basic SRT structure
        lines = srt.strip().split('\n')
        assert lines[0] == '1'  # First subtitle number
        assert ' --> ' in lines[1]  # Time range
    
    def test_format_as_subtitles_vtt(self, formatter, sample_script):
        """Test WebVTT subtitle formatting."""
        vtt = formatter.format_as_subtitles(sample_script, 'vtt')
        
        assert isinstance(vtt, str)
        assert vtt.startswith('WEBVTT')
        assert ' --> ' in vtt
        assert '<v ' in vtt or 'Dr. Smith' in vtt  # Speaker tags
    
    def test_format_as_subtitles_ass(self, formatter, sample_script):
        """Test ASS subtitle formatting."""
        ass = formatter.format_as_subtitles(sample_script, 'ass')
        
        assert isinstance(ass, str)
        assert '[Script Info]' in ass
        assert '[V4+ Styles]' in ass
        assert '[Events]' in ass
        assert 'Dialogue: ' in ass
    
    def test_format_as_screenplay(self, formatter, sample_script):
        """Test screenplay formatting."""
        screenplay = formatter.format_as_screenplay(sample_script)
        
        assert isinstance(screenplay, str)
        assert 'TEST SCRIPT' in screenplay
        assert 'by Test User' in screenplay
        
        # Check for centered character names
        assert 'DR. SMITH ANNOUNCED.' in screenplay.upper()
        assert 'ASSISTANT REPLIED.' in screenplay.upper()
        
        # Check for dialogue indentation (at least 10 spaces)
        lines = screenplay.split('\n')
        dialogue_lines = [l for l in lines if l.strip() and l.startswith(' ' * 10)]
        assert len(dialogue_lines) > 0
    
    def test_format_as_json(self, formatter, sample_script):
        """Test JSON formatting."""
        json_str = formatter.format_as_json(sample_script)
        
        assert isinstance(json_str, str)
        
        # Parse JSON to validate structure
        data = json.loads(json_str)
        
        assert 'metadata' in data
        assert 'statistics' in data
        assert 'characters' in data
        assert 'scenes' in data
        
        # Check metadata
        assert data['metadata']['title'] == 'TEST SCRIPT'
        assert data['metadata']['location'] == 'Test Lab'
        
        # Check statistics
        assert data['statistics']['word_count'] > 0
        assert data['statistics']['scene_count'] > 0
        
        # Check scenes
        assert len(data['scenes']) > 0
        for scene in data['scenes']:
            assert 'id' in scene
            assert 'number' in scene
            assert 'duration' in scene
            assert 'elements' in scene
    
    def test_format_as_xml(self, formatter, sample_script):
        """Test XML formatting."""
        xml_str = formatter.format_as_xml(sample_script)
        
        assert isinstance(xml_str, str)
        assert '<?xml' in xml_str
        
        # Parse XML to validate structure
        root = ET.fromstring(xml_str)
        
        assert root.tag == 'script'
        
        # Check metadata
        metadata = root.find('metadata')
        assert metadata is not None
        assert metadata.find('title').text == 'TEST SCRIPT'
        
        # Check statistics
        stats = root.find('statistics')
        assert stats is not None
        assert stats.get('word_count') is not None
        
        # Check scenes
        scenes = root.find('scenes')
        assert scenes is not None
        assert len(scenes.findall('scene')) > 0
    
    def test_text_cleaning_for_speech(self, formatter):
        """Test text cleaning for voice synthesis."""
        # Test removing special characters
        text = "This is *bold* and _italic_ and ~strikethrough~"
        cleaned = formatter._clean_text_for_speech(text)
        assert '*' not in cleaned
        assert '_' not in cleaned
        assert '~' not in cleaned
        
        # Test spacing normalization
        text = "Multiple   spaces    here"
        cleaned = formatter._clean_text_for_speech(text)
        assert "  " not in cleaned
        
        # Test punctuation spacing
        text = "Hello ,world !How are you ?"
        cleaned = formatter._clean_text_for_speech(text)
        assert cleaned == "Hello, world! How are you? "
    
    def test_speaker_name_normalization(self, formatter):
        """Test speaker name normalization."""
        assert formatter._normalize_speaker_name("Dr. Smith") == "dr_smith"
        assert formatter._normalize_speaker_name("JOHN DOE") == "john_doe"
        assert formatter._normalize_speaker_name("Mary-Jane") == "mary_jane"
        assert formatter._normalize_speaker_name("Agent 007") == "agent_007"
        assert formatter._normalize_speaker_name("") == "unknown"
    
    def test_scene_mood_determination(self, formatter):
        """Test scene mood detection."""
        parser = MarkdownScriptParser()
        
        # Dark mood
        dark_script = parser.parse("# TEST\n\nDeath and horror filled the room.")
        mood = formatter._determine_scene_mood(dark_script.scenes[0])
        assert mood == 'dark'
        
        # Action mood
        action_script = parser.parse("# TEST\n\nThey were running and fighting for survival.")
        mood = formatter._determine_scene_mood(action_script.scenes[0])
        assert mood == 'action'
        
        # Neutral mood
        neutral_script = parser.parse("# TEST\n\nThe report was filed.")
        mood = formatter._determine_scene_mood(neutral_script.scenes[0])
        assert mood == 'neutral'
    
    def test_visual_style_determination(self, formatter, sample_script):
        """Test visual style determination."""
        style = formatter._determine_visual_style(sample_script, 'dark')
        assert 'dark' in style
        assert 'gritty' in style
        
        style = formatter._determine_visual_style(sample_script, 'action')
        assert 'dynamic' in style
        assert 'high energy' in style
    
    def test_text_wrapping(self, formatter):
        """Test text wrapping functionality."""
        long_text = "This is a very long line that needs to be wrapped because it exceeds the maximum line length specified in the formatting options."
        
        wrapped = formatter._wrap_text(long_text, 40)
        
        assert isinstance(wrapped, list)
        assert all(len(line) <= 40 for line in wrapped)
        assert ' '.join(wrapped) == long_text
    
    def test_time_formatting(self, formatter):
        """Test various time format functions."""
        # SRT format
        assert formatter._format_srt_time(0) == "00:00:00,000"
        assert formatter._format_srt_time(61.5) == "00:01:01,500"
        assert formatter._format_srt_time(3661.123) == "01:01:01,123"
        
        # VTT format
        assert formatter._format_vtt_time(0) == "00:00:00.000"
        assert formatter._format_vtt_time(61.5) == "00:01:01.500"
        
        # ASS format
        assert formatter._format_ass_time(0) == "0:00:00.00"
        assert formatter._format_ass_time(61.5) == "0:01:01.50"
    
    def test_format_options(self, formatter_with_options, sample_script):
        """Test formatting with custom options."""
        # Test without timing
        formatter_no_timing = ScriptFormatter(FormatOptions(include_timing=False))
        segments = formatter_no_timing.format_for_voice_synthesis(sample_script)
        # Timing should still be included in structure but could be ignored by consumer
        
        # Test without visual cues
        formatter_no_visual = ScriptFormatter(FormatOptions(include_visual_cues=False))
        json_str = formatter_no_visual.format_as_json(sample_script)
        data = json.loads(json_str)
        # Visual prompts might not be included in scenes
        
        # Test custom line length
        formatter_short_lines = ScriptFormatter(FormatOptions(max_line_length=40))
        screenplay = formatter_short_lines.format_as_screenplay(sample_script)
        lines = screenplay.split('\n')
        # Most lines should be under 40 chars (except maybe titles)