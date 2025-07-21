"""
Terminal Effects Module

Provides various visual effects for terminal simulation including
typing animation, glitch effects, static, and cursor animations.
"""

import random
import numpy as np
from PIL import Image, ImageDraw
from typing import List, Tuple, Optional, Callable
import math


class TypingEffect:
    """Creates realistic typing animations with variable speed"""
    
    def __init__(self, base_speed: float = 0.1, variation: float = 0.3):
        """
        Initialize typing effect
        
        Args:
            base_speed: Base typing speed in seconds per character
            variation: Random variation in typing speed (0-1)
        """
        self.base_speed = base_speed
        self.variation = variation
        self.current_text = ""
        self.target_text = ""
        self.char_index = 0
        self.time_accumulator = 0.0
        self.next_char_time = self._get_next_char_time()
    
    def _get_next_char_time(self) -> float:
        """Calculate time until next character appears"""
        variation = random.uniform(-self.variation, self.variation)
        return self.base_speed * (1 + variation)
    
    def set_text(self, text: str):
        """Set the target text to type"""
        self.target_text = text
        self.current_text = ""
        self.char_index = 0
        self.time_accumulator = 0.0
        self.next_char_time = self._get_next_char_time()
    
    def update(self, delta_time: float) -> str:
        """
        Update the typing animation
        
        Args:
            delta_time: Time elapsed since last update
            
        Returns:
            Current visible text
        """
        if self.char_index >= len(self.target_text):
            return self.current_text
        
        self.time_accumulator += delta_time
        
        while self.time_accumulator >= self.next_char_time and self.char_index < len(self.target_text):
            self.current_text += self.target_text[self.char_index]
            self.char_index += 1
            self.time_accumulator -= self.next_char_time
            self.next_char_time = self._get_next_char_time()
            
            # Simulate pauses after punctuation
            if self.char_index > 0 and self.target_text[self.char_index - 1] in '.!?':
                self.next_char_time *= 3
            elif self.char_index > 0 and self.target_text[self.char_index - 1] == ',':
                self.next_char_time *= 2
        
        return self.current_text
    
    def is_complete(self) -> bool:
        """Check if typing animation is complete"""
        return self.char_index >= len(self.target_text)


class GlitchEffect:
    """Creates glitch effects for terminal display"""
    
    def __init__(self, intensity: float = 0.5):
        """
        Initialize glitch effect
        
        Args:
            intensity: Glitch intensity (0-1)
        """
        self.intensity = intensity
        self.glitch_chars = "▓▒░█▄▀▌▐└┘┌┐╔╗╚╝║═╬"
        self.active = False
        self.duration = 0.0
        self.time_accumulator = 0.0
    
    def trigger(self, duration: float = 0.5):
        """Trigger a glitch effect"""
        self.active = True
        self.duration = duration
        self.time_accumulator = 0.0
    
    def update(self, delta_time: float):
        """Update glitch state"""
        if self.active:
            self.time_accumulator += delta_time
            if self.time_accumulator >= self.duration:
                self.active = False
    
    def apply_to_text(self, text: str) -> str:
        """Apply glitch effect to text"""
        if not self.active:
            return text
        
        glitched = list(text)
        num_glitches = int(len(text) * self.intensity * random.random())
        
        for _ in range(num_glitches):
            if glitched:
                pos = random.randint(0, len(glitched) - 1)
                if glitched[pos] not in '\n\r\t ':
                    glitched[pos] = random.choice(self.glitch_chars)
        
        return ''.join(glitched)
    
    def apply_to_image(self, image: Image.Image) -> Image.Image:
        """Apply glitch effect to image"""
        if not self.active:
            return image
        
        img_array = np.array(image)
        height, width = img_array.shape[:2]
        
        # Random horizontal shifts
        if random.random() < self.intensity:
            shift_amount = int(width * 0.1 * random.random())
            shift_row = random.randint(0, height - 1)
            img_array[shift_row] = np.roll(img_array[shift_row], shift_amount, axis=0)
        
        # Color channel shifts
        if len(img_array.shape) == 3 and random.random() < self.intensity:
            channel = random.randint(0, 2)
            shift = random.randint(-5, 5)
            img_array[:, :, channel] = np.roll(img_array[:, :, channel], shift, axis=0)
        
        # Random noise blocks
        num_blocks = int(5 * self.intensity)
        for _ in range(num_blocks):
            x = random.randint(0, width - 20)
            y = random.randint(0, height - 10)
            w = random.randint(5, 20)
            h = random.randint(2, 10)
            
            noise = np.random.randint(0, 255, (h, w, img_array.shape[2]), dtype=np.uint8)
            img_array[y:y+h, x:x+w] = noise
        
        return Image.fromarray(img_array)


