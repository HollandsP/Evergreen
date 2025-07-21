"""
Terminal effects module for video generation
"""
from .terminal_effects import (
    TerminalRenderer,
    AnimationSequence,
    TerminalTheme,
    parse_terminal_commands
)

__all__ = [
    'TerminalRenderer',
    'AnimationSequence', 
    'TerminalTheme',
    'parse_terminal_commands'
]