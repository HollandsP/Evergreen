"""
Advanced visual effects for terminal UI including Matrix rain, syntax highlighting, and more.
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random
import math
from typing import List, Tuple, Optional, Dict, Any
import re
from dataclasses import dataclass
from enum import Enum

from .effects import Effect
from .fonts import get_font


class Language(Enum):
    """Supported programming languages for syntax highlighting."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    RUST = "rust"
    GO = "go"
    CPP = "cpp"
    BASH = "bash"
    JSON = "json"
    YAML = "yaml"
    MARKDOWN = "markdown"


@dataclass
class SyntaxTheme:
    """Color theme for syntax highlighting."""
    background: Tuple[int, int, int]
    text: Tuple[int, int, int]
    keyword: Tuple[int, int, int]
    string: Tuple[int, int, int]
    comment: Tuple[int, int, int]
    number: Tuple[int, int, int]
    function: Tuple[int, int, int]
    class_name: Tuple[int, int, int]
    operator: Tuple[int, int, int]
    bracket: Tuple[int, int, int]


# Predefined syntax themes
SYNTAX_THEMES = {
    "monokai": SyntaxTheme(
        background=(39, 40, 34),
        text=(248, 248, 242),
        keyword=(249, 38, 114),
        string=(230, 219, 116),
        comment=(117, 113, 94),
        number=(174, 129, 255),
        function=(166, 226, 46),
        class_name=(166, 226, 46),
        operator=(249, 38, 114),
        bracket=(248, 248, 242)
    ),
    "dracula": SyntaxTheme(
        background=(40, 42, 54),
        text=(248, 248, 242),
        keyword=(255, 121, 198),
        string=(241, 250, 140),
        comment=(98, 114, 164),
        number=(189, 147, 249),
        function=(80, 250, 123),
        class_name=(139, 233, 253),
        operator=(255, 121, 198),
        bracket=(248, 248, 242)
    ),
    "solarized": SyntaxTheme(
        background=(0, 43, 54),
        text=(131, 148, 150),
        keyword=(133, 153, 0),
        string=(42, 161, 152),
        comment=(88, 110, 117),
        number=(220, 50, 47),
        function=(181, 137, 0),
        class_name=(38, 139, 210),
        operator=(133, 153, 0),
        bracket=(131, 148, 150)
    )
}


class MatrixRainEffect(Effect):
    """Matrix-style digital rain effect."""
    
    def __init__(
        self,
        intensity: float = 1.0,
        drop_speed: float = 1.0,
        character_set: str = "ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ01",
        color: Tuple[int, int, int] = (0, 255, 0),
        fade_length: int = 20
    ):
        super().__init__(intensity)
        self.drop_speed = drop_speed
        self.character_set = character_set
        self.color = color
        self.fade_length = fade_length
        self.drops: List[Dict[str, Any]] = []
        self.initialized = False
    
    def _initialize_drops(self, width: int, height: int, char_width: int, char_height: int):
        """Initialize rain drop positions."""
        cols = width // char_width
        self.drops = []
        
        for col in range(cols):
            self.drops.append({
                'x': col * char_width,
                'y': random.randint(-height, 0),
                'speed': random.uniform(0.5, 1.5) * self.drop_speed,
                'chars': [random.choice(self.character_set) for _ in range(self.fade_length)],
                'brightness': random.uniform(0.7, 1.0)
            })
        
        self.initialized = True
    
    def apply(self, frame: np.ndarray, time: float, delta_time: float) -> np.ndarray:
        """Apply Matrix rain effect to frame."""
        height, width = frame.shape[:2]
        
        # Get font for Matrix characters
        font_size = 16
        try:
            font = ImageFont.truetype("Monaco", font_size)
        except:
            font = get_font(font_size)
        
        # Estimate character dimensions
        char_width = font_size * 0.6
        char_height = font_size
        
        if not self.initialized:
            self._initialize_drops(width, height, int(char_width), int(char_height))
        
        # Create overlay for rain
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Update and draw drops
        for drop in self.drops:
            # Update position
            drop['y'] += drop['speed'] * delta_time * 60
            
            # Reset if off screen
            if drop['y'] > height + self.fade_length * char_height:
                drop['y'] = -self.fade_length * char_height
                drop['chars'] = [random.choice(self.character_set) for _ in range(self.fade_length)]
                drop['brightness'] = random.uniform(0.7, 1.0)
            
            # Draw characters with fade
            for i, char in enumerate(drop['chars']):
                char_y = drop['y'] + i * char_height
                
                if 0 <= char_y <= height:
                    # Calculate fade
                    if i == 0:
                        # Leading character is brightest
                        alpha = 255
                        char_color = (
                            min(255, int(self.color[0] * drop['brightness'] * 1.2)),
                            min(255, int(self.color[1] * drop['brightness'] * 1.2)),
                            min(255, int(self.color[2] * drop['brightness'] * 1.2))
                        )
                    else:
                        # Fade based on position
                        fade = 1 - (i / self.fade_length)
                        alpha = int(255 * fade * drop['brightness'])
                        char_color = tuple(int(c * drop['brightness']) for c in self.color)
                    
                    # Occasionally change character
                    if random.random() < 0.02:
                        drop['chars'][i] = random.choice(self.character_set)
                    
                    # Draw character
                    draw.text(
                        (drop['x'], char_y),
                        drop['chars'][i],
                        font=font,
                        fill=(*char_color, alpha)
                    )
        
        # Convert overlay to numpy array
        overlay_array = np.array(overlay)
        
        # Blend with original frame
        if len(frame.shape) == 3:
            # RGB frame
            frame_rgba = np.zeros((height, width, 4), dtype=np.uint8)
            frame_rgba[:, :, :3] = frame
            frame_rgba[:, :, 3] = 255
        else:
            # Already RGBA
            frame_rgba = frame.copy()
        
        # Alpha blending
        alpha = overlay_array[:, :, 3:4] / 255.0 * self.intensity
        frame_rgba[:, :, :3] = (1 - alpha) * frame_rgba[:, :, :3] + alpha * overlay_array[:, :, :3]
        
        return frame_rgba


