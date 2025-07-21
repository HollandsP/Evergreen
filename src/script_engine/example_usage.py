"""
Example usage of the script engine for the AI Content Generation Pipeline.
"""

from pathlib import Path
from .parser import MarkdownScriptParser, ScreenplayScriptParser
from .analyzer import ScriptAnalyzer
from .formatter import ScriptFormatter, FormatOptions
from .validator import ScriptValidator


def process_markdown_script(script_path: str):
    """
    Process a markdown format script through the complete pipeline.
    
    Args:
        script_path: Path to the markdown script file
    """
    print(f"Processing markdown script: {script_path}")
    print("=" * 60)
    
    # Read the script
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Parse the script
    parser = MarkdownScriptParser()
    parsed_script = parser.parse(content)
    
    print(f"Title: {parsed_script.metadata.title}")
    print(f"Location: {parsed_script.metadata.location}")
    print(f"Reporter: {parsed_script.metadata.reporter}")
    print(f"Scenes: {len(parsed_script.scenes)}")
    print(f"Characters: {', '.join(parsed_script.characters)}")
    print(f"Total Duration: {parsed_script.total_duration:.1f} seconds")
    print()
    
    # 2. Validate the script
    validator = ScriptValidator()
    validation_result = validator.validate(parsed_script)
    
    print("Validation Results:")
    print(f"  Valid: {validation_result.valid}")
    print(f"  Score: {validation_result.score:.2f}")
    print(f"  Errors: {len(validation_result.errors)}")
    print(f"  Warnings: {len(validation_result.warnings)}")
    
    if validation_result.errors:
        print("  Errors:")
        for error in validation_result.errors:
            print(f"    - {error.message}")
    
    if validation_result.warnings:
        print("  Warnings:")
        for warning in validation_result.warnings[:3]:  # Show first 3
            print(f"    - {warning.message}")
    print()
    
    # 3. Analyze the script
    analyzer = ScriptAnalyzer()
    analysis = analyzer.analyze(parsed_script)
    
    print("Analysis Results:")
    print(f"  Themes: {', '.join(analysis.content.themes)}")
    print(f"  Narrative Arc: {analysis.content.narrative_arc}")
    print(f"  Production Complexity: {analysis.metrics['estimated_production_complexity']}")
    print(f"  Average Scene Duration: {analysis.timing.average_scene_duration:.1f}s")
    print()
    
    # 4. Format for voice synthesis
    formatter = ScriptFormatter()
    voice_segments = formatter.format_for_voice_synthesis(parsed_script)
    
    print(f"Voice Synthesis Segments: {len(voice_segments)}")
    print("Sample segments:")
    for segment in voice_segments[:3]:
        print(f"  - {segment['type']}: {segment['text'][:50]}...")
        print(f"    Voice: {segment['voice']}, Duration: {segment['timing']['estimated_duration']:.1f}s")
    print()
    
    # 5. Format for visual generation
    visual_prompts = formatter.format_for_visual_generation(parsed_script)
    
    print(f"Visual Generation Prompts: {len(visual_prompts)}")
    for prompt in visual_prompts[:2]:
        print(f"  - Type: {prompt['type']}")
        print(f"    Prompt: {prompt['prompt'][:60]}...")
        print(f"    Style: {prompt['style'][:40]}...")
    print()
    
    # 6. Export formats
    print("Available Export Formats:")
    print("  - JSON: for API integration")
    print("  - XML: for structured data exchange")
    print("  - SRT/VTT/ASS: for subtitles")
    print("  - Screenplay: for traditional script format")
    
    return parsed_script, analysis


