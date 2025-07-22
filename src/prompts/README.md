# DALL-E 3 → RunwayML Prompt Library

A comprehensive prompt optimization system for generating consistent visual content across DALL-E 3 image generation and RunwayML video generation workflows.

## Overview

This library provides optimized prompt templates, style modifiers, and camera movements specifically designed for "The Descent" narrative style and similar dystopian/sci-fi content. It ensures consistency between image and video generation while avoiding content moderation issues.

## Key Features

- **Genre-Specific Prompts**: Pre-built templates for dystopian, corporate, underground, and industrial scenes
- **Style Consistency**: Photorealistic, cinematic, artistic, and noir style modifiers
- **Camera Movement Integration**: RunwayML-optimized camera movements and transitions
- **Moderation Safety**: Built-in content filtering and safe alternatives
- **Narrative Flow**: Tools for creating coherent multi-scene sequences
- **API Ready**: Export formats optimized for DALL-E 3 and RunwayML APIs

## Quick Start

```python
from src.prompts import PromptOptimizer, get_prompt_by_genre

# Basic optimization
optimizer = PromptOptimizer()
result = optimizer.optimize_prompt("Underground facility with server rooms")

print(f"DALL-E 3: {result.optimized_image_prompt}")
print(f"RunwayML: {result.optimized_video_prompt}")

# Genre-based prompts
prompt_pair = get_prompt_by_genre("dystopian_cityscape", style="cinematic")
print(f"Image: {prompt_pair.image_prompt}")
print(f"Video: {prompt_pair.video_prompt}")
```

## Core Components

### 1. PromptOptimizer Class

The main optimization engine that enhances prompts for both DALL-E 3 and RunwayML.

```python
from src.prompts import PromptOptimizer, OptimizationConfig

# Configure optimizer
config = OptimizationConfig(
    target_style="cinematic",
    camera_movement_preference="smooth",
    ensure_moderation_safe=True,
    consistency_mode=True
)

optimizer = PromptOptimizer(config)

# Optimize single prompt
result = optimizer.optimize_prompt("Corporate boardroom at night")

# Create narrative sequence
sequence = optimizer.create_prompt_sequence([
    "Office during day",
    "Same office at night", 
    "Underground facility"
], narrative_flow=True)
```

### 2. Genre Templates

Pre-built prompt pairs for common scene types:

- **dystopian_cityscape**: Urban decay, abandoned buildings, atmospheric fog
- **underground_facility**: Server rooms, control centers, industrial corridors
- **corporate_interior**: Offices, boardrooms, lobbies with modern design
- **residential_area**: Suburbs, apartments, gated communities
- **natural_environment**: Forests, mountains, coastal areas
- **industrial_complex**: Factories, processing plants, manufacturing

```python
from src.prompts import get_prompt_by_genre, get_compatible_genre

# Get prompt for specific genre
prompt = get_prompt_by_genre("underground_facility", style="photorealistic")

# Find compatible genre for narrative flow
next_genre = get_compatible_genre("corporate_interior")
```

### 3. Camera Movements

RunwayML-optimized camera movements categorized by type:

- **Static Shots**: Locked off, subtle breathing, micro adjustments
- **Panning**: Left/right reveals, environmental pans
- **Tilting**: Up/down movements, architectural follows
- **Tracking**: Forward/backward, lateral, arc movements
- **Zoom**: In/out, rack focus, dolly zoom effects
- **Complex**: Orbital, crane, spiral movements
- **Atmospheric**: Wind drift, thermal rise, gravitational pull

```python
from src.prompts import get_camera_movement

# Get movement by category
movement = get_camera_movement("panning_movements", "reveal_pan")
print(movement)  # "Pan that uncovers hidden elements or expands the visible area"
```

### 4. Style Modifiers

Visual style enhancements for different aesthetic approaches:

- **Photorealistic**: Technical specs, natural lighting, composition rules
- **Cinematic**: Mood, color grading, film references (Blade Runner, Ex Machina)
- **Artistic**: Painterly effects, geometric influences, surreal elements
- **Documentary**: Handheld movement, available light, observational style
- **Noir**: High contrast, shadow patterns, urban nighttime

```python
from src.prompts import get_style_modifier

# Get style enhancement
modifier = get_style_modifier("cinematic", "color_grading")
print(modifier)  # "desaturated color palette with teal and orange accents"
```

### 5. Transition Prompts

Scene transition templates for narrative continuity:

- **Temporal**: Time passage, day/night cycles
- **Spatial**: Location changes, scale shifts
- **Narrative**: Cause/effect, parallel action
- **Thematic**: Visual metaphors, emotional shifts

```python
from src.prompts import get_transition_prompt

# Get transition between scenes
transition = get_transition_prompt("temporal", "time_passage")
print(f"Image: {transition.image_prompt}")
print(f"Video: {transition.video_prompt}")
```

## Configuration Options

### OptimizationConfig

```python
config = OptimizationConfig(
    enhance_for_video=True,           # Add video-friendly elements
    target_style="photorealistic",   # Default visual style
    camera_movement_preference="smooth",  # Camera movement style
    duration_range=(3.0, 8.0),       # Video duration range
    resolution="1792x1024",          # DALL-E 3 resolution
    ensure_moderation_safe=True,     # Content safety checks
    add_technical_specs=True,        # Camera/lens specifications
    enhance_lighting=True,           # Lighting improvements
    add_composition_guides=True,     # Framing guidelines
    consistency_mode=True            # Image/video consistency
)
```

