"""
Terminal Font Management Module

Handles terminal fonts including monospace fonts and ASCII art rendering.
"""

from PIL import Image, ImageDraw, ImageFont
from typing import Optional, Tuple, Dict, List
import os
import platform


class TerminalFont:
    """Manages terminal fonts and text rendering"""
    
    # Common monospace fonts by platform
    FONT_SUGGESTIONS = {
        "Windows": [
            "Consolas",
            "Courier New",
            "Lucida Console",
            "Cascadia Mono",
            "Terminal"
        ],
        "Darwin": [  # macOS
            "Monaco",
            "Menlo",
            "SF Mono",
            "Courier New",
            "Andale Mono"
        ],
        "Linux": [
            "DejaVu Sans Mono",
            "Liberation Mono",
            "Ubuntu Mono",
            "Courier New",
            "Monospace"
        ]
    }
    
    # Fallback ASCII art characters for special effects
    ASCII_BLOCKS = {
        'full': '█',
        'dark': '▓',
        'medium': '▒',
        'light': '░',
        'top_half': '▀',
        'bottom_half': '▄',
        'left_half': '▌',
        'right_half': '▐',
        'corners': ['┌', '┐', '└', '┘'],
        'lines': ['─', '│', '┼', '├', '┤', '┬', '┴']
    }
    
    def __init__(self, font_name: Optional[str] = None, size: int = 14):
        """
        Initialize terminal font
        
        Args:
            font_name: Font name or path (None for auto-detect)
            size: Font size in pixels
        """
        self.size = size
        self.font = self._load_font(font_name, size)
        self.char_width, self.char_height = self._calculate_char_dimensions()
        self._char_cache: Dict[str, Image.Image] = {}
    
    def _load_font(self, font_name: Optional[str], size: int) -> ImageFont.FreeTypeFont:
        """Load font with fallback to system defaults"""
        if font_name and os.path.exists(font_name):
            # Load from file path
            try:
                return ImageFont.truetype(font_name, size)
            except:
                pass
        
        # Try to load by name
        if font_name:
            try:
                return ImageFont.truetype(font_name, size)
            except:
                pass
        
        # Try platform-specific fonts
        system = platform.system()
        suggestions = self.FONT_SUGGESTIONS.get(system, [])
        
        for font in suggestions:
            try:
                return ImageFont.truetype(font, size)
            except:
                continue
        
        # Fallback to default
        return ImageFont.load_default()
    
    def _calculate_char_dimensions(self) -> Tuple[int, int]:
        """Calculate character dimensions for monospace layout"""
        # Use 'M' as reference character for monospace fonts
        bbox = self.font.getbbox('M')
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        
        # Add some padding
        return width + 2, height + 4
    
    def get_text_dimensions(self, text: str) -> Tuple[int, int]:
        """Get dimensions for rendered text"""
        lines = text.split('\n')
        max_width = max(len(line) for line in lines) if lines else 0
        height = len(lines)
        
        return max_width * self.char_width, height * self.char_height
    
    def render_text(self, text: str, color: Tuple[int, ...], 
                   bg_color: Optional[Tuple[int, ...]] = None) -> Image.Image:
        """
        Render text to image
        
        Args:
            text: Text to render
            color: Text color (RGB or RGBA)
            bg_color: Background color (optional)
        
        Returns:
            Rendered text image
        """
        width, height = self.get_text_dimensions(text)
        if width == 0 or height == 0:
            return Image.new('RGBA', (1, 1), (0, 0, 0, 0))
        
        # Create image
        if bg_color:
            image = Image.new('RGBA', (width, height), bg_color)
        else:
            image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        
        draw = ImageDraw.Draw(image)
        
        # Render each character
        lines = text.split('\n')
        for y, line in enumerate(lines):
            for x, char in enumerate(line):
                if char != ' ':
                    draw.text(
                        (x * self.char_width, y * self.char_height),
                        char,
                        font=self.font,
                        fill=color
                    )
        
        return image
    
    def render_char(self, char: str, color: Tuple[int, ...]) -> Image.Image:
        """Render a single character (cached)"""
        cache_key = f"{char}_{color}"
        
        if cache_key not in self._char_cache:
            image = Image.new('RGBA', (self.char_width, self.char_height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            draw.text((1, 2), char, font=self.font, fill=color)
            self._char_cache[cache_key] = image
        
        return self._char_cache[cache_key]
    
    def create_ascii_art(self, image: Image.Image, width: int = 80, 
                        charset: str = "standard") -> str:
        """
        Convert image to ASCII art
        
        Args:
            image: Source image
            width: Target width in characters
            charset: Character set ("standard", "blocks", "gradient")
        
        Returns:
            ASCII art string
        """
        # Define character sets
        charsets = {
            "standard": " .:-=+*#%@",
            "blocks": " ░▒▓█",
            "gradient": " .'`^\",:;Il!i><~+_-?][}{1)(|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$",
            "binary": " █"
        }
        
        chars = charsets.get(charset, charsets["standard"])
        
        # Resize image
        aspect_ratio = image.height / image.width
        height = int(width * aspect_ratio * 0.55)  # Adjust for font aspect ratio
        image = image.resize((width, height), Image.Resampling.LANCZOS)
        
        # Convert to grayscale
        image = image.convert('L')
        
        # Convert pixels to ASCII
        ascii_art = []
        pixels = image.load()
        
        for y in range(height):
            line = []
            for x in range(width):
                brightness = pixels[x, y]
                char_index = int((brightness / 255) * (len(chars) - 1))
                line.append(chars[char_index])
            ascii_art.append(''.join(line))
        
        return '\n'.join(ascii_art)
    
    def render_box(self, width: int, height: int, style: str = "single") -> str:
        """
        Create a box using box-drawing characters
        
        Args:
            width: Box width in characters
            height: Box height in characters
            style: Box style ("single", "double", "rounded")
        
        Returns:
            Box string
        """
        styles = {
            "single": {
                'tl': '┌', 'tr': '┐', 'bl': '└', 'br': '┘',
                'h': '─', 'v': '│'
            },
            "double": {
                'tl': '╔', 'tr': '╗', 'bl': '╚', 'br': '╝',
                'h': '═', 'v': '║'
            },
            "rounded": {
                'tl': '╭', 'tr': '╮', 'bl': '╰', 'br': '╯',
                'h': '─', 'v': '│'
            }
        }
        
        s = styles.get(style, styles["single"])
        
        # Build box
        lines = []
        
        # Top line
        lines.append(s['tl'] + s['h'] * (width - 2) + s['tr'])
        
        # Middle lines
        for _ in range(height - 2):
            lines.append(s['v'] + ' ' * (width - 2) + s['v'])
        
        # Bottom line
        lines.append(s['bl'] + s['h'] * (width - 2) + s['br'])
        
        return '\n'.join(lines)
    
    def render_progress_bar(self, progress: float, width: int = 40, 
                           style: str = "blocks") -> str:
        """
        Create a progress bar
        
        Args:
            progress: Progress value (0-1)
            width: Bar width in characters
            style: Bar style ("blocks", "lines", "dots")
        
        Returns:
            Progress bar string
        """
        filled = int(progress * width)
        empty = width - filled
        
        styles = {
            "blocks": ('█', '░'),
            "lines": ('━', '─'),
            "dots": ('●', '○'),
            "arrows": ('▶', '▷')
        }
        
        fill_char, empty_char = styles.get(style, styles["blocks"])
        
        bar = fill_char * filled + empty_char * empty
        percentage = f"{int(progress * 100):3d}%"
        
        return f"[{bar}] {percentage}"
    
    def create_table(self, headers: List[str], rows: List[List[str]], 
                    style: str = "single") -> str:
        """
        Create a formatted table
        
        Args:
            headers: Column headers
            rows: Table rows
            style: Table style
        
        Returns:
            Formatted table string
        """
        # Calculate column widths
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(str(cell)))
        
        # Add padding
        col_widths = [w + 2 for w in col_widths]
        
        # Box drawing characters
        if style == "double":
            h, v, tl, tr, bl, br = '═', '║', '╔', '╗', '╚', '╝'
            cross, t_down, t_up, t_right, t_left = '╬', '╦', '╩', '╠', '╣'
        else:
            h, v, tl, tr, bl, br = '─', '│', '┌', '┐', '└', '┘'
            cross, t_down, t_up, t_right, t_left = '┼', '┬', '┴', '├', '┤'
        
        lines = []
        
        # Top border
        top = tl
        for i, w in enumerate(col_widths):
            top += h * w
            if i < len(col_widths) - 1:
                top += t_down
        top += tr
        lines.append(top)
        
        # Headers
        header_line = v
        for i, (header, width) in enumerate(zip(headers, col_widths)):
            header_line += f" {header:^{width-2}} "
            if i < len(headers) - 1:
                header_line += v
        header_line += v
        lines.append(header_line)
        
        # Separator
        sep = t_right
        for i, w in enumerate(col_widths):
            sep += h * w
            if i < len(col_widths) - 1:
                sep += cross
        sep += t_left
        lines.append(sep)
        
        # Rows
        for row in rows:
            row_line = v
            for i, (cell, width) in enumerate(zip(row, col_widths)):
                row_line += f" {str(cell):{width-2}} "
                if i < len(row) - 1:
                    row_line += v
            row_line += v
            lines.append(row_line)
        
        # Bottom border
        bottom = bl
        for i, w in enumerate(col_widths):
            bottom += h * w
            if i < len(col_widths) - 1:
                bottom += t_up
        bottom += br
        lines.append(bottom)
        
        return '\n'.join(lines)