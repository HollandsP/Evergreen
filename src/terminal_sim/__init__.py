"""
Terminal UI Simulator Package

A comprehensive terminal simulation system for creating realistic
terminal animations with various effects and themes.
"""

from .effects import (
    TypingEffect,
    GlitchEffect,
    StaticEffect,
    CursorEffect,
    ScanlineEffect
)

from .renderer import TerminalRenderer
from .themes import TerminalTheme, get_theme
from .compositor import TerminalCompositor
from .fonts import TerminalFont

__version__ = "0.1.0"
__all__ = [
    "TypingEffect",
    "GlitchEffect", 
    "StaticEffect",
    "CursorEffect",
    "ScanlineEffect",
    "TerminalRenderer",
    "TerminalTheme",
    "get_theme",
    "TerminalCompositor",
    "TerminalFont"
]