class SyntaxHighlightEffect(Effect):
    """Syntax highlighting effect for code display."""
    
    def __init__(
        self,
        language: Language = Language.PYTHON,
        theme: str = "monokai",
        intensity: float = 1.0
    ):
        super().__init__(intensity)
        self.language = language
        self.theme = SYNTAX_THEMES[theme]
        self.patterns = self._get_language_patterns()
    
    def _get_language_patterns(self) -> Dict[str, str]:
        """Get regex patterns for language syntax."""
        if self.language == Language.PYTHON:
            return {
                'keyword': r'\b(def|class|import|from|return|if|else|elif|for|while|try|except|finally|with|as|pass|break|continue|lambda|yield|global|nonlocal|assert|async|await)\b',
                'string': r'(""".*?"""|\'\'\'.*?\'\'\'|".*?"|\'.*?\')',
                'comment': r'#.*?$',
                'number': r'\b\d+\.?\d*\b',
                'function': r'\b([a-zA-Z_]\w*)\s*\(',
                'class': r'\bclass\s+([A-Z]\w*)',
                'operator': r'[+\-*/%=<>!&|^~]',
                'bracket': r'[(){}\[\]]'
            }
        elif self.language == Language.JAVASCRIPT:
            return {
                'keyword': r'\b(const|let|var|function|class|return|if|else|for|while|do|switch|case|break|continue|try|catch|finally|throw|async|await|import|export|from|default)\b',
                'string': r'(`.*?`|".*?"|\'.*?\')',
                'comment': r'(//.*?$|/\*.*?\*/)',
                'number': r'\b\d+\.?\d*\b',
                'function': r'\b([a-zA-Z_$][\w$]*)\s*\(',
                'class': r'\bclass\s+([A-Z]\w*)',
                'operator': r'[+\-*/%=<>!&|^~?:]',
                'bracket': r'[(){}\[\]]'
            }
        else:
            # Default patterns
            return {
                'keyword': r'\b(if|else|for|while|return|function|class|def|import|export)\b',
                'string': r'(".*?"|\'.*?\')',
                'comment': r'(#|//|/\*).*?$',
                'number': r'\b\d+\.?\d*\b',
                'operator': r'[+\-*/%=<>!&|^~]',
                'bracket': r'[(){}\[\]]'
            }
    
    def highlight_code(self, code: str) -> List[Tuple[str, Tuple[int, int, int]]]:
        """Apply syntax highlighting to code and return colored segments."""
        # Start with default text color
        highlighted = [(code, self.theme.text)]
        
        # Apply patterns in order of precedence
        for pattern_name, pattern in self.patterns.items():
            new_highlighted = []
            
            for text, color in highlighted:
                if color != self.theme.text:
                    # Already highlighted
                    new_highlighted.append((text, color))
                    continue
                
                # Find matches
                last_end = 0
                for match in re.finditer(pattern, text, re.MULTILINE | re.DOTALL):
                    # Add text before match
                    if match.start() > last_end:
                        new_highlighted.append((text[last_end:match.start()], self.theme.text))
                    
                    # Add highlighted match
                    if pattern_name == 'keyword':
                        new_highlighted.append((match.group(), self.theme.keyword))
                    elif pattern_name == 'string':
                        new_highlighted.append((match.group(), self.theme.string))
                    elif pattern_name == 'comment':
                        new_highlighted.append((match.group(), self.theme.comment))
                    elif pattern_name == 'number':
                        new_highlighted.append((match.group(), self.theme.number))
                    elif pattern_name == 'function':
                        # Highlight function name only
                        func_name = match.group(1) if match.lastindex else match.group()
                        new_highlighted.append((func_name, self.theme.function))
                        new_highlighted.append(("(", self.theme.bracket))
                    elif pattern_name == 'class':
                        new_highlighted.append((match.group(), self.theme.class_name))
                    elif pattern_name == 'operator':
                        new_highlighted.append((match.group(), self.theme.operator))
                    elif pattern_name == 'bracket':
                        new_highlighted.append((match.group(), self.theme.bracket))
                    
                    last_end = match.end()
                
                # Add remaining text
                if last_end < len(text):
                    new_highlighted.append((text[last_end:], self.theme.text))
            
            highlighted = new_highlighted
        
        return highlighted
    
    def apply(self, frame: np.ndarray, time: float, delta_time: float) -> np.ndarray:
        """This effect is applied during text rendering, not post-processing."""
        return frame


