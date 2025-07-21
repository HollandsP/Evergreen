"""
Terminal Compositor Module

Composites terminal overlays with alpha channel support for video editing.
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
from typing import List, Tuple, Optional, Union
import cv2
from enum import Enum


class BlendMode(Enum):
    """Blend modes for compositing"""
    NORMAL = "normal"
    MULTIPLY = "multiply"
    SCREEN = "screen"
    OVERLAY = "overlay"
    ADD = "add"
    SUBTRACT = "subtract"
    DIFFERENCE = "difference"
    SOFT_LIGHT = "soft_light"
    HARD_LIGHT = "hard_light"
    COLOR_DODGE = "color_dodge"
    COLOR_BURN = "color_burn"


class TerminalCompositor:
    """Composites terminal renders with backgrounds and effects"""
    
    def __init__(self):
        """Initialize terminal compositor"""
        self.layers: List[Tuple[Image.Image, float, BlendMode]] = []
        self.background: Optional[Image.Image] = None
    
    def set_background(self, background: Union[Image.Image, Tuple[int, ...], str]):
        """
        Set background for composition
        
        Args:
            background: PIL Image, color tuple, or image file path
        """
        if isinstance(background, str):
            self.background = Image.open(background)
        elif isinstance(background, tuple):
            # Create solid color background
            if not hasattr(self, '_size'):
                self._size = (800, 600)  # Default size
            self.background = Image.new('RGBA', self._size, background)
        else:
            self.background = background
        
        if self.background:
            self._size = self.background.size
    
    def add_layer(self, image: Image.Image, opacity: float = 1.0, 
                  blend_mode: BlendMode = BlendMode.NORMAL):
        """
        Add a layer to the composition
        
        Args:
            image: Layer image
            opacity: Layer opacity (0-1)
            blend_mode: Blend mode for this layer
        """
        self.layers.append((image, opacity, blend_mode))
    
    def clear_layers(self):
        """Clear all layers"""
        self.layers.clear()
    
    def composite(self) -> Image.Image:
        """
        Composite all layers
        
        Returns:
            Composited image
        """
        if not self.background and not self.layers:
            return Image.new('RGBA', (800, 600), (0, 0, 0, 0))
        
        # Start with background or first layer
        if self.background:
            result = self.background.copy()
        else:
            result, _, _ = self.layers[0]
            result = result.copy()
            start_idx = 1
        
        # Composite each layer
        for i in range(start_idx if not self.background else 0, len(self.layers)):
            layer, opacity, blend_mode = self.layers[i]
            result = self._blend_layer(result, layer, opacity, blend_mode)
        
        return result
    
    def _blend_layer(self, base: Image.Image, layer: Image.Image, 
                     opacity: float, blend_mode: BlendMode) -> Image.Image:
        """Blend a layer onto the base image"""
        # Ensure both images are RGBA
        if base.mode != 'RGBA':
            base = base.convert('RGBA')
        if layer.mode != 'RGBA':
            layer = layer.convert('RGBA')
        
        # Resize layer if needed
        if layer.size != base.size:
            layer = layer.resize(base.size, Image.Resampling.LANCZOS)
        
        # Apply opacity
        if opacity < 1.0:
            layer = self._apply_opacity(layer, opacity)
        
        # Apply blend mode
        if blend_mode == BlendMode.NORMAL:
            return Image.alpha_composite(base, layer)
        else:
            return self._apply_blend_mode(base, layer, blend_mode)
    
    def _apply_opacity(self, image: Image.Image, opacity: float) -> Image.Image:
        """Apply opacity to an image"""
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # Multiply alpha channel by opacity
        r, g, b, a = image.split()
        a = a.point(lambda x: int(x * opacity))
        return Image.merge('RGBA', (r, g, b, a))
    
    def _apply_blend_mode(self, base: Image.Image, layer: Image.Image, 
                          mode: BlendMode) -> Image.Image:
        """Apply blend mode between two images"""
        # Convert to numpy arrays for advanced blending
        base_array = np.array(base).astype(float) / 255.0
        layer_array = np.array(layer).astype(float) / 255.0
        
        # Extract alpha channels
        base_alpha = base_array[:, :, 3]
        layer_alpha = layer_array[:, :, 3]
        
        # Blend RGB channels based on mode
        if mode == BlendMode.MULTIPLY:
            blended = base_array[:, :, :3] * layer_array[:, :, :3]
        
        elif mode == BlendMode.SCREEN:
            blended = 1 - (1 - base_array[:, :, :3]) * (1 - layer_array[:, :, :3])
        
        elif mode == BlendMode.OVERLAY:
            blended = np.where(
                base_array[:, :, :3] < 0.5,
                2 * base_array[:, :, :3] * layer_array[:, :, :3],
                1 - 2 * (1 - base_array[:, :, :3]) * (1 - layer_array[:, :, :3])
            )
        
        elif mode == BlendMode.ADD:
            blended = np.clip(base_array[:, :, :3] + layer_array[:, :, :3], 0, 1)
        
        elif mode == BlendMode.SUBTRACT:
            blended = np.clip(base_array[:, :, :3] - layer_array[:, :, :3], 0, 1)
        
        elif mode == BlendMode.DIFFERENCE:
            blended = np.abs(base_array[:, :, :3] - layer_array[:, :, :3])
        
        elif mode == BlendMode.SOFT_LIGHT:
            blended = np.where(
                layer_array[:, :, :3] < 0.5,
                base_array[:, :, :3] * (1 + 2 * layer_array[:, :, :3] - 1),
                base_array[:, :, :3] + (2 * layer_array[:, :, :3] - 1) * 
                (np.sqrt(base_array[:, :, :3]) - base_array[:, :, :3])
            )
        
        elif mode == BlendMode.HARD_LIGHT:
            blended = np.where(
                layer_array[:, :, :3] < 0.5,
                2 * base_array[:, :, :3] * layer_array[:, :, :3],
                1 - 2 * (1 - base_array[:, :, :3]) * (1 - layer_array[:, :, :3])
            )
        
        elif mode == BlendMode.COLOR_DODGE:
            blended = np.where(
                layer_array[:, :, :3] < 1,
                np.minimum(1, base_array[:, :, :3] / (1 - layer_array[:, :, :3] + 1e-10)),
                1
            )
        
        elif mode == BlendMode.COLOR_BURN:
            blended = np.where(
                layer_array[:, :, :3] > 0,
                1 - np.minimum(1, (1 - base_array[:, :, :3]) / (layer_array[:, :, :3] + 1e-10)),
                0
            )
        
        else:
            blended = layer_array[:, :, :3]
        
        # Composite with alpha
        alpha_composite = layer_alpha + base_alpha * (1 - layer_alpha)
        
        # Avoid division by zero
        alpha_composite = np.where(alpha_composite > 0, alpha_composite, 1)
        
        result_rgb = (blended * layer_alpha[:, :, np.newaxis] + 
                     base_array[:, :, :3] * base_alpha[:, :, np.newaxis] * 
                     (1 - layer_alpha[:, :, np.newaxis])) / alpha_composite[:, :, np.newaxis]
        
        # Combine RGB and alpha
        result = np.dstack((result_rgb, alpha_composite))
        
        # Convert back to image
        result = (result * 255).astype(np.uint8)
        return Image.fromarray(result)
    
    def create_vignette(self, size: Tuple[int, int], intensity: float = 0.5,
                       color: Tuple[int, ...] = (0, 0, 0, 255)) -> Image.Image:
        """
        Create a vignette overlay
        
        Args:
            size: Image size
            intensity: Vignette intensity (0-1)
            color: Vignette color
        
        Returns:
            Vignette overlay image
        """
        vignette = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(vignette)
        
        # Create radial gradient
        center_x, center_y = size[0] // 2, size[1] // 2
        max_radius = int(np.sqrt(center_x**2 + center_y**2))
        
        for radius in range(max_radius, 0, -5):
            alpha = int(255 * intensity * (1 - radius / max_radius)**2)
            color_with_alpha = color[:3] + (alpha,)
            draw.ellipse(
                [center_x - radius, center_y - radius,
                 center_x + radius, center_y + radius],
                fill=color_with_alpha
            )
        
        return vignette
    
    def create_scanline_overlay(self, size: Tuple[int, int], 
                               line_spacing: int = 3,
                               line_opacity: float = 0.1) -> Image.Image:
        """
        Create scanline overlay
        
        Args:
            size: Image size
            line_spacing: Spacing between scanlines
            line_opacity: Opacity of scanlines
        
        Returns:
            Scanline overlay image
        """
        overlay = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        alpha = int(255 * line_opacity)
        
        for y in range(0, size[1], line_spacing):
            draw.line([(0, y), (size[0], y)], fill=(0, 0, 0, alpha))
        
        return overlay
    
    def create_noise_overlay(self, size: Tuple[int, int], 
                            intensity: float = 0.1) -> Image.Image:
        """
        Create noise overlay
        
        Args:
            size: Image size
            intensity: Noise intensity (0-1)
        
        Returns:
            Noise overlay image
        """
        # Create noise array
        noise = np.random.randint(0, int(255 * intensity), (*size[::-1], 1))
        noise = np.repeat(noise, 4, axis=2)
        noise[:, :, 3] = int(255 * intensity)  # Set alpha
        
        return Image.fromarray(noise.astype(np.uint8))
    
    def create_glow_overlay(self, terminal_image: Image.Image,
                           glow_color: Tuple[int, ...] = (0, 255, 0, 255),
                           intensity: float = 0.5) -> Image.Image:
        """
        Create glow overlay from terminal content
        
        Args:
            terminal_image: Terminal render
            glow_color: Glow color
            intensity: Glow intensity
        
        Returns:
            Glow overlay image
        """
        # Extract bright areas
        if terminal_image.mode != 'RGBA':
            terminal_image = terminal_image.convert('RGBA')
        
        # Convert to grayscale to find bright areas
        gray = terminal_image.convert('L')
        
        # Threshold to get only bright pixels
        threshold = 128
        mask = gray.point(lambda x: 255 if x > threshold else 0)
        
        # Create colored glow
        glow = Image.new('RGBA', terminal_image.size, (0, 0, 0, 0))
        glow.paste(glow_color, mask=mask)
        
        # Apply Gaussian blur
        glow = glow.filter(ImageFilter.GaussianBlur(radius=5))
        
        # Apply intensity
        return self._apply_opacity(glow, intensity)
    
    def export_with_alpha(self, output_path: str):
        """
        Export composition with alpha channel preserved
        
        Args:
            output_path: Output file path (PNG recommended)
        """
        result = self.composite()
        
        # Ensure RGBA mode
        if result.mode != 'RGBA':
            result = result.convert('RGBA')
        
        # Save with alpha
        result.save(output_path, 'PNG')
    
    def export_video_sequence(self, frames: List[Image.Image], 
                            output_path: str, fps: int = 30,
                            with_alpha: bool = False):
        """
        Export frame sequence as video
        
        Args:
            frames: List of frames
            output_path: Output video path
            fps: Frames per second
            with_alpha: Preserve alpha channel (requires appropriate codec)
        """
        if not frames:
            return
        
        height, width = frames[0].size[::-1]
        
        # Choose codec
        if with_alpha:
            fourcc = cv2.VideoWriter_fourcc(*'FFV1')
        else:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        
        writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        for frame in frames:
            if with_alpha and frame.mode == 'RGBA':
                cv_frame = cv2.cvtColor(np.array(frame), cv2.COLOR_RGBA2BGRA)
            else:
                if frame.mode == 'RGBA':
                    frame = frame.convert('RGB')
                cv_frame = cv2.cvtColor(np.array(frame), cv2.COLOR_RGB2BGR)
            
            writer.write(cv_frame)
        
        writer.release()