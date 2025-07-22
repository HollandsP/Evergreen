#!/usr/bin/env python3
"""
Example usage script for the DALL-E 3 → RunwayML prompt optimization system.

This script demonstrates how to use the prompt library and optimizer
to create consistent visual content for "The Descent" narrative style.
"""

import asyncio
import json
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.prompts import (
    PromptOptimizer, 
    OptimizationConfig,
    get_prompt_by_genre,
    get_camera_movement,
    get_style_modifier,
    get_transition_prompt,
    get_compatible_genre
)


def print_separator(title: str):
    """Print a formatted separator with title."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def demonstrate_basic_optimization():
    """Demonstrate basic prompt optimization."""
    print_separator("BASIC PROMPT OPTIMIZATION")
    
    # Create optimizer with default config
    optimizer = PromptOptimizer()
    
    # Test prompts inspired by "The Descent" narrative
    test_prompts = [
        "Underground facility with server rooms and blinking screens",
        "Corporate office building at night with empty cubicles",
        "Dystopian cityscape with abandoned buildings",
        "Control room with multiple monitors showing system alerts"
    ]
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n--- Test {i}: Original Prompt ---")
        print(f"Original: {prompt}")
        
        result = optimizer.optimize_prompt(prompt)
        
        print(f"\nDALL-E 3 Optimized:")
        print(f"  {result.optimized_image_prompt}")
        
        print(f"\nRunwayML Video:")
        print(f"  {result.optimized_video_prompt}")
        
        print(f"\nMetadata:")
        print(f"  Style: {result.style_applied}")
        print(f"  Camera: {result.camera_movement}")
        print(f"  Duration: {result.estimated_duration:.1f}s")
        print(f"  Moderation Safe: {result.moderation_safe}")
        
        if result.optimization_notes:
            print(f"  Notes: {', '.join(result.optimization_notes)}")


def demonstrate_genre_system():
    """Demonstrate the genre-based prompt system."""
    print_separator("GENRE-BASED PROMPT SYSTEM")
    
    genres = [
        "dystopian_cityscape",
        "underground_facility", 
        "corporate_interior",
        "industrial_complex"
    ]
    
    for genre in genres:
        print(f"\n--- Genre: {genre} ---")
        
        # Get prompt pair for genre
        prompt_pair = get_prompt_by_genre(genre, style="cinematic")
        
        if prompt_pair:
            print(f"Image Prompt:")
            print(f"  {prompt_pair.image_prompt}")
            
            print(f"\nVideo Prompt:")
            print(f"  {prompt_pair.video_prompt}")
            
            print(f"\nMetadata:")
            print(f"  Genre: {prompt_pair.genre}")
            print(f"  Style: {prompt_pair.style}")
            print(f"  Camera Movement: {prompt_pair.camera_movement}")
        else:
            print(f"  No prompts found for genre: {genre}")


def demonstrate_style_variations():
    """Demonstrate different style variations."""
    print_separator("STYLE VARIATIONS")
    
    base_prompt = "Corporate boardroom with glass walls overlooking the city"
    styles = ["photorealistic", "cinematic", "artistic", "noir"]
    
    optimizer = PromptOptimizer()
    
    for style in styles:
        print(f"\n--- Style: {style} ---")
        
        config = OptimizationConfig(target_style=style)
        optimizer.config = config
        
        result = optimizer.optimize_prompt(base_prompt)
        
        print(f"Optimized Image:")
        print(f"  {result.optimized_image_prompt}")
        
        print(f"Video Motion:")
        print(f"  {result.optimized_video_prompt}")


def demonstrate_camera_movements():
    """Demonstrate camera movement options."""
    print_separator("CAMERA MOVEMENT DEMONSTRATIONS")
    
    movement_categories = [
        "panning_movements",
        "tracking_movements", 
        "tilting_movements",
        "atmospheric_movements"
    ]
    
    for category in movement_categories:
        print(f"\n--- Category: {category} ---")
        
        # Get sample movements from category
        movement = get_camera_movement(category)
        print(f"  {movement}")
        
        # Show specific movements in category
        from src.prompts.dalle3_runway_prompts import CAMERA_MOVEMENTS
        if category in CAMERA_MOVEMENTS:
            specific_movements = CAMERA_MOVEMENTS[category]
            print(f"  Available movements:")
            for name, description in list(specific_movements.items())[:3]:  # Show first 3
                print(f"    {name}: {description}")


def demonstrate_narrative_sequence():
    """Demonstrate creating a narrative sequence."""
    print_separator("NARRATIVE SEQUENCE CREATION")
    
    # Create a sequence of prompts for "The Descent" story
    sequence_prompts = [
        "Modern corporate office during business hours with employees at workstations",
        "Same office at night, empty and dark with only emergency lighting",
        "Underground data center with rows of server racks and blinking status lights",
        "Control room with multiple screens showing system failures and alerts",
        "Abandoned city streets with empty buildings and scattered debris"
    ]
    
    # Configure for cinematic consistency
    config = OptimizationConfig(
        target_style="cinematic",
        camera_movement_preference="smooth",
        consistency_mode=True
    )
    
    optimizer = PromptOptimizer(config)
    
    # Optimize the sequence
    sequence_results = optimizer.create_prompt_sequence(
        sequence_prompts, 
        narrative_flow=True
    )
    
    total_duration = sum(r.estimated_duration for r in sequence_results)
    
    print(f"Narrative Sequence ({len(sequence_results)} scenes, {total_duration:.1f}s total):")
    
    for i, result in enumerate(sequence_results, 1):
        print(f"\n--- Scene {i} ({result.estimated_duration:.1f}s) ---")
        print(f"Image: {result.optimized_image_prompt[:80]}...")
        print(f"Video: {result.optimized_video_prompt[:80]}...")
        print(f"Camera: {result.camera_movement}")


def demonstrate_transition_prompts():
    """Demonstrate transition prompts for scene changes."""
    print_separator("TRANSITION PROMPTS")
    
    transition_types = [
        ("temporal", "time_passage"),
        ("spatial", "location_change"),
        ("narrative", "cause_effect"),
        ("thematic", "emotional_shift")
    ]
    
    for transition_type, subtype in transition_types:
        print(f"\n--- Transition: {transition_type} / {subtype} ---")
        
        transition = get_transition_prompt(transition_type, subtype)
        
        if transition:
            print(f"Image: {transition.image_prompt}")
            print(f"Video: {transition.video_prompt}")
            print(f"Camera: {transition.camera_movement}")
        else:
            print(f"  No transition found for {transition_type}/{subtype}")


def demonstrate_api_export():
    """Demonstrate exporting prompts for API use."""
    print_separator("API EXPORT FORMAT")
    
    # Create a sample sequence
    test_prompts = [
        "Corporate headquarters exterior at dawn",
        "Executive meeting room with concerned faces",
        "Underground server facility with emergency lighting"
    ]
    
    config = OptimizationConfig(
        target_style="cinematic",
        resolution="1792x1024",
        ensure_moderation_safe=True
    )
    
    optimizer = PromptOptimizer(config)
    results = optimizer.create_prompt_sequence(test_prompts)
    
    # Export for API use
    api_export = optimizer.export_prompts_for_api(results)
    
    print("\nAPI Export Format:")
    print(json.dumps(api_export, indent=2))
    
    # Show optimization statistics
    stats = optimizer.get_optimization_stats()
    print(f"\nOptimization Statistics:")
    print(json.dumps(stats, indent=2))


def demonstrate_moderation_safety():
    """Demonstrate moderation safety features."""
    print_separator("MODERATION SAFETY")
    
    # Test potentially problematic prompts
    test_prompts = [
        "Destroyed building with debris and damage",  # Safe version of destruction
        "Tense confrontation in corporate boardroom",  # Safe version of conflict
        "Emergency evacuation scene with warning systems",  # Safe version of danger
        "Security checkpoint with access control systems"  # Safe version of authority
    ]
    
    optimizer = PromptOptimizer(OptimizationConfig(ensure_moderation_safe=True))
    
    for prompt in test_prompts:
        print(f"\nTesting: {prompt}")
        
        result = optimizer.optimize_prompt(prompt)
        
        print(f"Moderation Safe: {result.moderation_safe}")
        print(f"Optimized: {result.optimized_image_prompt[:100]}...")
        
        if not result.moderation_safe:
            print("⚠️  Warning: Prompt may trigger content moderation")


def demonstrate_the_descent_workflow():
    """Demonstrate complete workflow for 'The Descent' narrative."""
    print_separator("THE DESCENT - COMPLETE WORKFLOW")
    
    print("Creating prompts optimized for 'The Descent' narrative style...")
    
    # Configuration optimized for the story
    config = OptimizationConfig(
        target_style="cinematic",
        camera_movement_preference="smooth",
        duration_range=(4.0, 8.0),
        resolution="1792x1024",
        consistency_mode=True,
        ensure_moderation_safe=True,
        add_technical_specs=True,
        enhance_lighting=True
    )
    
    optimizer = PromptOptimizer(config)
    
    # Story progression prompts
    story_beats = [
        "Modern tech company office with employees working at computers",
        "Same office after hours, eerily quiet with only security lighting",
        "Discovery of hidden underground access behind server room",
        "Descent into underground facility with industrial architecture",
        "Vast underground data center with artificial intelligence infrastructure",
        "Control room showing AI system status and global network maps",
        "Evidence of AI autonomous decision-making and expansion",
        "Empty city streets as AI influence spreads globally"
    ]
    
    print(f"\nOptimizing {len(story_beats)} story beats...")
    
    # Optimize the complete sequence
    sequence = optimizer.create_prompt_sequence(story_beats, narrative_flow=True)
    
    # Create transitions between scenes
    print(f"\nCreating transitions...")
    
    transitions = []
    for i in range(len(sequence) - 1):
        # Determine appropriate transition type
        if i in [0, 1]:  # Office day to night
            transition = get_transition_prompt("temporal", "day_night")
        elif i in [2, 3]:  # Location change to underground
            transition = get_transition_prompt("spatial", "location_change")
        else:  # Narrative progression
            transition = get_transition_prompt("narrative", "cause_effect")
        
        if transition:
            transitions.append(transition)
    
    # Export complete production package
    print(f"\nExporting production package...")
    
    api_export = optimizer.export_prompts_for_api(sequence)
    
    # Add transition data
    api_export["transitions"] = [
        {
            "after_scene": i,
            "image_prompt": trans.image_prompt,
            "video_prompt": trans.video_prompt,
            "camera_movement": trans.camera_movement
        }
        for i, trans in enumerate(transitions)
    ]
    
    # Summary
    total_duration = sum(r.estimated_duration for r in sequence)
    transition_duration = len(transitions) * 2.0  # Estimated transition time
    
    print(f"\n--- PRODUCTION SUMMARY ---")
    print(f"Story Scenes: {len(sequence)}")
    print(f"Transitions: {len(transitions)}")
    print(f"Total Duration: {total_duration + transition_duration:.1f}s")
    print(f"Average Scene Length: {total_duration / len(sequence):.1f}s")
    print(f"Style Consistency: {config.target_style}")
    print(f"Moderation Safe: {all(r.moderation_safe for r in sequence)}")
    
    # Save to file for production use
    output_file = Path(__file__).parent / "the_descent_prompts.json"
    
    with open(output_file, 'w') as f:
        json.dump(api_export, f, indent=2)
    
    print(f"\nProduction package saved to: {output_file}")
    
    return api_export


def main():
    """Run all demonstrations."""
    print("DALL-E 3 → RunwayML Prompt System Demonstration")
    print("Optimized for 'The Descent' narrative style")
    
    try:
        # Basic functionality
        demonstrate_basic_optimization()
        demonstrate_genre_system()
        demonstrate_style_variations()
        
        # Advanced features
        demonstrate_camera_movements()
        demonstrate_transition_prompts()
        demonstrate_narrative_sequence()
        
        # Production features
        demonstrate_moderation_safety()
        demonstrate_api_export()
        
        # Complete workflow
        the_descent_package = demonstrate_the_descent_workflow()
        
        print_separator("DEMONSTRATION COMPLETE")
        print("All prompt optimization systems demonstrated successfully!")
        print(f"Production package ready for 'The Descent' video generation.")
        
        return the_descent_package
        
    except Exception as e:
        print(f"\nError during demonstration: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Run demonstrations
    result = main()
    
    if result:
        print(f"\nDemo completed successfully!")
        print(f"Generated {len(result['dalle3_prompts'])} DALL-E 3 prompts")
        print(f"Generated {len(result['runway_prompts'])} RunwayML prompts")
    else:
        print(f"\nDemo encountered errors. Check output above.")