"""
Terminal Simulator Example

Demonstrates the capabilities of the terminal UI simulator.
"""

import time
from pathlib import Path

from .renderer import TerminalRenderer
from .themes import get_theme
from .effects import GlitchEffect, StaticEffect, ScanlineEffect
from .compositor import TerminalCompositor, BlendMode
from .fonts import TerminalFont


def demo_typing_animation():
    """Demo: Basic typing animation with Matrix theme"""
    print("Demo 1: Typing Animation (Matrix Theme)")
    
    # Create renderer with Matrix theme
    renderer = TerminalRenderer(
        width=800,
        height=600,
        theme=get_theme("matrix"),
        fps=30
    )
    
    # Add scanline effect
    renderer.add_effect(ScanlineEffect(intensity=0.3))
    
    # Create typing animation
    commands = [
        ("$ accessing mainframe...", 1.0),
        ("$ bypassing security protocols", 0.5),
        ("$ downloading data: [████████████████] 100%", 1.5),
        ("$ connection established", 1.0),
        ("$ WELCOME TO THE MATRIX", 2.0)
    ]
    
    output_path = "terminal_demo_matrix.mp4"
    renderer.render_command_sequence(commands, output_path)
    print(f"Saved to: {output_path}")


def demo_glitch_effect():
    """Demo: Glitch effects with Cyberpunk theme"""
    print("\nDemo 2: Glitch Effect (Cyberpunk Theme)")
    
    renderer = TerminalRenderer(
        width=800,
        height=600,
        theme=get_theme("cyberpunk"),
        fps=30
    )
    
    # Add glitch and static effects
    glitch = GlitchEffect(intensity=0.7)
    static = StaticEffect(intensity=0.2)
    renderer.add_effect(glitch)
    renderer.add_effect(static)
    
    # Write some text
    renderer.write("SYSTEM MALFUNCTION\n")
    renderer.write("ERROR CODE: 0xDEADBEEF\n")
    renderer.write("ATTEMPTING RECOVERY...\n")
    
    # Create animation with glitch triggers
    def update_callback(time, frame, total_frames):
        # Trigger glitch at specific times
        if frame == 30 or frame == 60 or frame == 90:
            glitch.trigger(duration=0.3)
    
    output_path = "terminal_demo_glitch.mp4"
    renderer.export_animation(output_path, duration=5.0, update_callback=update_callback)
    print(f"Saved to: {output_path}")


def demo_composite_overlay():
    """Demo: Composite terminal with alpha channel"""
    print("\nDemo 3: Composite Overlay (Green Phosphor)")
    
    renderer = TerminalRenderer(
        width=800,
        height=600,
        theme=get_theme("green_phosphor"),
        fps=30
    )
    
    compositor = TerminalCompositor()
    
    # Render terminal frame
    renderer.write("SYSTEM STATUS: ONLINE\n")
    renderer.write("CPU: ████████░░ 80%\n")
    renderer.write("MEM: ██████░░░░ 60%\n")
    renderer.write("DISK: █████████░ 90%\n")
    
    terminal_frame = renderer.render_frame()
    
    # Create composite with effects
    compositor.set_background((0, 0, 0, 255))  # Black background
    
    # Add vignette
    vignette = compositor.create_vignette((800, 600), intensity=0.7)
    
    # Add scanlines
    scanlines = compositor.create_scanline_overlay((800, 600), line_opacity=0.1)
    
    # Add glow
    glow = compositor.create_glow_overlay(terminal_frame, intensity=0.5)
    
    # Composite layers
    compositor.add_layer(glow, opacity=0.8, blend_mode=BlendMode.ADD)
    compositor.add_layer(terminal_frame, opacity=1.0, blend_mode=BlendMode.NORMAL)
    compositor.add_layer(scanlines, opacity=0.5, blend_mode=BlendMode.MULTIPLY)
    compositor.add_layer(vignette, opacity=0.8, blend_mode=BlendMode.MULTIPLY)
    
    # Export with alpha
    output_path = "terminal_composite_alpha.png"
    compositor.export_with_alpha(output_path)
    print(f"Saved to: {output_path}")


def demo_ascii_art():
    """Demo: ASCII art rendering"""
    print("\nDemo 4: ASCII Art (Amber Theme)")
    
    renderer = TerminalRenderer(
        width=800,
        height=600,
        theme=get_theme("amber"),
        fps=30
    )
    
    # Create ASCII art
    ascii_logo = """
    ╔═══════════════════════════════════╗
    ║      EVERGREEN AI SYSTEMS         ║
    ║         ▄▄▄▄▄▄▄▄▄▄▄▄▄            ║
    ║       ▄█████████████████▄         ║
    ║      ████▀▀▀▀▀▀▀▀▀▀▀████         ║
    ║      ████ NEURAL NET ████         ║
    ║      ████▄▄▄▄▄▄▄▄▄▄▄████         ║
    ║       ▀█████████████████▀         ║
    ║         ▀▀▀▀▀▀▀▀▀▀▀▀▀            ║
    ╚═══════════════════════════════════╝
    """
    
    # Type out ASCII art
    renderer.type_text(ascii_logo)
    
    output_path = "terminal_demo_ascii.mp4"
    
    def update_callback(time, frame, total_frames):
        # Add pulsing effect to completed animation
        if renderer.typing_effect.is_complete():
            intensity = 0.5 + 0.3 * abs(time % 2 - 1)
            renderer.theme.glow_intensity = intensity
    
    renderer.export_animation(output_path, duration=5.0, update_callback=update_callback)
    print(f"Saved to: {output_path}")


def demo_all_themes():
    """Demo: Show all available themes"""
    print("\nDemo 5: All Terminal Themes")
    
    from .themes import list_themes
    
    for theme_name in list_themes():
        print(f"  Rendering {theme_name} theme...")
        
        renderer = TerminalRenderer(
            width=800,
            height=300,
            theme=get_theme(theme_name),
            fps=30
        )
        
        # Add theme-appropriate effects
        if theme_name in ["matrix", "green_phosphor", "amber"]:
            renderer.add_effect(ScanlineEffect(intensity=0.2))
        
        # Write theme demo text
        renderer.write(f"THEME: {theme_name.upper()}\n")
        renderer.write(f"{'='*40}\n")
        renderer.write("The quick brown fox jumps over the lazy dog\n")
        renderer.write("0123456789 !@#$%^&*()_+-={}[]|\\:;\"'<>,.?/\n")
        renderer.write("\nColors: ")
        
        # Render single frame
        frame = renderer.render_frame()
        output_path = f"terminal_theme_{theme_name}.png"
        frame.save(output_path)
        print(f"    Saved to: {output_path}")


if __name__ == "__main__":
    print("Terminal UI Simulator Demo\n")
    
    # Run demos
    demo_typing_animation()
    demo_glitch_effect()
    demo_composite_overlay()
    demo_ascii_art()
    demo_all_themes()
    
    print("\nAll demos completed!")