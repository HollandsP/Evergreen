"""
Terminal Themes Module

Provides various retro terminal color themes and visual styles.
"""

from dataclasses import dataclass
from typing import Tuple, Dict, Optional
import colorsys


@dataclass
class TerminalTheme:
    """Terminal color theme configuration"""
    
    name: str
    background: Tuple[int, int, int, int]  # RGBA
    foreground: Tuple[int, int, int, int]
    cursor: Tuple[int, int, int, int]
    selection: Tuple[int, int, int, int]
    
    # ANSI colors (normal and bright variants)
    black: Tuple[int, int, int, int]
    red: Tuple[int, int, int, int]
    green: Tuple[int, int, int, int]
    yellow: Tuple[int, int, int, int]
    blue: Tuple[int, int, int, int]
    magenta: Tuple[int, int, int, int]
    cyan: Tuple[int, int, int, int]
    white: Tuple[int, int, int, int]
    
    bright_black: Tuple[int, int, int, int]
    bright_red: Tuple[int, int, int, int]
    bright_green: Tuple[int, int, int, int]
    bright_yellow: Tuple[int, int, int, int]
    bright_blue: Tuple[int, int, int, int]
    bright_magenta: Tuple[int, int, int, int]
    bright_cyan: Tuple[int, int, int, int]
    bright_white: Tuple[int, int, int, int]
    
    # Visual effects
    glow_intensity: float = 0.0  # 0-1, phosphor glow effect
    scan_line_intensity: float = 0.0  # 0-1, CRT scanline effect
    noise_amount: float = 0.0  # 0-1, static noise
    curvature: float = 0.0  # 0-1, CRT screen curvature
    chromatic_aberration: float = 0.0  # 0-1, color fringing
    
    def get_ansi_color(self, code: int, bright: bool = False) -> Tuple[int, int, int, int]:
        """Get ANSI color by code"""
        colors = [
            self.black, self.red, self.green, self.yellow,
            self.blue, self.magenta, self.cyan, self.white
        ]
        bright_colors = [
            self.bright_black, self.bright_red, self.bright_green, self.bright_yellow,
            self.bright_blue, self.bright_magenta, self.bright_cyan, self.bright_white
        ]
        
        if 0 <= code <= 7:
            return bright_colors[code] if bright else colors[code]
        return self.foreground


