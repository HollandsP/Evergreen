"""Unit tests for script validator module."""

import pytest
from src.script_engine.parser import MarkdownScriptParser
from src.script_engine.validator import (
    ScriptValidator, ValidationResult, ValidationIssue
)


class TestScriptValidator:
    """Test cases for ScriptValidator."""
    
    @pytest.fixture
    def validator(self):
        """Create a validator instance."""
        return ScriptValidator()
    
    @pytest.fixture
    def valid_markdown(self):
        """Valid markdown script content."""
        return """# LOG_0001: THE BEGINNING

**Location**: New York, Downtown
**Date**: Day 1
**Reporter**: Jane Doe

---

The city was quiet, too quiet. Something was about to happen.

"Is anyone there?" - Voice echoed.

The silence was deafening. We knew we had to act fast.

---

More content here to meet minimum requirements.
This is additional narrative text.
We need to ensure the script is long enough."""
    
    @pytest.fixture
    def valid_screenplay(self):
        """Valid screenplay format content."""
        return """FADE IN:

INT. OFFICE BUILDING - DAY

The office is bustling with activity. People move between cubicles.

JANE
(worried)
Have you seen the latest reports?

JOHN
Not yet. What's wrong?

JANE
The numbers don't add up.

They huddle over a computer screen.

CUT TO:

INT. CONFERENCE ROOM - LATER

The team gathers for an emergency meeting.

FADE OUT."""
    
    def test_validate_valid_markdown(self, validator, valid_markdown):
        """Test validation of valid markdown content."""
        result = validator.validate(valid_markdown)
        
        assert isinstance(result, ValidationResult)
        assert result.valid is True
        assert len(result.errors) == 0
        assert result.score > 0.8
    
    def test_validate_valid_screenplay(self, validator, valid_screenplay):
        """Test validation of valid screenplay content."""
        result = validator.validate(valid_screenplay)
        
        assert isinstance(result, ValidationResult)
        assert result.valid is True
        assert len(result.errors) == 0
    
    def test_validate_empty_content(self, validator):
        """Test validation of empty content."""
        result = validator.validate("")
        
        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].message == "Script content is empty"
        assert result.score == 0.0
    
    def test_validate_short_content(self, validator):
        """Test validation of very short content."""
        short_content = "# Title\n\nVery short."
        result = validator.validate(short_content)
        
        assert len(result.warnings) > 0
        warning_messages = [w.message for w in result.warnings]
        assert any("very short" in msg.lower() for msg in warning_messages)
    
    def test_validate_long_lines(self, validator):
        """Test validation of content with long lines."""
        long_line = "x" * 250  # Very long line
        content = f"# Title\n\n{long_line}\n\nMore content here."
        
        result = validator.validate(content)
        
        warnings = [i for i in result.issues if i.severity == 'warning']
        assert any("exceeding" in w.message and "characters" in w.message for w in warnings)
    
    def test_validate_no_title(self, validator):
        """Test validation of content without title."""
        no_title = """Some content here without a proper title.
        
More text follows.

Even more content."""
        
        result = validator.validate(no_title)
        
        warnings = result.warnings
        assert any("title" in w.message.lower() for w in warnings)
    
    def test_validate_sensitive_content(self, validator):
        """Test detection of sensitive content."""
        sensitive = """# Dark Story

The scene depicts graphic violence and death. Multiple suicides are shown.

More disturbing content follows.

This is very explicit material."""
        
        result = validator.validate(sensitive)
        
        info_issues = result.info
        assert any("sensitive content" in i.message for i in info_issues)
    
    def test_validate_inconsistent_terminology(self, validator):
        """Test detection of inconsistent terminology."""
        inconsistent = """# Tech Report

The artificial intelligence was advanced. The A.I. learned quickly.

We sent an e-mail about the dataset. The data set was corrupted.

Check the web site for updates. Our website has more info."""
        
        result = validator.validate(inconsistent)
        
        info_issues = result.info
        assert any("inconsistent terminology" in i.message.lower() for i in info_issues)
    
    def test_validate_parsed_script(self, validator, valid_markdown):
        """Test validation of parsed script object."""
        parser = MarkdownScriptParser()
        script = parser.parse(valid_markdown)
        
        result = validator.validate(script)
        
        assert isinstance(result, ValidationResult)
        assert result.valid is True
        assert 'total_scenes' in result.statistics
        assert 'average_scene_duration' in result.statistics
    
    def test_validate_timing_issues(self, validator):
        """Test detection of timing issues."""
        parser = MarkdownScriptParser()
        
        # Very short scenes
        short_scenes = """# Test

---

Quick.

---

Short.

---"""
        
        script = parser.parse(short_scenes)
        result = validator.validate(script)
        
        timing_warnings = [i for i in result.issues if i.category == 'timing']
        assert len(timing_warnings) > 0
    
    def test_validate_character_consistency(self, validator):
        """Test character name consistency validation."""
        parser = MarkdownScriptParser()
        
        inconsistent_chars = """# Test

"Hello" - John

"Hi there" - JOHN

"Goodbye" - John Smith"""
        
        script = parser.parse(inconsistent_chars)
        result = validator.validate(script)
        
        # Should detect possible character variations
        warnings = result.warnings
        assert any("character name variations" in w.message for w in warnings)
    
    def test_validate_scene_composition(self, validator):
        """Test scene composition validation."""
        parser = MarkdownScriptParser()
        
        # Dialogue-heavy scene
        dialogue_heavy = """# Test

---

"Line 1" - A
"Line 2" - B
"Line 3" - A
"Line 4" - B
"Line 5" - A
"Line 6" - B

---"""
        
        script = parser.parse(dialogue_heavy)
        result = validator.validate(script)
        
        info_issues = result.info
        assert any("dialogue-heavy" in i.message for i in info_issues)
    
    def test_validate_production_feasibility(self, validator):
        """Test production feasibility checks."""
        parser = MarkdownScriptParser()
        
        # Complex production
        complex_script = """# Complex Production

---

" + "\n".join([f'"Line {i}" - Character{i}' for i in range(15)]) + """