class StaticEffect:
    """Creates static/noise effects"""
    
    def __init__(self, intensity: float = 0.3):
        """
        Initialize static effect
        
        Args:
            intensity: Static intensity (0-1)
        """
        self.intensity = intensity
        self.phase = 0.0
    
    def update(self, delta_time: float):
        """Update static animation phase"""
        self.phase += delta_time * 10  # Animate static
    
    def apply_to_image(self, image: Image.Image) -> Image.Image:
        """Apply static effect to image"""
        img_array = np.array(image)
        height, width = img_array.shape[:2]
        
        # Generate static noise
        noise = np.random.randint(0, int(255 * self.intensity), 
                                 (height, width), dtype=np.uint8)
        
        # Create scanline pattern
        scanlines = np.zeros((height, width), dtype=np.uint8)
        for y in range(height):
            if y % 2 == 0:
                scanlines[y, :] = int(20 * self.intensity)
        
        # Apply effects
        if len(img_array.shape) == 3:
            for i in range(3):
                img_array[:, :, i] = np.clip(
                    img_array[:, :, i].astype(np.int16) + noise + scanlines, 
                    0, 255
                ).astype(np.uint8)
        else:
            img_array = np.clip(
                img_array.astype(np.int16) + noise + scanlines,
                0, 255
            ).astype(np.uint8)
        
        return Image.fromarray(img_array)


class CursorEffect:
    """Creates blinking cursor animations"""
    
    def __init__(self, blink_rate: float = 0.5, style: str = "block"):
        """
        Initialize cursor effect
        
        Args:
            blink_rate: Cursor blink rate in seconds
            style: Cursor style ("block", "underline", "pipe")
        """
        self.blink_rate = blink_rate
        self.style = style
        self.time_accumulator = 0.0
        self.visible = True
    
    def update(self, delta_time: float):
        """Update cursor blink state"""
        self.time_accumulator += delta_time
        if self.time_accumulator >= self.blink_rate:
            self.visible = not self.visible
            self.time_accumulator = 0.0
    
    def get_cursor_char(self) -> str:
        """Get cursor character based on style and visibility"""
        if not self.visible:
            return " "
        
        cursor_chars = {
            "block": "█",
            "underline": "_",
            "pipe": "|"
        }
        return cursor_chars.get(self.style, "█")
    
    def draw_cursor(self, draw: ImageDraw.Draw, x: int, y: int, 
                    char_width: int, char_height: int, color: Tuple[int, ...]):
        """Draw cursor on image"""
        if not self.visible:
            return
        
        if self.style == "block":
            draw.rectangle([x, y, x + char_width, y + char_height], fill=color)
        elif self.style == "underline":
            draw.rectangle([x, y + char_height - 2, x + char_width, y + char_height], fill=color)
        elif self.style == "pipe":
            draw.rectangle([x, y, x + 2, y + char_height], fill=color)


class ScanlineEffect:
    """Creates CRT scanline effects"""
    
    def __init__(self, intensity: float = 0.2, speed: float = 1.0):
        """
        Initialize scanline effect
        
        Args:
            intensity: Scanline darkness (0-1)
            speed: Scanline movement speed
        """
        self.intensity = intensity
        self.speed = speed
        self.offset = 0.0
    
    def update(self, delta_time: float):
        """Update scanline position"""
        self.offset += delta_time * self.speed * 100
    
    def apply_to_image(self, image: Image.Image) -> Image.Image:
        """Apply scanline effect to image"""
        img_array = np.array(image)
        height, width = img_array.shape[:2]
        
        # Create scanline pattern
        for y in range(height):
            # Moving scanline
            moving_intensity = abs(math.sin((y + self.offset) * 0.1)) * 0.3
            
            # Static scanline pattern
            if y % 3 == 0:
                darkness = 1.0 - self.intensity
                img_array[y] = (img_array[y] * darkness).astype(np.uint8)
            elif y % 3 == 1:
                darkness = 1.0 - (self.intensity * 0.5)
                img_array[y] = (img_array[y] * darkness).astype(np.uint8)
            
            # Apply moving scanline
            if moving_intensity > 0.1:
                img_array[y] = (img_array[y] * (1.0 - moving_intensity * self.intensity)).astype(np.uint8)
        
        # Add slight bloom effect
        if len(img_array.shape) == 3:
            bloom = img_array.copy()
            bloom = np.clip(bloom * 1.1, 0, 255).astype(np.uint8)
            img_array = ((img_array * 0.9 + bloom * 0.1)).astype(np.uint8)
        
        return Image.fromarray(img_array)


class CompositeEffect:
    """Combines multiple effects"""
    
    def __init__(self):
        self.effects: List[Callable] = []
    
    def add_effect(self, effect: Callable):
        """Add an effect to the composite"""
        self.effects.append(effect)
    
    def update(self, delta_time: float):
        """Update all effects"""
        for effect in self.effects:
            if hasattr(effect, 'update'):
                effect.update(delta_time)
    
    def apply_to_image(self, image: Image.Image) -> Image.Image:
        """Apply all effects to image"""
        result = image
        for effect in self.effects:
            if hasattr(effect, 'apply_to_image'):
                result = effect.apply_to_image(result)
        return result
    
    def apply_to_text(self, text: str) -> str:
        """Apply all text effects"""
        result = text
        for effect in self.effects:
            if hasattr(effect, 'apply_to_text'):
                result = effect.apply_to_text(result)
        return result