# Predefined themes
THEMES: Dict[str, TerminalTheme] = {
    "matrix": TerminalTheme(
        name="Matrix",
        background=(0, 0, 0, 255),
        foreground=(0, 255, 0, 255),
        cursor=(0, 255, 0, 255),
        selection=(0, 100, 0, 128),
        black=(0, 0, 0, 255),
        red=(0, 200, 0, 255),
        green=(0, 255, 0, 255),
        yellow=(0, 255, 100, 255),
        blue=(0, 150, 0, 255),
        magenta=(0, 200, 50, 255),
        cyan=(0, 255, 150, 255),
        white=(0, 255, 200, 255),
        bright_black=(0, 50, 0, 255),
        bright_red=(0, 255, 50, 255),
        bright_green=(100, 255, 100, 255),
        bright_yellow=(150, 255, 150, 255),
        bright_blue=(0, 200, 100, 255),
        bright_magenta=(50, 255, 100, 255),
        bright_cyan=(100, 255, 200, 255),
        bright_white=(200, 255, 200, 255),
        glow_intensity=0.8,
        scan_line_intensity=0.3,
        noise_amount=0.1,
        curvature=0.2,
        chromatic_aberration=0.05
    ),
    
    "amber": TerminalTheme(
        name="Amber Phosphor",
        background=(20, 10, 0, 255),
        foreground=(255, 176, 0, 255),
        cursor=(255, 200, 0, 255),
        selection=(100, 50, 0, 128),
        black=(20, 10, 0, 255),
        red=(255, 100, 0, 255),
        green=(255, 176, 0, 255),
        yellow=(255, 220, 0, 255),
        blue=(200, 120, 0, 255),
        magenta=(255, 150, 50, 255),
        cyan=(255, 200, 100, 255),
        white=(255, 230, 150, 255),
        bright_black=(50, 25, 0, 255),
        bright_red=(255, 150, 50, 255),
        bright_green=(255, 200, 100, 255),
        bright_yellow=(255, 255, 150, 255),
        bright_blue=(230, 180, 50, 255),
        bright_magenta=(255, 200, 100, 255),
        bright_cyan=(255, 230, 150, 255),
        bright_white=(255, 255, 200, 255),
        glow_intensity=0.7,
        scan_line_intensity=0.4,
        noise_amount=0.15,
        curvature=0.3,
        chromatic_aberration=0.02
    ),
    
    "green_phosphor": TerminalTheme(
        name="Green Phosphor",
        background=(0, 10, 0, 255),
        foreground=(50, 255, 50, 255),
        cursor=(100, 255, 100, 255),
        selection=(0, 100, 0, 128),
        black=(0, 10, 0, 255),
        red=(50, 200, 50, 255),
        green=(50, 255, 50, 255),
        yellow=(150, 255, 50, 255),
        blue=(50, 150, 50, 255),
        magenta=(100, 200, 50, 255),
        cyan=(50, 255, 150, 255),
        white=(150, 255, 150, 255),
        bright_black=(0, 50, 0, 255),
        bright_red=(100, 255, 100, 255),
        bright_green=(150, 255, 150, 255),
        bright_yellow=(200, 255, 100, 255),
        bright_blue=(100, 200, 100, 255),
        bright_magenta=(150, 255, 100, 255),
        bright_cyan=(100, 255, 200, 255),
        bright_white=(200, 255, 200, 255),
        glow_intensity=0.6,
        scan_line_intensity=0.5,
        noise_amount=0.2,
        curvature=0.4,
        chromatic_aberration=0.03
    ),
    
    "retro_blue": TerminalTheme(
        name="Retro Blue",
        background=(0, 0, 20, 255),
        foreground=(100, 200, 255, 255),
        cursor=(150, 220, 255, 255),
        selection=(0, 50, 100, 128),
        black=(0, 0, 20, 255),
        red=(255, 100, 150, 255),
        green=(100, 255, 200, 255),
        yellow=(255, 255, 150, 255),
        blue=(100, 200, 255, 255),
        magenta=(200, 150, 255, 255),
        cyan=(150, 255, 255, 255),
        white=(200, 230, 255, 255),
        bright_black=(50, 50, 70, 255),
        bright_red=(255, 150, 200, 255),
        bright_green=(150, 255, 230, 255),
        bright_yellow=(255, 255, 200, 255),
        bright_blue=(150, 230, 255, 255),
        bright_magenta=(230, 200, 255, 255),
        bright_cyan=(200, 255, 255, 255),
        bright_white=(255, 255, 255, 255),
        glow_intensity=0.5,
        scan_line_intensity=0.3,
        noise_amount=0.1,
        curvature=0.2,
        chromatic_aberration=0.04
    ),
    
    "cyberpunk": TerminalTheme(
        name="Cyberpunk",
        background=(10, 0, 20, 255),
        foreground=(255, 0, 255, 255),
        cursor=(255, 100, 255, 255),
        selection=(100, 0, 100, 128),
        black=(10, 0, 20, 255),
        red=(255, 0, 100, 255),
        green=(0, 255, 200, 255),
        yellow=(255, 200, 0, 255),
        blue=(0, 200, 255, 255),
        magenta=(255, 0, 255, 255),
        cyan=(0, 255, 255, 255),
        white=(255, 200, 255, 255),
        bright_black=(50, 20, 70, 255),
        bright_red=(255, 100, 150, 255),
        bright_green=(100, 255, 230, 255),
        bright_yellow=(255, 255, 100, 255),
        bright_blue=(100, 230, 255, 255),
        bright_magenta=(255, 150, 255, 255),
        bright_cyan=(150, 255, 255, 255),
        bright_white=(255, 255, 255, 255),
        glow_intensity=0.9,
        scan_line_intensity=0.2,
        noise_amount=0.3,
        curvature=0.1,
        chromatic_aberration=0.08
    ),
    
    "classic": TerminalTheme(
        name="Classic Terminal",
        background=(0, 0, 0, 255),
        foreground=(192, 192, 192, 255),
        cursor=(255, 255, 255, 255),
        selection=(50, 50, 50, 128),
        black=(0, 0, 0, 255),
        red=(255, 0, 0, 255),
        green=(0, 255, 0, 255),
        yellow=(255, 255, 0, 255),
        blue=(0, 0, 255, 255),
        magenta=(255, 0, 255, 255),
        cyan=(0, 255, 255, 255),
        white=(192, 192, 192, 255),
        bright_black=(128, 128, 128, 255),
        bright_red=(255, 128, 128, 255),
        bright_green=(128, 255, 128, 255),
        bright_yellow=(255, 255, 128, 255),
        bright_blue=(128, 128, 255, 255),
        bright_magenta=(255, 128, 255, 255),
        bright_cyan=(128, 255, 255, 255),
        bright_white=(255, 255, 255, 255),
        glow_intensity=0.0,
        scan_line_intensity=0.0,
        noise_amount=0.0,
        curvature=0.0,
        chromatic_aberration=0.0
    ),
    
    "hacker": TerminalTheme(
        name="Hacker",
        background=(0, 0, 0, 255),
        foreground=(0, 255, 0, 255),
        cursor=(0, 255, 0, 255),
        selection=(0, 50, 0, 128),
        black=(0, 0, 0, 255),
        red=(255, 0, 0, 255),
        green=(0, 255, 0, 255),
        yellow=(255, 255, 0, 255),
        blue=(0, 100, 255, 255),
        magenta=(255, 0, 255, 255),
        cyan=(0, 255, 255, 255),
        white=(200, 200, 200, 255),
        bright_black=(100, 100, 100, 255),
        bright_red=(255, 100, 100, 255),
        bright_green=(100, 255, 100, 255),
        bright_yellow=(255, 255, 100, 255),
        bright_blue=(100, 150, 255, 255),
        bright_magenta=(255, 100, 255, 255),
        bright_cyan=(100, 255, 255, 255),
        bright_white=(255, 255, 255, 255),
        glow_intensity=0.4,
        scan_line_intensity=0.2,
        noise_amount=0.05,
        curvature=0.0,
        chromatic_aberration=0.01
    )
}