class HologramEffect(Effect):
    """Holographic display effect with interference patterns."""
    
    def __init__(
        self,
        intensity: float = 1.0,
        scan_speed: float = 1.0,
        interference: float = 0.5,
        color: Tuple[int, int, int] = (0, 200, 255)
    ):
        super().__init__(intensity)
        self.scan_speed = scan_speed
        self.interference = interference
        self.color = color
    
    def apply(self, frame: np.ndarray, time: float, delta_time: float) -> np.ndarray:
        """Apply holographic effect to frame."""
        height, width = frame.shape[:2]
        
        # Create hologram overlay
        overlay = np.zeros((height, width, 4), dtype=np.uint8)
        
        # Horizontal scan lines
        scan_pos = int((time * self.scan_speed * 100) % height)
        for y in range(0, height, 3):
            alpha = 30
            # Brighter scan line
            if abs(y - scan_pos) < 5:
                alpha = 100
            
            overlay[y, :] = (*self.color, alpha)
        
        # Vertical interference pattern
        for x in range(width):
            interference_value = math.sin(x * 0.02 + time * 2) * self.interference
            brightness = max(0, min(255, 128 + interference_value * 127))
            
            # Apply interference to column
            overlay[:, x, 3] = (overlay[:, x, 3] * brightness / 255).astype(np.uint8)
        
        # Add random glitches
        if random.random() < 0.02:
            glitch_y = random.randint(0, height - 10)
            glitch_height = random.randint(5, 20)
            overlay[glitch_y:glitch_y+glitch_height, :] = (*self.color, 150)
        
        # Apply chromatic aberration
        shift = 2
        overlay[shift:, :, 0] = overlay[:-shift, :, 0]  # Shift red channel
        overlay[:, shift:, 2] = overlay[:, :-shift, 2]  # Shift blue channel
        
        # Blend with original frame
        alpha = overlay[:, :, 3:4] / 255.0 * self.intensity
        
        if len(frame.shape) == 3 and frame.shape[2] == 3:
            # RGB frame
            result = frame.copy()
            result = (1 - alpha) * result + alpha * overlay[:, :, :3]
        else:
            # RGBA frame
            result = frame.copy()
            result[:, :, :3] = (1 - alpha) * result[:, :, :3] + alpha * overlay[:, :, :3]
        
        return result.astype(np.uint8)