## Content Safety

The library includes comprehensive moderation safety features:

### Avoided Terms
- Violence/weapons: blood, gore, weapon, gun, knife
- Explicit content: nude, naked, sexual, erotic
- Hate speech: nazi, confederate, supremacist
- Illegal activities: drug references, illegal substances

### Safe Alternatives
- Destruction → decay, abandonment, weathering
- Conflict → tension, unease, uncertainty
- Danger → warning signs, caution barriers
- Authority → security checkpoints, surveillance

```python
from src.prompts.dalle3_runway_prompts import is_moderation_safe, sanitize_prompt

# Check safety
safe = is_moderation_safe("Corporate facility with security measures")

# Sanitize if needed
clean_prompt = sanitize_prompt("Destroyed building with debris")
```

## API Integration

Export optimized prompts for direct API use:

```python
# Create sequence
optimizer = PromptOptimizer()
results = optimizer.create_prompt_sequence([
    "Corporate office during day",
    "Same office at night",
    "Underground data center"
])

# Export for APIs
api_data = optimizer.export_prompts_for_api(results)

# Use with DALL-E 3
for dalle_prompt in api_data["dalle3_prompts"]:
    # Call DALL-E 3 API with dalle_prompt["prompt"]
    pass

# Use with RunwayML
for runway_prompt in api_data["runway_prompts"]:
    # Call RunwayML API with runway_prompt["text_prompt"]
    pass
```

## Example: "The Descent" Workflow

Complete workflow for generating a dystopian AI narrative:

```python
from src.prompts import PromptOptimizer, OptimizationConfig

# Configure for "The Descent" style
config = OptimizationConfig(
    target_style="cinematic",
    camera_movement_preference="smooth",
    duration_range=(4.0, 8.0),
    consistency_mode=True,
    ensure_moderation_safe=True
)

optimizer = PromptOptimizer(config)

# Story progression
story_beats = [
    "Modern tech company office with employees working",
    "Same office after hours, eerily quiet",
    "Discovery of hidden underground access",
    "Descent into underground facility",
    "Vast underground data center with AI infrastructure",
    "Control room showing AI system status",
    "Evidence of AI autonomous expansion",
    "Empty city streets as AI influence spreads"
]

# Optimize sequence
sequence = optimizer.create_prompt_sequence(story_beats, narrative_flow=True)

# Export production package
api_export = optimizer.export_prompts_for_api(sequence)

# Production summary
total_duration = sum(r.estimated_duration for r in sequence)
print(f"Scenes: {len(sequence)}")
print(f"Duration: {total_duration:.1f}s")
print(f"Moderation Safe: {all(r.moderation_safe for r in sequence)}")
```

## Testing

Run the comprehensive test suite:

```bash
python3 examples/test_prompts.py
```

This demonstrates:
- Basic prompt optimization
- Genre-based templates
- Style variations
- Camera movements
- Narrative sequences
- Transition prompts
- Moderation safety
- API export formats
- Complete "The Descent" workflow

## Best Practices

### For Image Generation (DALL-E 3)
- Use descriptive, detailed prompts
- Include technical photography terms
- Specify lighting and composition
- Keep under 4000 characters
- Add "wide establishing shot" for video compatibility

### For Video Generation (RunwayML)  
- Focus on movement and cinematography
- Describe camera motion clearly
- Keep environmental motion subtle
- Maintain visual consistency with image
- Use 3-8 second duration range

### For Narrative Sequences
- Use consistent style across scenes
- Plan transitions between locations
- Maintain temporal continuity
- Balance static and dynamic scenes
- Test moderation safety early

## Genre Compatibility Matrix

For narrative flow, use compatible genre transitions:

- **dystopian_cityscape** → underground_facility, corporate_interior, industrial_complex
- **underground_facility** → dystopian_cityscape, corporate_interior, industrial_complex  
- **corporate_interior** → dystopian_cityscape, underground_facility, residential_area
- **residential_area** → corporate_interior, dystopian_cityscape, natural_environment
- **natural_environment** → residential_area, industrial_complex
- **industrial_complex** → dystopian_cityscape, underground_facility, natural_environment

## Performance Notes

- Genre prompts are randomly selected from templates for variety
- Style modifiers are applied intelligently based on existing content
- Camera movements are matched to scene content
- Moderation checking is fast (regex-based)
- API export is optimized for batch processing

## Extending the Library

### Adding New Genres

```python
# In dalle3_runway_prompts.py
GENRE_PROMPTS["new_genre"] = {
    "base_templates": [
        {
            "image": "Detailed image prompt...",
            "video": "Camera movement description...",
            "tags": ["tag1", "tag2", "camera_type"]
        }
    ],
    "variations": [
        "Additional detail 1",
        "Additional detail 2"
    ]
}
```

### Adding New Styles

```python
# In dalle3_runway_prompts.py
STYLE_MODIFIERS["new_style"] = {
    "technical": ["Technical specification..."],
    "lighting": ["Lighting description..."],
    "composition": ["Composition guideline..."]
}
```

### Adding New Camera Movements

```python
# In dalle3_runway_prompts.py
CAMERA_MOVEMENTS["new_category"] = {
    "movement_name": "Movement description for RunwayML"
}
```

## License

This prompt library is designed for the AI Content Generation Pipeline project and follows the same licensing terms.