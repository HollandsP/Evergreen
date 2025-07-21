# Script Engine Module

A comprehensive script parsing and processing engine for the AI Content Generation Pipeline. This module handles markdown and screenplay format scripts, extracting metadata, analyzing content, and formatting output for voice synthesis and visual generation.

## Features

### Parser (`parser.py`)
- **Markdown Script Parser**: Handles LOG-style markdown scripts with metadata
- **Screenplay Script Parser**: Processes traditional screenplay format
- **Automatic timing calculation** based on word count and content type
- **Visual cue extraction** for video generation
- **Emotional tone detection** for voice synthesis
- **Character identification** and dialogue attribution

### Analyzer (`analyzer.py`)
- **Scene-by-scene analysis** with duration, pacing, and complexity metrics
- **Character analysis** including speaking time and scene appearances
- **Theme detection** (dystopian, horror, thriller, sci-fi, etc.)
- **Mood progression tracking** throughout the script
- **Music cue suggestions** based on mood and pacing
- **Narrative arc detection** (rising, falling, steady, climactic)
- **Production complexity estimation**
- **Comprehensive recommendations** for voice, visual, and pacing

### Formatter (`formatter.py`)
- **Voice Synthesis Format**: Structured segments with timing and voice assignment
- **Visual Generation Format**: Scene prompts with style and mood information
- **Subtitle Formats**: SRT, WebVTT, and ASS subtitle generation
- **Screenplay Format**: Traditional screenplay formatting
- **Structured Formats**: JSON and XML export
- **Customizable formatting options** for different use cases

### Validator (`validator.py`)
- **Format detection** and validation
- **Content quality checks** including length, structure, and consistency
- **Timing validation** for scene and total duration
- **Character consistency** verification
- **Production feasibility** assessment
- **Sensitive content detection**
- **Comprehensive scoring system** (0-1 scale)

## Usage

### Basic Example

```python
from src.script_engine import MarkdownScriptParser, ScriptAnalyzer, ScriptFormatter, ScriptValidator

# Parse a markdown script
parser = MarkdownScriptParser()
with open('stories/LOG_0002_DESCENT.md', 'r') as f:
    content = f.read()
    
parsed_script = parser.parse(content)

# Validate the script
validator = ScriptValidator()
validation_result = validator.validate(parsed_script)
print(f"Valid: {validation_result.valid}, Score: {validation_result.score}")

# Analyze the script
analyzer = ScriptAnalyzer()
analysis = analyzer.analyze(parsed_script)
print(f"Themes: {analysis.content.themes}")
print(f"Duration: {analysis.timing.total_duration:.1f} seconds")

# Format for voice synthesis
formatter = ScriptFormatter()
voice_segments = formatter.format_for_voice_synthesis(parsed_script)
for segment in voice_segments[:3]:
    print(f"{segment['type']}: {segment['text'][:50]}...")
```

### Processing a Complete Script

```python
from src.script_engine.example_usage import process_markdown_script, export_script_data

# Process a script file
parsed_script, analysis = process_markdown_script('path/to/script.md')

# Export in various formats
export_script_data(parsed_script, './output')
```

## Script Format Examples

### Markdown Format (LOG Style)

```markdown
# LOG_0001: THE BEGINNING

**Location**: City Name, District
**Date**: Day X
**Reporter**: Character Name, Title

---

Narrative text describing the scene. Visual descriptions for video generation.

"Dialogue text here." - Speaker Name

More narrative content.

[SCENE TRANSITION OR EFFECT]

---

**METADATA**:
- Duration: M:SS
- Corruption: X%
- Recovery Status: PARTIAL/COMPLETE
```

### Screenplay Format

```
TITLE

FADE IN:

INT. LOCATION - TIME

Scene description and action.

CHARACTER NAME
(emotion/direction)
Dialogue text here.

More action description.

CUT TO:

EXT. ANOTHER LOCATION - LATER

FADE OUT.
```

## Data Classes

### ParsedScript
- `metadata`: Script metadata (title, location, date, etc.)
- `scenes`: List of Scene objects
- `characters`: List of character names
- `total_duration`: Total estimated duration in seconds
- `word_count`: Total word count
- `visual_cues`: Extracted visual descriptions
- `narrative_segments`: All narrative elements
- `dialogue_segments`: All dialogue elements

### ScriptAnalysis
- `timing`: Timing analysis with scene durations
- `characters`: Character analysis with speaking time
- `scenes`: Individual scene analyses
- `content`: Content analysis with themes and mood
- `recommendations`: Production recommendations
- `metrics`: Various script metrics

### ValidationResult
- `valid`: Overall validity boolean
- `issues`: List of validation issues
- `statistics`: Script statistics
- `score`: Quality score (0-1)

## Error Handling

The script engine includes comprehensive error handling:
- Empty or invalid content gracefully returns empty structures
- Malformed scripts still extract available information
- Validation provides detailed feedback on issues
- All components are designed to fail gracefully

## Testing

Comprehensive unit and integration tests are provided:
- `tests/script_engine/test_parser.py`: Parser functionality
- `tests/script_engine/test_analyzer.py`: Analysis algorithms
- `tests/script_engine/test_formatter.py`: Output formatting
- `tests/script_engine/test_validator.py`: Validation logic
- `tests/script_engine/test_integration.py`: End-to-end pipeline

Run tests with:
```bash
pytest tests/script_engine/
```

## Performance Considerations

- **Timing Calculations**: Based on average reading speeds (150 WPM narration, 180 WPM dialogue)
- **Visual Cue Extraction**: Uses regex patterns optimized for common descriptions
- **Memory Efficient**: Processes scripts in a single pass where possible
- **Scalable**: Handles scripts from a few lines to thousands of lines

## Future Enhancements

- Support for additional script formats (fountain, celtx)
- Machine learning-based emotion detection
- Advanced visual prompt generation with scene continuity
- Real-time collaboration features
- Integration with voice cloning services
- Custom timing profiles for different content types