class RetroComputerEffect(Effect):
    """Retro computer boot sequence and interface effects."""
    
    def __init__(
        self,
        intensity: float = 1.0,
        boot_time: float = 3.0,
        bios_color: Tuple[int, int, int] = (255, 255, 255),
        show_cursor: bool = True
    ):
        super().__init__(intensity)
        self.boot_time = boot_time
        self.bios_color = bios_color
        self.show_cursor = show_cursor
        self.boot_messages = [
            "BIOS v2.31 - Advanced Terminal Systems",
            "Memory Test: 640K OK",
            "Detecting hardware...",
            "CPU: Neural Processor 9000 @ 4.2 GHz",
            "RAM: 64GB Quantum Memory Detected",
            "Storage: 10TB Holographic Drive",
            "Network: Neural Link Established",
            "Loading System...",
            "",
            "EVERGREEN OS v4.2.1",
            "Copyright (c) 2025 Future Systems Inc.",
            "",
            "Initializing subsystems...",
            "[OK] Quantum Core",
            "[OK] Neural Interface",
            "[OK] Holographic Display",
            "[OK] Time Sync",
            "",
            "System Ready.",
            ""
        ]
        self.current_line = 0
        self.char_index = 0
        self.last_update = 0
    
    def apply(self, frame: np.ndarray, time: float, delta_time: float) -> np.ndarray:
        """Apply retro computer boot effect."""
        if time > self.boot_time:
            return frame
        
        height, width = frame.shape[:2]
        
        # Create overlay for boot text
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 200))
        draw = ImageDraw.Draw(overlay)
        
        # Get monospace font
        font_size = 14
        font = get_font(font_size)
        
        # Calculate text progress
        chars_per_second = 30
        total_chars = sum(len(msg) for msg in self.boot_messages[:self.current_line + 1])
        current_chars = int(time * chars_per_second)
        
        # Draw boot messages
        y_offset = 20
        chars_drawn = 0
        
        for i, message in enumerate(self.boot_messages):
            if chars_drawn + len(message) <= current_chars:
                # Draw complete line
                draw.text((20, y_offset), message, font=font, fill=(*self.bios_color, 255))
                chars_drawn += len(message)
            elif chars_drawn < current_chars:
                # Draw partial line
                chars_to_draw = current_chars - chars_drawn
                partial_message = message[:chars_to_draw]
                draw.text((20, y_offset), partial_message, font=font, fill=(*self.bios_color, 255))
                
                # Draw cursor
                if self.show_cursor and int(time * 2) % 2 == 0:
                    cursor_x = 20 + len(partial_message) * font_size * 0.6
                    draw.rectangle(
                        [(cursor_x, y_offset), (cursor_x + font_size * 0.6, y_offset + font_size)],
                        fill=(*self.bios_color, 255)
                    )
                break
            else:
                break
            
            y_offset += font_size + 4
        
        # Convert overlay to numpy array
        overlay_array = np.array(overlay)
        
        # Blend with frame
        if len(frame.shape) == 3 and frame.shape[2] == 3:
            # RGB frame
            frame_rgba = np.zeros((height, width, 4), dtype=np.uint8)
            frame_rgba[:, :, :3] = frame
            frame_rgba[:, :, 3] = 255
            frame = frame_rgba
        
        # Alpha blending
        alpha = overlay_array[:, :, 3:4] / 255.0 * self.intensity
        frame[:, :, :3] = (1 - alpha) * frame[:, :, :3] + alpha * overlay_array[:, :, :3]
        
        return frame


