"""
Terminal UI effects and animations for video generation
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from typing import List, Dict, Any, Tuple, Optional
import ffmpeg
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class TerminalTheme(Enum):
    """Available terminal color themes"""
    DARK = "dark"
    LIGHT = "light"
    MATRIX = "matrix"
    HACKER = "hacker"
    VSCODE = "vscode"


@dataclass
class ThemeColors:
    """Color configuration for terminal themes"""
    background: Tuple[int, int, int]
    foreground: Tuple[int, int, int]
    cursor: Tuple[int, int, int]
    selection: Tuple[int, int, int, int]  # RGBA
    comment: Tuple[int, int, int]
    keyword: Tuple[int, int, int]
    string: Tuple[int, int, int]
    error: Tuple[int, int, int]
    success: Tuple[int, int, int]
    warning: Tuple[int, int, int]


# Theme configurations
THEMES = {
    TerminalTheme.DARK: ThemeColors(
        background=(12, 12, 12),
        foreground=(204, 204, 204),
        cursor=(255, 255, 255),
        selection=(51, 51, 51, 128),
        comment=(106, 153, 85),
        keyword=(86, 156, 214),
        string=(206, 145, 120),
        error=(244, 71, 71),
        success=(87, 166, 74),
        warning=(255, 203, 107)
    ),
    TerminalTheme.MATRIX: ThemeColors(
        background=(0, 0, 0),
        foreground=(0, 255, 65),
        cursor=(0, 255, 65),
        selection=(0, 128, 32, 128),
        comment=(0, 180, 45),
        keyword=(0, 255, 65),
        string=(0, 200, 50),
        error=(255, 0, 0),
        success=(0, 255, 65),
        warning=(255, 255, 0)
    ),
    TerminalTheme.HACKER: ThemeColors(
        background=(10, 10, 10),
        foreground=(0, 255, 0),
        cursor=(255, 255, 0),
        selection=(0, 100, 0, 128),
        comment=(0, 200, 0),
        keyword=(255, 0, 255),
        string=(0, 255, 255),
        error=(255, 0, 0),
        success=(0, 255, 0),
        warning=(255, 165, 0)
    ),
    TerminalTheme.LIGHT: ThemeColors(
        background=(255, 255, 255),
        foreground=(36, 36, 36),
        cursor=(0, 0, 0),
        selection=(200, 200, 200, 128),
        comment=(0, 128, 0),
        keyword=(0, 0, 255),
        string=(163, 21, 21),
        error=(255, 0, 0),
        success=(0, 128, 0),
        warning=(255, 140, 0)
    ),
    TerminalTheme.VSCODE: ThemeColors(
        background=(30, 30, 30),
        foreground=(212, 212, 212),
        cursor=(255, 255, 255),
        selection=(38, 79, 120, 128),
        comment=(96, 139, 78),
        keyword=(197, 134, 192),
        string=(206, 145, 120),
        error=(244, 71, 71),
        success=(75, 202, 129),
        warning=(220, 220, 170)
    )
}


class TerminalRenderer:
    """Renders terminal animations frame by frame"""
    
    def __init__(self, 
                 width: int = 1920, 
                 height: int = 1080,
                 cols: int = 80,
                 rows: int = 24,
                 theme: TerminalTheme = TerminalTheme.DARK,
                 font_size: int = 16):
        """
        Initialize terminal renderer
        
        Args:
            width: Video width in pixels
            height: Video height in pixels
            cols: Terminal columns
            rows: Terminal rows
            theme: Color theme to use
            font_size: Font size for terminal text
        """
        self.width = width
        self.height = height
        self.cols = cols
        self.rows = rows
        self.theme = THEMES[theme]
        self.font_size = font_size
        
        # Calculate terminal dimensions
        self.char_width = width // cols
        self.char_height = height // rows
        
        # Terminal state
        self.buffer: List[List[str]] = [[' ' for _ in range(cols)] for _ in range(rows)]
        self.cursor_row = 0
        self.cursor_col = 0
        self.cursor_visible = True
        
        # Try to load a monospace font
        self.font = self._load_font()
        
        # Frame counter for animations
        self.frame_count = 0
        
    def _load_font(self) -> ImageFont.FreeTypeFont:
        """Load a monospace font for terminal rendering"""
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
            "/System/Library/Fonts/Monaco.dfont",
            "C:\\Windows\\Fonts\\consola.ttf",
            "/app/fonts/FiraCode-Regular.ttf"  # Custom bundled font
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    return ImageFont.truetype(font_path, self.font_size)
                except Exception:
                    continue
        
        # Fallback to default font
        logger.warning("No monospace font found, using default")
        return ImageFont.load_default()
    
    def clear(self):
        """Clear the terminal buffer"""
        self.buffer = [[' ' for _ in range(self.cols)] for _ in range(self.rows)]
        self.cursor_row = 0
        self.cursor_col = 0
    
    def write_text(self, text: str, instant: bool = False):
        """
        Write text to terminal buffer
        
        Args:
            text: Text to write
            instant: If True, write all text immediately
        """
        for char in text:
            if char == '\n':
                self.cursor_row += 1
                self.cursor_col = 0
                if self.cursor_row >= self.rows:
                    # Scroll up
                    self.buffer.pop(0)
                    self.buffer.append([' ' for _ in range(self.cols)])
                    self.cursor_row = self.rows - 1
            elif char == '\r':
                self.cursor_col = 0
            elif char == '\t':
                # Tab to next 4-space boundary
                self.cursor_col = ((self.cursor_col // 4) + 1) * 4
            else:
                if self.cursor_col < self.cols and self.cursor_row < self.rows:
                    self.buffer[self.cursor_row][self.cursor_col] = char
                    self.cursor_col += 1
                    
                if self.cursor_col >= self.cols:
                    self.cursor_col = 0
                    self.cursor_row += 1
                    if self.cursor_row >= self.rows:
                        # Scroll up
                        self.buffer.pop(0)
                        self.buffer.append([' ' for _ in range(self.cols)])
                        self.cursor_row = self.rows - 1
    
    def render_frame(self) -> Image.Image:
        """Render current terminal state to an image"""
        # Create image with background color
        img = Image.new('RGB', (self.width, self.height), self.theme.background)
        draw = ImageDraw.Draw(img)
        
        # Draw terminal content
        for row in range(self.rows):
            for col in range(self.cols):
                char = self.buffer[row][col]
                if char != ' ':
                    x = col * self.char_width
                    y = row * self.char_height
                    draw.text((x, y), char, fill=self.theme.foreground, font=self.font)
        
        # Draw cursor if visible
        if self.cursor_visible and self.frame_count % 60 < 30:  # Blink every second at 30fps
            x = self.cursor_col * self.char_width
            y = self.cursor_row * self.char_height
            draw.rectangle(
                [x, y, x + self.char_width - 1, y + self.char_height - 1],
                fill=self.theme.cursor
            )
        
        self.frame_count += 1
        return img
    
    def create_typing_animation(self, 
                               text: str, 
                               duration: float,
                               fps: int = 30) -> List[Image.Image]:
        """
        Create a typing animation for the given text
        
        Args:
            text: Text to animate
            duration: Total duration in seconds
            fps: Frames per second
            
        Returns:
            List of PIL Images representing the animation frames
        """
        frames = []
        total_frames = int(duration * fps)
        chars_per_frame = max(1, len(text) // total_frames)
        
        # Initial frame with empty terminal
        frames.append(self.render_frame())
        
        # Type text progressively
        text_buffer = ""
        char_index = 0
        
        for frame_num in range(total_frames):
            # Add characters for this frame
            chars_to_add = min(chars_per_frame, len(text) - char_index)
            if chars_to_add > 0:
                new_chars = text[char_index:char_index + chars_to_add]
                text_buffer += new_chars
                self.write_text(new_chars)
                char_index += chars_to_add
            
            # Render frame
            frames.append(self.render_frame())
        
        # Add a few frames at the end with cursor blinking
        for _ in range(fps):  # 1 second of cursor blinking
            frames.append(self.render_frame())
        
        return frames
    
    def export_video(self, frames: List[Image.Image], output_path: str, fps: int = 30):
        """
        Export frames as video using FFmpeg
        
        Args:
            frames: List of PIL Images
            output_path: Output video file path
            fps: Frames per second
        """
        # Create temporary directory for frames
        temp_dir = os.path.dirname(output_path)
        os.makedirs(temp_dir, exist_ok=True)
        
        # Save frames as temporary images
        frame_pattern = os.path.join(temp_dir, "frame_%05d.png")
        for i, frame in enumerate(frames):
            frame.save(frame_pattern % i)
        
        # Use ffmpeg to create video
        try:
            (
                ffmpeg
                .input(frame_pattern.replace("%05d", "*"), pattern_type='glob', framerate=fps)
                .output(output_path, vcodec='libx264', pix_fmt='yuv420p', crf=23)
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            logger.info(f"Video exported successfully: {output_path}")
        except ffmpeg.Error as e:
            logger.error(f"FFmpeg error: {e.stderr.decode()}")
            raise
        finally:
            # Clean up temporary frames
            import glob
            for frame_file in glob.glob(frame_pattern.replace("%05d", "*")):
                os.remove(frame_file)


class AnimationSequence:
    """Manages animation sequences and timing"""
    
    def __init__(self, renderer: TerminalRenderer):
        self.renderer = renderer
        self.sequences = []
    
    def add_typing(self, text: str, start_time: float, duration: float):
        """Add a typing animation sequence"""
        self.sequences.append({
            'type': 'typing',
            'text': text,
            'start_time': start_time,
            'duration': duration
        })
    
    def add_instant_text(self, text: str, start_time: float):
        """Add instant text display"""
        self.sequences.append({
            'type': 'instant',
            'text': text,
            'start_time': start_time
        })
    
    def add_clear(self, start_time: float):
        """Add terminal clear command"""
        self.sequences.append({
            'type': 'clear',
            'start_time': start_time
        })
    
    def render_sequence(self, total_duration: float, fps: int = 30) -> List[Image.Image]:
        """Render the complete animation sequence"""
        frames = []
        total_frames = int(total_duration * fps)
        
        # Sort sequences by start time
        sorted_sequences = sorted(self.sequences, key=lambda x: x['start_time'])
        
        current_time = 0.0
        seq_index = 0
        
        for frame_num in range(total_frames):
            current_time = frame_num / fps
            
            # Process sequences that should start
            while seq_index < len(sorted_sequences) and sorted_sequences[seq_index]['start_time'] <= current_time:
                seq = sorted_sequences[seq_index]
                
                if seq['type'] == 'clear':
                    self.renderer.clear()
                elif seq['type'] == 'instant':
                    self.renderer.write_text(seq['text'], instant=True)
                elif seq['type'] == 'typing':
                    # For typing, we'll handle it frame by frame
                    pass
                
                seq_index += 1
            
            # Render current frame
            frames.append(self.renderer.render_frame())
        
        return frames


def parse_terminal_commands(text: str) -> List[Dict[str, Any]]:
    """
    Parse on-screen text to identify terminal commands and output
    
    Args:
        text: Raw on-screen text from script
        
    Returns:
        List of parsed command segments
    """
    segments = []
    lines = text.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if line.startswith('$') or line.startswith('>'):
            # Command line
            segments.append({
                'type': 'command',
                'text': line,
                'typing_speed': 0.05  # 50ms per character
            })
        elif line.startswith('#'):
            # Comment
            segments.append({
                'type': 'comment', 
                'text': line,
                'typing_speed': 0.03  # Faster for comments
            })
        else:
            # Output or text
            segments.append({
                'type': 'output',
                'text': line,
                'instant': True  # Output appears instantly
            })
    
    return segments