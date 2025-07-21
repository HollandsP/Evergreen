# Terminal UI Simulator

A comprehensive terminal simulation system for creating realistic terminal animations with various retro effects and themes.

## Features

### Effects
- **Typing Animation**: Realistic typing with variable speed and punctuation pauses
- **Glitch Effects**: Random character corruption and visual distortions
- **Static/Noise**: CRT-style static and interference
- **Cursor Animation**: Blinking cursor with multiple styles (block, underline, pipe)
- **Scanlines**: CRT monitor scanline effects with movement
- **Phosphor Glow**: Authentic phosphor monitor glow
- **Chromatic Aberration**: Color fringing for retro CRT look
- **CRT Curvature**: Screen curvature distortion

### Themes
- **Matrix**: Classic green-on-black Matrix theme
- **Amber**: Vintage amber phosphor monitor
- **Green Phosphor**: Classic green terminal
- **Retro Blue**: IBM-style blue terminal
- **Cyberpunk**: Neon pink/cyan aesthetic
- **Classic**: Traditional black and white
- **Hacker**: High contrast green theme

### Capabilities
- Export videos with alpha channel for compositing
- ASCII art rendering and generation
- Terminal command visualization
- Multi-layer compositing with blend modes
- Box drawing and table generation
- Progress bar animations

## Installation

```bash
pip install pillow numpy opencv-python
```

## Quick Start

```python
from terminal_sim import TerminalRenderer, get_theme

# Create a terminal renderer
renderer = TerminalRenderer(
    width=800,
    height=600,
    theme=get_theme("matrix"),
    fps=30
)

# Type some text
renderer.type_text("Welcome to the Matrix...")

# Export to video
renderer.export_animation("output.mp4", duration=5.0)
```

## Usage Examples

### Basic Typing Animation

```python
from terminal_sim import TerminalRenderer, get_theme

renderer = TerminalRenderer(theme=get_theme("matrix"))

# Create command sequence
commands = [
    ("$ ls -la", 1.0),
    ("$ cd projects/", 0.5),
    ("$ python main.py", 2.0)
]

renderer.render_command_sequence(commands, "terminal_commands.mp4")
```

### Adding Effects

```python
from terminal_sim import TerminalRenderer, GlitchEffect, ScanlineEffect

renderer = TerminalRenderer()

# Add multiple effects
renderer.add_effect(GlitchEffect(intensity=0.5))
renderer.add_effect(ScanlineEffect(intensity=0.3))

# Trigger glitch during animation
def update(time, frame, total):
    if frame == 60:  # Trigger at 2 seconds (30 fps)
        renderer.effects.effects[0].trigger(duration=0.5)

renderer.export_animation("glitchy_terminal.mp4", duration=5.0, 
                         update_callback=update)
```

### Composite with Alpha Channel

```python
from terminal_sim import TerminalRenderer, TerminalCompositor, BlendMode

renderer = TerminalRenderer(theme=get_theme("cyberpunk"))
compositor = TerminalCompositor()

# Render terminal content
renderer.write("SYSTEM STATUS: CRITICAL")
frame = renderer.render_frame()

# Create composite
compositor.set_background((0, 0, 0, 255))
compositor.add_layer(frame, opacity=1.0)

# Add effects
vignette = compositor.create_vignette((800, 600), intensity=0.5)
compositor.add_layer(vignette, blend_mode=BlendMode.MULTIPLY)

# Export with alpha
compositor.export_with_alpha("terminal_overlay.png")
```

### ASCII Art Generation

```python
from terminal_sim import TerminalFont
from PIL import Image

font = TerminalFont()

# Convert image to ASCII
image = Image.open("logo.png")
ascii_art = font.create_ascii_art(image, width=80, charset="blocks")

print(ascii_art)
```

### Custom Theme

```python
from terminal_sim import create_custom_theme, TerminalRenderer

# Create custom theme based on color
custom_theme = create_custom_theme(
    name="Custom Purple",
    base_color=(128, 0, 255),
    style="retro"
)

renderer = TerminalRenderer(theme=custom_theme)
```

## API Reference

### TerminalRenderer

Main rendering engine for terminal animations.

#### Methods
- `write(text)`: Write text immediately
- `type_text(text)`: Set text for typing animation
- `render_frame(delta_time)`: Render single frame
- `start_recording(path, with_alpha)`: Start video recording
- `export_animation(path, duration, callback, with_alpha)`: Export animation
- `render_command_sequence(commands, path, with_alpha)`: Render command sequence

### Effects

#### TypingEffect
- `base_speed`: Base typing speed (seconds per character)
- `variation`: Random speed variation (0-1)

#### GlitchEffect
- `intensity`: Glitch intensity (0-1)
- `trigger(duration)`: Trigger glitch effect

#### StaticEffect
- `intensity`: Static noise intensity (0-1)

#### CursorEffect
- `blink_rate`: Cursor blink rate (seconds)
- `style`: Cursor style ("block", "underline", "pipe")

#### ScanlineEffect
- `intensity`: Scanline darkness (0-1)
- `speed`: Scanline movement speed

### TerminalTheme

Terminal color theme configuration.

#### Properties
- `background`, `foreground`, `cursor`: Main colors
- `black`, `red`, `green`, etc.: ANSI colors
- `glow_intensity`: Phosphor glow (0-1)
- `scan_line_intensity`: CRT scanlines (0-1)
- `noise_amount`: Static noise (0-1)
- `curvature`: CRT curvature (0-1)
- `chromatic_aberration`: Color fringing (0-1)

### TerminalCompositor

Layer compositing with blend modes.

#### Methods
- `set_background(background)`: Set base layer
- `add_layer(image, opacity, blend_mode)`: Add layer
- `composite()`: Composite all layers
- `create_vignette(size, intensity, color)`: Create vignette
- `create_scanline_overlay(size, spacing, opacity)`: Create scanlines
- `create_glow_overlay(terminal_image, color, intensity)`: Create glow

#### Blend Modes
- `NORMAL`, `MULTIPLY`, `SCREEN`, `OVERLAY`
- `ADD`, `SUBTRACT`, `DIFFERENCE`
- `SOFT_LIGHT`, `HARD_LIGHT`
- `COLOR_DODGE`, `COLOR_BURN`

### TerminalFont

Font rendering and ASCII art generation.

#### Methods
- `render_text(text, color, bg_color)`: Render text
- `create_ascii_art(image, width, charset)`: Convert to ASCII
- `render_box(width, height, style)`: Draw box
- `render_progress_bar(progress, width, style)`: Progress bar
- `create_table(headers, rows, style)`: Format table

## Tips

1. **Performance**: Cache rendered frames when possible
2. **Quality**: Use higher FPS (60) for smooth animations
3. **File Size**: Use H.264 codec for smaller files
4. **Alpha Channel**: Use PNG sequences or FFV1 codec
5. **Effects**: Layer effects for complex visuals

## License

Part of the Evergreen AI Content Generation Pipeline.