class DataVisualizationEffect(Effect):
    """Real-time data visualization overlay effect."""
    
    def __init__(
        self,
        intensity: float = 1.0,
        data_type: str = "network",  # network, cpu, memory, custom
        position: Tuple[int, int] = (20, 20),
        size: Tuple[int, int] = (300, 200),
        color_scheme: str = "cyan"
    ):
        super().__init__(intensity)
        self.data_type = data_type
        self.position = position
        self.size = size
        self.color_schemes = {
            "cyan": [(0, 200, 255), (0, 150, 200), (0, 100, 150)],
            "green": [(0, 255, 0), (0, 200, 0), (0, 150, 0)],
            "amber": [(255, 200, 0), (200, 150, 0), (150, 100, 0)],
            "red": [(255, 0, 0), (200, 0, 0), (150, 0, 0)]
        }
        self.colors = self.color_schemes[color_scheme]
        self.data_history = []
        self.max_history = 50
    
    def apply(self, frame: np.ndarray, time: float, delta_time: float) -> np.ndarray:
        """Apply data visualization overlay."""
        height, width = frame.shape[:2]
        
        # Generate data point
        if self.data_type == "network":
            value = 50 + 30 * math.sin(time * 2) + random.uniform(-10, 10)
        elif self.data_type == "cpu":
            value = 30 + 20 * math.sin(time * 1.5) + 10 * math.cos(time * 3) + random.uniform(-5, 5)
        elif self.data_type == "memory":
            value = 60 + 10 * math.sin(time * 0.5) + random.uniform(-5, 5)
        else:
            value = random.uniform(0, 100)
        
        # Update history
        self.data_history.append(value)
        if len(self.data_history) > self.max_history:
            self.data_history.pop(0)
        
        # Create visualization overlay
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        x, y = self.position
        w, h = self.size
        
        # Draw background
        draw.rectangle(
            [(x, y), (x + w, y + h)],
            fill=(0, 0, 0, 150)
        )
        
        # Draw border
        draw.rectangle(
            [(x, y), (x + w, y + h)],
            outline=(*self.colors[0], 200),
            width=2
        )
        
        # Draw title
        font = get_font(12)
        title = f"{self.data_type.upper()} MONITOR"
        draw.text((x + 10, y + 5), title, font=font, fill=(*self.colors[0], 255))
        
        # Draw grid
        grid_spacing = 20
        for gx in range(x + grid_spacing, x + w, grid_spacing):
            draw.line([(gx, y + 25), (gx, y + h - 10)], fill=(*self.colors[2], 50))
        for gy in range(y + 25 + grid_spacing, y + h - 10, grid_spacing):
            draw.line([(x + 10, gy), (x + w - 10, gy)], fill=(*self.colors[2], 50))
        
        # Draw data line
        if len(self.data_history) > 1:
            points = []
            for i, value in enumerate(self.data_history):
                px = x + 10 + (i / self.max_history) * (w - 20)
                py = y + h - 10 - (value / 100) * (h - 40)
                points.append((px, py))
            
            # Draw line segments
            for i in range(len(points) - 1):
                draw.line([points[i], points[i + 1]], fill=(*self.colors[0], 255), width=2)
            
            # Draw current value
            current_value = self.data_history[-1]
            value_text = f"{current_value:.1f}%"
            draw.text((x + w - 60, y + 5), value_text, font=font, fill=(*self.colors[1], 255))
        
        # Convert to numpy array
        overlay_array = np.array(overlay)
        
        # Blend with frame
        if len(frame.shape) == 3 and frame.shape[2] == 3:
            # RGB frame
            frame_rgba = np.zeros((height, width, 4), dtype=np.uint8)
            frame_rgba[:, :, :3] = frame
            frame_rgba[:, :, 3] = 255
            frame = frame_rgba
        
        # Alpha blending
        alpha = overlay_array[:, :, 3:4] / 255.0 * self.intensity
        frame[:, :, :3] = (1 - alpha) * frame[:, :, :3] + alpha * overlay_array[:, :, :3]
        
        return frame