def process_screenplay_script(script_path: str):
    """
    Process a screenplay format script.
    
    Args:
        script_path: Path to the screenplay script file
    """
    print(f"Processing screenplay script: {script_path}")
    print("=" * 60)
    
    # Read the script
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse with screenplay parser
    parser = ScreenplayScriptParser()
    parsed_script = parser.parse(content)
    
    # Rest of pipeline is the same...
    validator = ScriptValidator()
    validation_result = validator.validate(content)
    
    analyzer = ScriptAnalyzer()
    analysis = analyzer.analyze(parsed_script)
    
    formatter = ScriptFormatter()
    voice_segments = formatter.format_for_voice_synthesis(parsed_script)
    
    print(f"Scenes: {len(parsed_script.scenes)}")
    print(f"Characters: {', '.join(parsed_script.characters)}")
    print(f"Total Duration: {parsed_script.total_duration:.1f} seconds")
    print(f"Validation Score: {validation_result.score:.2f}")
    
    return parsed_script, analysis


def export_script_data(parsed_script, output_dir: str = "./output"):
    """
    Export script data in various formats.
    
    Args:
        parsed_script: Parsed script object
        output_dir: Directory to save output files
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    formatter = ScriptFormatter()
    
    # Export as JSON
    json_output = formatter.format_as_json(parsed_script)
    json_path = output_path / "script_data.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        f.write(json_output)
    print(f"Exported JSON to: {json_path}")
    
    # Export as subtitles
    srt_output = formatter.format_as_subtitles(parsed_script, 'srt')
    srt_path = output_path / "script_subtitles.srt"
    with open(srt_path, 'w', encoding='utf-8') as f:
        f.write(srt_output)
    print(f"Exported SRT to: {srt_path}")
    
    # Export as screenplay
    screenplay_output = formatter.format_as_screenplay(parsed_script)
    screenplay_path = output_path / "script_screenplay.txt"
    with open(screenplay_path, 'w', encoding='utf-8') as f:
        f.write(screenplay_output)
    print(f"Exported screenplay to: {screenplay_path}")
    
    # Export voice synthesis data
    voice_segments = formatter.format_for_voice_synthesis(parsed_script)
    voice_path = output_path / "voice_segments.json"
    import json
    with open(voice_path, 'w', encoding='utf-8') as f:
        json.dump(voice_segments, f, indent=2)
    print(f"Exported voice segments to: {voice_path}")
    
    # Export visual prompts
    visual_prompts = formatter.format_for_visual_generation(parsed_script)
    visual_path = output_path / "visual_prompts.json"
    with open(visual_path, 'w', encoding='utf-8') as f:
        json.dump(visual_prompts, f, indent=2)
    print(f"Exported visual prompts to: {visual_path}")


def main():
    """Main example function."""
    # Example: Process LOG_0002_DESCENT.md
    log_script_path = Path(__file__).parent.parent.parent / "stories" / "LOG_0002_DESCENT.md"
    
    if log_script_path.exists():
        print("Processing LOG_0002_DESCENT.md")
        print("=" * 80)
        parsed_script, analysis = process_markdown_script(str(log_script_path))
        
        # Export the processed data
        export_script_data(parsed_script, "./output/LOG_0002")
        
        print("\n" + "=" * 80)
        print("Processing complete!")
        
        # Show production recommendations
        print("\nProduction Recommendations:")
        for category, recommendations in analysis.recommendations.items():
            if recommendations:
                print(f"\n{category.replace('_', ' ').title()}:")
                for rec in recommendations:
                    print(f"  - {rec}")
    else:
        print(f"Script file not found: {log_script_path}")
        print("Creating example script for demonstration...")
        
        # Create example script
        example_script = """# EXAMPLE: TEST TRANSMISSION

**Location**: Research Lab
**Date**: Day 1
**Reporter**: Dr. Smith

---

The experiment begins. All systems are operational.

"Initialize the sequence," - Dr. Smith commanded.

"Sequence initiated," - Assistant confirmed.

The machines hum to life. Data streams across the monitors.

[SYSTEM ALERT]

Something unexpected happens.

---

**METADATA**:
- Duration: 0:45
- Status: COMPLETE"""
        
        # Process example
        parser = MarkdownScriptParser()
        parsed = parser.parse(example_script)
        
        validator = ScriptValidator()
        validation = validator.validate(parsed)
        
        print(f"Example script parsed successfully!")
        print(f"Duration: {parsed.total_duration:.1f} seconds")
        print(f"Validation score: {validation.score:.2f}")


if __name__ == "__main__":
    main()