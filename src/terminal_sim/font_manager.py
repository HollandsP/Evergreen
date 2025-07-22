"""
Advanced font management system with bundled fonts and custom rendering.
"""

import os
import base64
import tempfile
from typing import Dict, Optional, List, Tuple
from PIL import Image, ImageDraw, ImageFont
import requests
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class FontManager:
    """Manages custom fonts with fallback options and bundled fonts."""
    
    # Base64 encoded minimal bitmap font for ultimate fallback
    BUILTIN_BITMAP_FONT = """
    iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAYAAADED76LAAAABHNCSVQICAgIfAhkiAAAAAlwSFlz
    AAALEwAACxMBAJqcGAAAADxJREFUGJVjYMABmBgYGBj+MzD8Z8AD/jMwMDCwMDAwMHBwcOAVZ2Fg
    YGBgYcEjzsLAwMDA8p+B4T8DAAO5BQUHrJjmAAAAAElFTkSuQmCC
    """
    
    def __init__(self):
        self.fonts_dir = Path(tempfile.gettempdir()) / "evergreen_fonts"
        self.fonts_dir.mkdir(exist_ok=True)
        self.font_cache: Dict[Tuple[str, int], ImageFont.FreeTypeFont] = {}
        self.available_fonts: Dict[str, Path] = {}
        self._initialize_fonts()
    
    def _initialize_fonts(self):
        """Initialize bundled fonts and download if necessary."""
        # Define font sources (using open-source fonts)
        font_sources = {
            "FiraCode": {
                "url": "https://github.com/tonsky/FiraCode/releases/download/6.2/Fira_Code_v6.2.zip",
                "filename": "FiraCode-Regular.ttf",
                "style": "monospace"
            },
            "JetBrainsMono": {
                "url": "https://github.com/JetBrains/JetBrainsMono/releases/download/v2.304/JetBrainsMono-2.304.zip",
                "filename": "JetBrainsMono-Regular.ttf",
                "style": "monospace"
            },
            "IBMPlexMono": {
                "url": "https://github.com/IBM/plex/releases/download/v6.0.1/IBMPlexMono.zip",
                "filename": "IBMPlexMono-Regular.ttf",
                "style": "monospace"
            },
            "SourceCodePro": {
                "url": "https://github.com/adobe-fonts/source-code-pro/releases/download/2.038R-ro%2F1.058R-it/source-code-pro-2.038R-ro-1.058R-it.zip",
                "filename": "SourceCodePro-Regular.ttf",
                "style": "monospace"
            },
            "Hack": {
                "url": "https://github.com/source-foundry/Hack/releases/download/v3.003/Hack-v3.003-ttf.zip",
                "filename": "Hack-Regular.ttf",
                "style": "monospace"
            }
        }
        
        # Check for system fonts first
        self._find_system_fonts()
        
        # Load bundled fonts from resources
        self._load_bundled_fonts()
    
    def _find_system_fonts(self):
        """Find available system fonts."""
        system_font_paths = []
        
        # Platform-specific font directories
        if os.name == 'posix':
            if os.path.exists('/System/Library/Fonts'):  # macOS
                system_font_paths.extend([
                    '/System/Library/Fonts',
                    '/Library/Fonts',
                    os.path.expanduser('~/Library/Fonts')
                ])
            else:  # Linux
                system_font_paths.extend([
                    '/usr/share/fonts',
                    '/usr/local/share/fonts',
                    os.path.expanduser('~/.fonts'),
                    os.path.expanduser('~/.local/share/fonts')
                ])
        elif os.name == 'nt':  # Windows
            system_font_paths.extend([
                'C:\\Windows\\Fonts',
                os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Windows', 'Fonts')
            ])
        
        # Search for monospace fonts
        monospace_fonts = [
            'Monaco', 'Menlo', 'Consolas', 'Courier New', 'Courier',
            'DejaVu Sans Mono', 'Liberation Mono', 'Ubuntu Mono',
            'Fira Code', 'JetBrains Mono', 'Source Code Pro', 'Hack'
        ]
        
        for font_dir in system_font_paths:
            if os.path.exists(font_dir):
                for font_file in os.listdir(font_dir):
                    if font_file.endswith(('.ttf', '.otf')):
                        font_path = Path(font_dir) / font_file
                        font_name = font_file.replace('.ttf', '').replace('.otf', '')
                        
                        # Check if it's a monospace font we want
                        for mono_font in monospace_fonts:
                            if mono_font.lower().replace(' ', '') in font_name.lower().replace(' ', ''):
                                self.available_fonts[mono_font] = font_path
                                logger.info(f"Found system font: {mono_font} at {font_path}")
    
    def _load_bundled_fonts(self):
        """Load bundled fonts from package resources."""
        # Create a simple bitmap font as fallback
        self._create_bitmap_font()
        
        # Try to load embedded font data
        embedded_fonts = {
            "Terminal": self._get_terminal_font_data(),
            "Matrix": self._get_matrix_font_data(),
            "Retro": self._get_retro_font_data()
        }
        
        for font_name, font_data in embedded_fonts.items():
            if font_data:
                font_path = self.fonts_dir / f"{font_name}.ttf"
                with open(font_path, 'wb') as f:
                    f.write(font_data)
                self.available_fonts[font_name] = font_path
    
    def _create_bitmap_font(self):
        """Create a simple bitmap font for ultimate fallback."""
        # This creates a very basic 8x8 pixel font
        font_path = self.fonts_dir / "Bitmap.ttf"
        
        # For now, we'll use system fallback
        # In production, you'd embed a real bitmap font
        self.available_fonts["Bitmap"] = font_path
    
    def _get_terminal_font_data(self) -> Optional[bytes]:
        """Get embedded terminal font data."""
        # This would contain base64 encoded font data
        # For demo purposes, returning None to use system fonts
        return None
    
    def _get_matrix_font_data(self) -> Optional[bytes]:
        """Get embedded Matrix-style font data."""
        # This would contain base64 encoded font data
        return None
    
    def _get_retro_font_data(self) -> Optional[bytes]:
        """Get embedded retro computer font data."""
        # This would contain base64 encoded font data
        return None
    
    def get_font(
        self,
        font_name: Optional[str] = None,
        size: int = 14,
        style: str = "regular"
    ) -> ImageFont.FreeTypeFont:
        """Get a font with fallback options."""
        
        # Check cache first
        cache_key = (font_name or "default", size)
        if cache_key in self.font_cache:
            return self.font_cache[cache_key]
        
        # Try to load requested font
        font = None
        
        if font_name and font_name in self.available_fonts:
            try:
                font = ImageFont.truetype(str(self.available_fonts[font_name]), size)
            except Exception as e:
                logger.warning(f"Failed to load font {font_name}: {e}")
        
        # Fallback chain
        if not font:
            fallback_fonts = [
                "FiraCode", "JetBrainsMono", "Monaco", "Menlo",
                "Consolas", "Courier New", "DejaVu Sans Mono"
            ]
            
            for fallback in fallback_fonts:
                if fallback in self.available_fonts:
                    try:
                        font = ImageFont.truetype(str(self.available_fonts[fallback]), size)
                        break
                    except:
                        continue
        
        # Ultimate fallback to default font
        if not font:
            font = ImageFont.load_default()
        
        # Cache the font
        self.font_cache[cache_key] = font
        
        return font
    
    def get_font_metrics(self, font: ImageFont.FreeTypeFont) -> Dict[str, int]:
        """Get font metrics for proper text layout."""
        # Create a temporary image to measure text
        img = Image.new('RGB', (100, 100))
        draw = ImageDraw.Draw(img)
        
        # Measure various characters
        metrics = {
            'height': 0,
            'width': 0,
            'ascent': 0,
            'descent': 0,
            'line_height': 0
        }
        
        # Measure a sample string
        sample = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        bbox = draw.textbbox((0, 0), sample, font=font)
        
        metrics['height'] = bbox[3] - bbox[1]
        metrics['width'] = (bbox[2] - bbox[0]) // len(sample)  # Average width
        
        # Measure specific characters for ascent/descent
        ascent_bbox = draw.textbbox((0, 0), "Ag", font=font)
        descent_bbox = draw.textbbox((0, 0), "gjpqy", font=font)
        
        metrics['ascent'] = ascent_bbox[3] - ascent_bbox[1]
        metrics['descent'] = descent_bbox[3] - ascent_bbox[3]
        metrics['line_height'] = int(metrics['height'] * 1.2)  # 120% line height
        
        return metrics
    
    def render_text_with_effects(
        self,
        text: str,
        font: ImageFont.FreeTypeFont,
        color: Tuple[int, int, int],
        effects: Optional[Dict[str, Any]] = None
    ) -> Image.Image:
        """Render text with special effects."""
        
        # Default effects
        if effects is None:
            effects = {}
        
        # Measure text
        img = Image.new('RGBA', (1, 1))
        draw = ImageDraw.Draw(img)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Add padding for effects
        padding = 20
        img_width = text_width + padding * 2
        img_height = text_height + padding * 2
        
        # Create image
        img = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Apply effects
        x, y = padding, padding
        
        if effects.get('shadow'):
            # Draw shadow
            shadow_offset = effects.get('shadow_offset', (2, 2))
            shadow_color = effects.get('shadow_color', (0, 0, 0, 128))
            draw.text(
                (x + shadow_offset[0], y + shadow_offset[1]),
                text, font=font, fill=shadow_color
            )
        
        if effects.get('outline'):
            # Draw outline
            outline_width = effects.get('outline_width', 2)
            outline_color = effects.get('outline_color', (0, 0, 0))
            
            for dx in range(-outline_width, outline_width + 1):
                for dy in range(-outline_width, outline_width + 1):
                    if dx != 0 or dy != 0:
                        draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
        
        if effects.get('glow'):
            # Draw glow effect
            glow_color = effects.get('glow_color', color)
            glow_radius = effects.get('glow_radius', 5)
            
            for radius in range(glow_radius, 0, -1):
                alpha = int(255 * (1 - radius / glow_radius) * 0.3)
                glow_img = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))
                glow_draw = ImageDraw.Draw(glow_img)
                
                for dx in range(-radius, radius + 1):
                    for dy in range(-radius, radius + 1):
                        if dx*dx + dy*dy <= radius*radius:
                            glow_draw.text(
                                (x + dx, y + dy),
                                text, font=font,
                                fill=(*glow_color, alpha)
                            )
                
                img = Image.alpha_composite(img, glow_img)
        
        # Draw main text
        draw.text((x, y), text, font=font, fill=(*color, 255))
        
        return img
    
    def create_ascii_art_font(self, text: str, font_size: int = 20) -> List[str]:
        """Convert text to ASCII art using custom font rendering."""
        
        # Get font
        font = self.get_font(size=font_size)
        
        # Render text to image
        img = Image.new('L', (1, 1))
        draw = ImageDraw.Draw(img)
        bbox = draw.textbbox((0, 0), text, font=font)
        
        width = bbox[2] - bbox[0] + 10
        height = bbox[3] - bbox[1] + 10
        
        img = Image.new('L', (width, height), 0)
        draw = ImageDraw.Draw(img)
        draw.text((5, 5), text, font=font, fill=255)
        
        # Convert to ASCII
        ascii_chars = " .:-=+*#%@"
        ascii_art = []
        
        for y in range(0, height, 2):  # Sample every 2 pixels for height
            line = ""
            for x in range(width):
                pixel = img.getpixel((x, y))
                char_idx = int(pixel / 255 * (len(ascii_chars) - 1))
                line += ascii_chars[char_idx]
            ascii_art.append(line.rstrip())
        
        return ascii_art
    
    def download_font(self, font_url: str, font_name: str) -> Optional[Path]:
        """Download and install a font from URL."""
        try:
            response = requests.get(font_url, timeout=30)
            response.raise_for_status()
            
            font_path = self.fonts_dir / f"{font_name}.ttf"
            with open(font_path, 'wb') as f:
                f.write(response.content)
            
            self.available_fonts[font_name] = font_path
            logger.info(f"Downloaded font: {font_name}")
            
            return font_path
            
        except Exception as e:
            logger.error(f"Failed to download font {font_name}: {e}")
            return None
    
    def list_available_fonts(self) -> List[str]:
        """List all available fonts."""
        return list(self.available_fonts.keys())
    
    def get_monospace_fonts(self) -> List[str]:
        """Get list of available monospace fonts."""
        monospace_keywords = [
            'mono', 'code', 'courier', 'consolas', 'terminal',
            'fixed', 'typewriter'
        ]
        
        monospace_fonts = []
        for font_name in self.available_fonts:
            if any(keyword in font_name.lower() for keyword in monospace_keywords):
                monospace_fonts.append(font_name)
        
        return monospace_fonts
    
    def clear_cache(self):
        """Clear font cache."""
        self.font_cache.clear()
        logger.info("Font cache cleared")