class ParticleSystemEffect(Effect):
    """Advanced particle system for various visual effects."""
    
    def __init__(
        self,
        intensity: float = 1.0,
        particle_type: str = "sparks",  # sparks, snow, fire, dust
        emission_rate: int = 10,
        particle_lifetime: float = 2.0,
        gravity: float = 100.0,
        wind: Tuple[float, float] = (0, 0)
    ):
        super().__init__(intensity)
        self.particle_type = particle_type
        self.emission_rate = emission_rate
        self.particle_lifetime = particle_lifetime
        self.gravity = gravity
        self.wind = wind
        self.particles = []
        self.emission_accumulator = 0
    
    def emit_particle(self, width: int, height: int):
        """Emit a new particle."""
        if self.particle_type == "sparks":
            particle = {
                'x': random.uniform(0, width),
                'y': height - 10,
                'vx': random.uniform(-100, 100),
                'vy': random.uniform(-300, -100),
                'size': random.uniform(1, 3),
                'color': (255, random.randint(200, 255), 0),
                'lifetime': random.uniform(0.5, self.particle_lifetime),
                'age': 0
            }
        elif self.particle_type == "snow":
            particle = {
                'x': random.uniform(-50, width + 50),
                'y': -10,
                'vx': random.uniform(-20, 20),
                'vy': random.uniform(20, 50),
                'size': random.uniform(2, 6),
                'color': (255, 255, 255),
                'lifetime': self.particle_lifetime,
                'age': 0
            }
        elif self.particle_type == "fire":
            particle = {
                'x': random.uniform(width * 0.4, width * 0.6),
                'y': height,
                'vx': random.uniform(-30, 30),
                'vy': random.uniform(-150, -50),
                'size': random.uniform(5, 10),
                'color': (255, random.randint(100, 200), 0),
                'lifetime': random.uniform(0.5, 1.0),
                'age': 0
            }
        else:  # dust
            particle = {
                'x': random.uniform(0, width),
                'y': random.uniform(0, height),
                'vx': random.uniform(-10, 10),
                'vy': random.uniform(-5, 5),
                'size': random.uniform(1, 3),
                'color': (200, 180, 150),
                'lifetime': self.particle_lifetime,
                'age': 0
            }
        
        self.particles.append(particle)
    
    def apply(self, frame: np.ndarray, time: float, delta_time: float) -> np.ndarray:
        """Apply particle system effect."""
        height, width = frame.shape[:2]
        
        # Emit new particles
        self.emission_accumulator += self.emission_rate * delta_time
        while self.emission_accumulator >= 1:
            self.emit_particle(width, height)
            self.emission_accumulator -= 1
        
        # Create overlay for particles
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Update and draw particles
        particles_to_remove = []
        
        for particle in self.particles:
            # Update physics
            particle['vx'] += self.wind[0] * delta_time
            particle['vy'] += (self.gravity + self.wind[1]) * delta_time
            
            particle['x'] += particle['vx'] * delta_time
            particle['y'] += particle['vy'] * delta_time
            
            particle['age'] += delta_time
            
            # Check if particle should be removed
            if particle['age'] >= particle['lifetime'] or particle['y'] > height + 10:
                particles_to_remove.append(particle)
                continue
            
            # Calculate alpha based on age
            age_ratio = particle['age'] / particle['lifetime']
            
            if self.particle_type == "fire":
                # Fire particles fade and change color
                alpha = int(255 * (1 - age_ratio))
                color = (
                    particle['color'][0],
                    int(particle['color'][1] * (1 - age_ratio * 0.5)),
                    int(particle['color'][2] * age_ratio)
                )
            else:
                alpha = int(255 * (1 - age_ratio * 0.3))
                color = particle['color']
            
            # Draw particle with glow
            if particle['size'] > 3:
                # Draw glow for larger particles
                for glow_size in range(int(particle['size'] * 2), 0, -2):
                    glow_alpha = int(alpha * (1 - glow_size / (particle['size'] * 2)) * 0.3)
                    draw.ellipse(
                        [(particle['x'] - glow_size/2, particle['y'] - glow_size/2),
                         (particle['x'] + glow_size/2, particle['y'] + glow_size/2)],
                        fill=(*color, glow_alpha)
                    )
            
            # Draw particle
            draw.ellipse(
                [(particle['x'] - particle['size']/2, particle['y'] - particle['size']/2),
                 (particle['x'] + particle['size']/2, particle['y'] + particle['size']/2)],
                fill=(*color, alpha)
            )
        
        # Remove dead particles
        for particle in particles_to_remove:
            self.particles.remove(particle)
        
        # Convert to numpy array
        overlay_array = np.array(overlay)
        
        # Blend with frame
        if len(frame.shape) == 3 and frame.shape[2] == 3:
            # RGB frame
            frame_rgba = np.zeros((height, width, 4), dtype=np.uint8)
            frame_rgba[:, :, :3] = frame
            frame_rgba[:, :, 3] = 255
            frame = frame_rgba
        
        # Alpha blending
        alpha = overlay_array[:, :, 3:4] / 255.0 * self.intensity
        frame[:, :, :3] = (1 - alpha) * frame[:, :, :3] + alpha * overlay_array[:, :, :3]
        
        return frame