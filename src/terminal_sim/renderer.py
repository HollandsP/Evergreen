"""
Terminal Renderer Module

Renders terminal frames to video with smooth animations and effects.
"""

import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from typing import List, Optional, Tuple, Callable
import cv2
import tempfile
from dataclasses import dataclass
import math

from .themes import TerminalTheme
from .fonts import TerminalFont
from .effects import (
    TypingEffect, GlitchEffect, StaticEffect, 
    CursorEffect, ScanlineEffect, CompositeEffect
)


@dataclass
class TerminalState:
    """Represents the current state of the terminal"""
    text: str = ""
    cursor_pos: Tuple[int, int] = (0, 0)
    scroll_offset: int = 0
    selection: Optional[Tuple[int, int]] = None


class TerminalRenderer:
    """Main terminal rendering engine"""
    
    def __init__(self, 
                 width: int = 800,
                 height: int = 600,
                 theme: TerminalTheme = None,
                 font: TerminalFont = None,
                 fps: int = 30):
        """
        Initialize terminal renderer
        
        Args:
            width: Terminal width in pixels
            height: Terminal height in pixels
            theme: Terminal theme (uses classic if None)
            font: Terminal font (auto-detect if None)
            fps: Target frames per second
        """
        self.width = width
        self.height = height
        self.fps = fps
        self.frame_duration = 1.0 / fps
        
        # Initialize theme and font
        from .themes import get_theme
        self.theme = theme or get_theme("classic")
        self.font = font or TerminalFont()
        
        # Calculate terminal dimensions in characters
        self.cols = width // self.font.char_width
        self.rows = height // self.font.char_height
        
        # Terminal state
        self.state = TerminalState()
        self.buffer: List[str] = [""]  # Terminal text buffer
        
        # Effects
        self.effects = CompositeEffect()
        self.typing_effect = TypingEffect()
        self.cursor_effect = CursorEffect()
        
        # Video writer
        self.video_writer: Optional[cv2.VideoWriter] = None
        self.temp_dir = tempfile.mkdtemp()
        self.frame_count = 0
    
    def add_effect(self, effect):
        """Add an effect to the renderer"""
        self.effects.add_effect(effect)
    
    def clear(self):
        """Clear terminal"""
        self.buffer = [""]
        self.state.text = ""
        self.state.cursor_pos = (0, 0)
        self.state.scroll_offset = 0
    
    def write(self, text: str):
        """Write text to terminal (immediate)"""
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if i > 0:
                self.buffer.append("")
            if self.buffer:
                self.buffer[-1] += line
        
        # Update cursor position
        if self.buffer:
            last_line = len(self.buffer) - 1
            col = len(self.buffer[-1])
            self.state.cursor_pos = (col, last_line)
        
        # Handle scrolling
        if len(self.buffer) > self.rows:
            self.state.scroll_offset = len(self.buffer) - self.rows
    
    def type_text(self, text: str):
        """Set text for typing animation"""
        self.typing_effect.set_text(text)
    
    def render_frame(self, delta_time: float = None) -> Image.Image:
        """
        Render a single frame
        
        Args:
            delta_time: Time since last frame (uses frame_duration if None)
        
        Returns:
            Rendered frame image
        """
        if delta_time is None:
            delta_time = self.frame_duration
        
        # Update effects
        self.effects.update(delta_time)
        self.cursor_effect.update(delta_time)
        
        # Update typing animation
        if not self.typing_effect.is_complete():
            typed_text = self.typing_effect.update(delta_time)
            self.clear()
            self.write(typed_text)
        
        # Create base image
        image = Image.new('RGBA', (self.width, self.height), self.theme.background)
        draw = ImageDraw.Draw(image)
        
        # Apply CRT curvature if enabled
        if self.theme.curvature > 0:
            image = self._apply_crt_curvature(image, self.theme.curvature)
        
        # Render terminal content
        self._render_content(draw)
        
        # Render cursor
        self._render_cursor(draw)
        
        # Apply phosphor glow if enabled
        if self.theme.glow_intensity > 0:
            image = self._apply_phosphor_glow(image, self.theme.glow_intensity)
        
        # Apply chromatic aberration if enabled
        if self.theme.chromatic_aberration > 0:
            image = self._apply_chromatic_aberration(image, self.theme.chromatic_aberration)
        
        # Apply effects
        image = self.effects.apply_to_image(image)
        
        return image
    
    def _render_content(self, draw: ImageDraw.Draw):
        """Render terminal text content"""
        visible_start = self.state.scroll_offset
        visible_end = visible_start + self.rows
        
        for y, line_idx in enumerate(range(visible_start, min(visible_end, len(self.buffer)))):
            if line_idx < len(self.buffer):
                line = self.buffer[line_idx]
                
                # Apply text effects
                line = self.effects.apply_to_text(line)
                
                # Render each character
                for x, char in enumerate(line[:self.cols]):
                    if char != ' ':
                        char_x = x * self.font.char_width
                        char_y = y * self.font.char_height
                        
                        # Check if character is in selection
                        color = self.theme.foreground
                        if self._is_in_selection(x, y):
                            # Draw selection background
                            draw.rectangle(
                                [char_x, char_y, 
                                 char_x + self.font.char_width,
                                 char_y + self.font.char_height],
                                fill=self.theme.selection
                            )
                        
                        # Draw character
                        draw.text(
                            (char_x + 1, char_y + 2),
                            char,
                            font=self.font.font,
                            fill=color
                        )
    
    def _render_cursor(self, draw: ImageDraw.Draw):
        """Render cursor"""
        if self.cursor_effect.visible:
            col, row = self.state.cursor_pos
            
            # Adjust for scrolling
            visual_row = row - self.state.scroll_offset
            
            if 0 <= visual_row < self.rows and col < self.cols:
                x = col * self.font.char_width
                y = visual_row * self.font.char_height
                
                self.cursor_effect.draw_cursor(
                    draw, x, y,
                    self.font.char_width,
                    self.font.char_height,
                    self.theme.cursor
                )
    
    def _is_in_selection(self, x: int, y: int) -> bool:
        """Check if position is in selection"""
        if not self.state.selection:
            return False
        
        # TODO: Implement selection logic
        return False
    
    def _apply_phosphor_glow(self, image: Image.Image, intensity: float) -> Image.Image:
        """Apply phosphor glow effect"""
        # Create glow layer
        glow = image.copy()
        
        # Apply Gaussian blur
        radius = int(3 * intensity)
        glow = glow.filter(ImageFilter.GaussianBlur(radius=radius))
        
        # Blend with original
        return Image.blend(image, glow, intensity * 0.5)
    
    def _apply_crt_curvature(self, image: Image.Image, amount: float) -> Image.Image:
        """Apply CRT screen curvature distortion"""
        img_array = np.array(image)
        h, w = img_array.shape[:2]
        
        # Create coordinate grids
        x = np.linspace(-1, 1, w)
        y = np.linspace(-1, 1, h)
        X, Y = np.meshgrid(x, y)
        
        # Apply barrel distortion
        r = np.sqrt(X**2 + Y**2)
        factor = 1 + amount * r**2
        
        X_dist = X * factor
        Y_dist = Y * factor
        
        # Convert back to pixel coordinates
        X_pixel = ((X_dist + 1) * 0.5 * (w - 1)).astype(np.float32)
        Y_pixel = ((Y_dist + 1) * 0.5 * (h - 1)).astype(np.float32)
        
        # Remap image
        result = cv2.remap(img_array, X_pixel, Y_pixel, cv2.INTER_LINEAR)
        
        return Image.fromarray(result)
    
    def _apply_chromatic_aberration(self, image: Image.Image, amount: float) -> Image.Image:
        """Apply chromatic aberration (color fringing)"""
        img_array = np.array(image)
        
        if len(img_array.shape) < 3:
            return image
        
        # Shift color channels slightly
        shift = int(amount * 5)
        
        # Shift red channel left, blue channel right
        if shift > 0:
            img_array[:, shift:, 0] = img_array[:, :-shift, 0]
            img_array[:, :-shift, 2] = img_array[:, shift:, 2]
        
        return Image.fromarray(img_array)
    
    def start_recording(self, output_path: str, with_alpha: bool = False):
        """
        Start recording frames to video
        
        Args:
            output_path: Output video file path
            with_alpha: Export with alpha channel (requires FFV1 codec)
        """
        fourcc = cv2.VideoWriter_fourcc(*'FFV1') if with_alpha else cv2.VideoWriter_fourcc(*'mp4v')
        
        self.video_writer = cv2.VideoWriter(
            output_path,
            fourcc,
            self.fps,
            (self.width, self.height),
            True
        )
        
        self.frame_count = 0
        self.recording_alpha = with_alpha
    
    def record_frame(self, frame: Optional[Image.Image] = None):
        """Record a frame to video"""
        if not self.video_writer:
            return
        
        if frame is None:
            frame = self.render_frame()
        
        # Convert to OpenCV format
        if self.recording_alpha and frame.mode == 'RGBA':
            # Save as BGRA for alpha support
            cv_frame = cv2.cvtColor(np.array(frame), cv2.COLOR_RGBA2BGRA)
        else:
            # Convert to BGR for standard video
            if frame.mode == 'RGBA':
                frame = frame.convert('RGB')
            cv_frame = cv2.cvtColor(np.array(frame), cv2.COLOR_RGB2BGR)
        
        self.video_writer.write(cv_frame)
        self.frame_count += 1
    
    def stop_recording(self):
        """Stop recording and save video"""
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
    
    def render_animation(self, duration: float, update_callback: Optional[Callable] = None) -> List[Image.Image]:
        """
        Render an animation sequence
        
        Args:
            duration: Animation duration in seconds
            update_callback: Optional callback for updating state each frame
        
        Returns:
            List of rendered frames
        """
        frames = []
        num_frames = int(duration * self.fps)
        
        for i in range(num_frames):
            if update_callback:
                update_callback(i / self.fps, i, num_frames)
            
            frame = self.render_frame()
            frames.append(frame)
        
        return frames
    
    def export_animation(self, output_path: str, duration: float,
                        update_callback: Optional[Callable] = None,
                        with_alpha: bool = False):
        """
        Export animation directly to video file
        
        Args:
            output_path: Output video file path
            duration: Animation duration in seconds
            update_callback: Optional callback for updating state
            with_alpha: Export with alpha channel
        """
        self.start_recording(output_path, with_alpha)
        
        num_frames = int(duration * self.fps)
        for i in range(num_frames):
            if update_callback:
                update_callback(i / self.fps, i, num_frames)
            
            self.record_frame()
        
        self.stop_recording()
    
    def render_command_sequence(self, commands: List[Tuple[str, float]], 
                               output_path: str, with_alpha: bool = False):
        """
        Render a sequence of terminal commands
        
        Args:
            commands: List of (command_text, pause_duration) tuples
            output_path: Output video file path
            with_alpha: Export with alpha channel
        """
        self.start_recording(output_path, with_alpha)
        
        for command, pause in commands:
            # Type command
            self.type_text(command)
            
            while not self.typing_effect.is_complete():
                self.record_frame()
            
            # Show completed command with cursor for pause duration
            pause_frames = int(pause * self.fps)
            for _ in range(pause_frames):
                self.record_frame()
            
            # Add newline
            self.write("\n")
        
        self.stop_recording()