Many visual effects needed. Explosions everywhere.
Flying cars zoom past. Aliens attack the city.
Robots march through streets. Buildings collapse.

---"""
        
        script = parser.parse(complex_script)
        # Add many visual cues
        script.visual_cues = [f"visual_{i}" for i in range(60)]
        
        result = validator.validate(script)
        
        # Should warn about complexity
        assert any("Large cast" in i.message for i in result.issues)
        assert any("visual complexity" in i.message for i in result.issues)
    
    def test_validation_score_calculation(self, validator):
        """Test validation score calculation."""
        # Perfect script
        perfect = """# Great Script

**Location**: Studio
**Date**: Today

---

This is a well-formatted script with good content.

"Perfect dialogue here." - Speaker

More excellent narrative content follows.

---

Another scene with great pacing.

---"""
        
        result = validator.validate(perfect)
        assert result.score > 0.9
        
        # Script with issues
        problematic = """No title

Short."""
        
        result = validator.validate(problematic)
        assert result.score < 0.8
    
    def test_validation_statistics(self, validator):
        """Test statistics calculation."""
        parser = MarkdownScriptParser()
        script = parser.parse("""# Test

---

Narrative text here.

"Dialogue" - Speaker

More narrative.

---"""
        )
        
        result = validator.validate(script)
        stats = result.statistics
        
        assert stats['total_scenes'] == 1
        assert stats['dialogue_segments'] == 1
        assert stats['narrative_segments'] == 2
        assert 0 <= stats['dialogue_ratio'] <= 1
        assert 0 <= stats['narrative_ratio'] <= 1
        assert stats['dialogue_ratio'] + stats['narrative_ratio'] == 1.0
    
    def test_format_detection(self, validator):
        """Test format detection between markdown and screenplay."""
        # Ambiguous format
        ambiguous = """Some Title

Regular text here.

More content."""
        
        result = validator.validate(ambiguous)
        
        format_warnings = [i for i in result.issues if "format" in i.message.lower()]
        assert len(format_warnings) > 0
    
    def test_issue_categorization(self, validator):
        """Test proper categorization of issues."""
        result = ValidationResult(valid=True)
        
        # Add different types of issues
        result.issues.append(ValidationIssue(
            severity='error',
            category='structure',
            message='Test error'
        ))
        
        result.issues.append(ValidationIssue(
            severity='warning',
            category='timing',
            message='Test warning'
        ))
        
        result.issues.append(ValidationIssue(
            severity='info',
            category='content',
            message='Test info'
        ))
        
        assert len(result.errors) == 1
        assert len(result.warnings) == 1
        assert len(result.info) == 1
        
        assert result.errors[0].message == 'Test error'
        assert result.warnings[0].message == 'Test warning'
        assert result.info[0].message == 'Test info'