def get_theme(name: str) -> Optional[TerminalTheme]:
    """Get theme by name"""
    return THEMES.get(name.lower())


def list_themes() -> list[str]:
    """List available theme names"""
    return list(THEMES.keys())


def create_custom_theme(
    name: str,
    base_color: Tuple[int, int, int],
    style: str = "modern"
) -> TerminalTheme:
    """
    Create a custom theme based on a base color
    
    Args:
        name: Theme name
        base_color: Base RGB color
        style: Style preset ("modern", "retro", "minimal")
    
    Returns:
        Custom terminal theme
    """
    r, g, b = base_color
    h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
    
    # Generate color palette based on base color
    def make_color(h_offset: float, s_mult: float, v_mult: float) -> Tuple[int, int, int, int]:
        new_h = (h + h_offset) % 1.0
        new_s = min(1.0, s * s_mult)
        new_v = min(1.0, v * v_mult)
        rgb = colorsys.hsv_to_rgb(new_h, new_s, new_v)
        return (int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255), 255)
    
    # Background is darker version of base
    bg_color = make_color(0, 0.5, 0.1)
    
    # Style-specific effects
    effects = {
        "modern": (0.0, 0.0, 0.0, 0.0, 0.0),
        "retro": (0.6, 0.4, 0.1, 0.3, 0.03),
        "minimal": (0.0, 0.0, 0.0, 0.0, 0.0)
    }
    
    glow, scanline, noise, curve, chroma = effects.get(style, (0.0, 0.0, 0.0, 0.0, 0.0))
    
    return TerminalTheme(
        name=name,
        background=bg_color,
        foreground=(r, g, b, 255),
        cursor=(r, g, b, 255),
        selection=(*base_color, 128),
        black=bg_color,
        red=make_color(0.0, 1.0, 0.8),
        green=make_color(0.33, 1.0, 0.8),
        yellow=make_color(0.16, 1.0, 0.9),
        blue=make_color(0.66, 1.0, 0.8),
        magenta=make_color(0.83, 1.0, 0.8),
        cyan=make_color(0.5, 1.0, 0.8),
        white=make_color(0, 0.1, 1.0),
        bright_black=make_color(0, 0.3, 0.5),
        bright_red=make_color(0.0, 1.0, 1.0),
        bright_green=make_color(0.33, 1.0, 1.0),
        bright_yellow=make_color(0.16, 1.0, 1.0),
        bright_blue=make_color(0.66, 1.0, 1.0),
        bright_magenta=make_color(0.83, 1.0, 1.0),
        bright_cyan=make_color(0.5, 1.0, 1.0),
        bright_white=make_color(0, 0.0, 1.0),
        glow_intensity=glow,
        scan_line_intensity=scanline,
        noise_amount=noise,
        curvature=curve,
        chromatic_aberration=chroma
    )