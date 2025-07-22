"""
ModelScope Text-to-Video integration for AI video generation.
Provides alternative video generation using ModelScope models.
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import cv2
import torch
from modelscope.pipelines import pipeline as ms_pipeline
from modelscope.utils.constant import Tasks
import imageio

from ..config import settings
from .ffmpeg_service import FFmpegService

logger = logging.getLogger(__name__)


class ModelScopeVideoService:
    """Service for generating videos using ModelScope Text-to-Video."""
    
    def __init__(self):
        self.ffmpeg = FFmpegService()
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.pipe = None
        self._initialized = False
        
    async def initialize(self):
        """Initialize the video generation pipeline."""
        if self._initialized:
            return
            
        try:
            logger.info(f"Initializing ModelScope Text-to-Video on {self.device}")
            
            # Load ModelScope text-to-video model
            self.pipe = ms_pipeline(
                Tasks.text_to_video_synthesis,
                model='damo/text-to-video-synthesis',
                device=self.device
            )
            
            self._initialized = True
            logger.info("ModelScope Text-to-Video initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ModelScope: {e}")
            self._initialized = False
    
    async def generate_scene_video(
        self,
        scene_description: str,
        duration: float = 3.0,
        style: str = "cinematic",
        resolution: Tuple[int, int] = (1024, 576),
        fps: int = 24
    ) -> str:
        """Generate a video for a scene using ModelScope."""
        
        # Initialize if not already done
        await self.initialize()
        
        if not self._initialized:
            # Fallback to procedural generation
            return await self._generate_procedural_video(
                scene_description, duration, style, resolution, fps
            )
        
        try:
            # Enhance prompt for better results
            enhanced_prompt = self._enhance_prompt(scene_description, style)
            
            # Generate video
            result = self.pipe({
                'text': enhanced_prompt,
                'num_frames': min(int(duration * fps), 32),  # ModelScope limit
            })
            
            # Save video
            output_path = tempfile.mktemp(suffix=".mp4")
            
            if 'video_path' in result:
                # Copy generated video
                import shutil
                shutil.copy(result['video_path'], output_path)
            else:
                # Save frames
                frames = result.get('frames', [])
                if frames:
                    imageio.mimsave(output_path, frames, fps=fps)
                else:
                    raise ValueError("No video or frames generated")
            
            # Apply style effects
            output_path = await self._apply_style_effects(output_path, style)
            
            # Extend duration if needed
            if duration * fps > 32:
                output_path = await self._extend_video_duration(
                    output_path, duration, fps
                )
            
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to generate video with ModelScope: {e}")
            return await self._generate_procedural_video(
                scene_description, duration, style, resolution, fps
            )
    
    def _enhance_prompt(self, description: str, style: str) -> str:
        """Enhance prompt for better ModelScope results."""
        
        style_enhancements = {
            "cinematic": "cinematic shot, movie quality, dramatic lighting, professional cinematography, 4K",
            "noir": "film noir style, black and white, high contrast, dramatic shadows, 1940s detective movie",
            "cyberpunk": "cyberpunk style, neon lights, futuristic city, blade runner aesthetic, rain",
            "apocalyptic": "post-apocalyptic scene, destroyed city, dark atmosphere, abandoned, desolate",
            "tech": "high technology, futuristic, clean design, holographic displays, sci-fi"
        }
        
        base_enhancement = style_enhancements.get(style, style_enhancements["cinematic"])
        
        # Add motion descriptors for better video generation
        motion_hints = "slow camera movement, smooth transitions, dynamic scene"
        
        return f"{description}, {base_enhancement}, {motion_hints}"
    
    async def _apply_style_effects(self, video_path: str, style: str) -> str:
        """Apply style-specific effects to the generated video."""
        
        output_path = tempfile.mktemp(suffix=".mp4")
        
        # Style-specific filter chains
        style_filters = {
            "cinematic": [
                "curves=preset=increase_contrast",
                "colorbalance=rs=-0.05:gs=0:bs=0.05",
                "unsharp=5:5:0.8:3:3:0.4"
            ],
            "noir": [
                "colorchannelmixer=.3:.4:.3:0:.3:.4:.3:0:.3:.4:.3",
                "curves=preset=strong_contrast",
                "noise=alls=10:allf=t"
            ],
            "cyberpunk": [
                "colorbalance=rs=0.1:gs=-0.1:bs=0.3",
                "chromashift=crh=-3:crv=3",
                "gblur=sigma=0.5"
            ],
            "apocalyptic": [
                "colorbalance=rs=0.2:gs=0.1:bs=-0.1",
                "curves=preset=darker",
                "noise=alls=15:allf=t"
            ],
            "tech": [
                "curves=preset=linear_contrast",
                "colorbalance=rs=-0.1:gs=0:bs=0.1",
                "sharpen=3:0.5"
            ]
        }
        
        filters = style_filters.get(style, style_filters["cinematic"])
        
        # Add common effects
        filters.extend([
            "vignette=PI/4:1.5",
            "format=yuv420p"
        ])
        
        filter_complex = ",".join(filters)
        
        cmd = [
            'ffmpeg', '-i', video_path,
            '-vf', filter_complex,
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '18',
            output_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            logger.error(f"Style effects failed: {stderr.decode()}")
            return video_path
        
        os.unlink(video_path)
        return output_path
    
    async def _extend_video_duration(
        self,
        video_path: str,
        target_duration: float,
        fps: int
    ) -> str:
        """Extend video duration using smart looping and interpolation."""
        
        output_path = tempfile.mktemp(suffix=".mp4")
        
        # Calculate loop count
        current_duration = 32 / fps  # ModelScope max frames
        loop_count = int(np.ceil(target_duration / current_duration))
        
        # Create seamless loop with crossfade
        filter_complex = f"""
        [0:v]split={loop_count}{"".join(f'[v{i}]' for i in range(loop_count))};
        {"".join(f'[v{i}]' for i in range(loop_count))}concat=n={loop_count}:v=1[extended];
        [extended]trim=duration={target_duration}[final]
        """
        
        cmd = [
            'ffmpeg', '-i', video_path,
            '-filter_complex', filter_complex,
            '-map', '[final]',
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '18',
            output_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            logger.error(f"Video extension failed: {stderr.decode()}")
            return video_path
        
        os.unlink(video_path)
        return output_path
    
    async def _generate_procedural_video(
        self,
        scene_description: str,
        duration: float,
        style: str,
        resolution: Tuple[int, int],
        fps: int
    ) -> str:
        """Generate high-quality procedural video as fallback."""
        
        logger.info("Using procedural video generation")
        
        # Create frames
        frames = []
        total_frames = int(duration * fps)
        width, height = resolution
        
        for frame_idx in range(total_frames):
            t = frame_idx / fps
            
            # Create frame based on scene
            if "rooftop" in scene_description.lower():
                frame = self._create_rooftop_frame(width, height, t, style)
            elif "server" in scene_description.lower():
                frame = self._create_server_frame(width, height, t, style)
            elif "message" in scene_description.lower():
                frame = self._create_message_frame(width, height, t, style)
            elif "control" in scene_description.lower():
                frame = self._create_control_frame(width, height, t, style)
            else:
                frame = self._create_generic_frame(width, height, t, style)
            
            frames.append(frame)
        
        # Save as video
        output_path = tempfile.mktemp(suffix=".mp4")
        
        # Convert PIL images to numpy arrays
        frames_array = [np.array(frame) for frame in frames]
        
        # Use imageio to save with proper codec
        imageio.mimsave(
            output_path,
            frames_array,
            fps=fps,
            quality=9,
            codec='libx264',
            pixelformat='yuv420p'
        )
        
        return output_path
    
    def _create_rooftop_frame(
        self,
        width: int,
        height: int,
        t: float,
        style: str
    ) -> Image.Image:
        """Create animated rooftop scene frame."""
        
        img = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(img)
        
        # Animated sky gradient
        sky_darkness = int(20 + 10 * np.sin(t / 10))
        for y in range(height):
            darkness = sky_darkness + int((y / height) * 30)
            draw.rectangle([(0, y), (width, y+1)], fill=(darkness, darkness, darkness+10))
        
        # Lightning flash occasionally
        if np.random.random() < 0.02:  # 2% chance per frame
            draw.rectangle([(0, 0), (width, height)], fill=(80, 80, 100))
        
        # City with animated lights
        building_count = 15
        for i in range(building_count):
            x = int(i * width / building_count)
            building_height = int(height * (0.4 + 0.4 * np.sin(i + t / 20)))
            building_width = width // 15
            
            # Building silhouette
            draw.rectangle(
                [(x, height - building_height), (x + building_width, height)],
                fill=(10, 10, 15)
            )
            
            # Animated windows
            window_rows = building_height // 25
            window_cols = building_width // 20
            for row in range(window_rows):
                for col in range(window_cols):
                    # Animate lights turning on/off
                    light_phase = np.sin(t * 2 + i + row * 0.5 + col * 0.3)
                    if light_phase > 0:
                        wx = x + col * 20 + 5
                        wy = height - building_height + row * 25 + 5
                        brightness = int(180 + 75 * light_phase)
                        color = (brightness, brightness - 20, brightness - 40)
                        draw.rectangle([(wx, wy), (wx+10, wy+15)], fill=color)
        
        # Animated rain
        rain_offset = int(t * 200) % height
        for i in range(300):
            x = np.random.randint(0, width)
            y = (np.random.randint(0, height) + rain_offset) % height
            draw.line([(x, y), (x-2, y+20)], fill=(150, 150, 170), width=1)
        
        # Apply style processing
        return self._apply_frame_style(img, style)
    
    def _create_server_frame(
        self,
        width: int,
        height: int,
        t: float,
        style: str
    ) -> Image.Image:
        """Create animated server room frame."""
        
        img = Image.new('RGB', (width, height), (5, 5, 10))
        draw = ImageDraw.Draw(img)
        
        # Animated perspective grid
        for i in range(0, width, 40):
            # Vertical lines with perspective
            x_top = width//2 + (i - width//2) * 0.5
            x_bottom = i
            draw.line([(x_top, height//3), (x_bottom, height)], fill=(20, 20, 30), width=1)
        
        for j in range(height//3, height, 30):
            # Horizontal lines with perspective
            y = j
            width_at_y = width * (0.5 + 0.5 * (y - height//3) / (height - height//3))
            x_start = (width - width_at_y) // 2
            x_end = x_start + width_at_y
            draw.line([(x_start, y), (x_end, y)], fill=(20, 20, 30), width=1)
        
        # Server racks with animated LEDs
        rack_positions = [width//5, width*2//5, width*3//5, width*4//5]
        
        for idx, rack_x in enumerate(rack_positions):
            # Rack cabinet
            rack_width = width // 8
            rack_height = height // 2
            rack_y = height // 3
            
            # 3D effect
            draw.polygon([
                (rack_x, rack_y),
                (rack_x + rack_width, rack_y - 10),
                (rack_x + rack_width, rack_y + rack_height - 10),
                (rack_x, rack_y + rack_height)
            ], fill=(25, 25, 30), outline=(40, 40, 45))
            
            # Front face
            draw.rectangle(
                [(rack_x - rack_width//2, rack_y), (rack_x + rack_width//2, rack_y + rack_height)],
                fill=(30, 30, 35),
                outline=(50, 50, 55)
            )
            
            # Animated LED matrix
            for row in range(15):
                for col in range(6):
                    led_x = rack_x - rack_width//2 + 10 + col * 15
                    led_y = rack_y + 20 + row * 25
                    
                    # Complex LED animation pattern
                    phase = np.sin(t * 3 + idx + row * 0.2) * np.cos(t * 2 + col * 0.3)
                    
                    if phase > 0.3:
                        # Green - normal
                        led_color = (0, int(150 + 105 * phase), 0)
                    elif phase > -0.2:
                        # Blue - data transfer
                        led_color = (0, int(100 + 100 * phase), int(200 + 55 * phase))
                    elif np.random.random() < 0.05:
                        # Red - alert
                        led_color = (255, 0, 0)
                    else:
                        # Orange - activity
                        led_color = (int(200 * abs(phase)), int(100 * abs(phase)), 0)
                    
                    # LED with glow
                    draw.ellipse([(led_x-2, led_y-2), (led_x+2, led_y+2)], fill=led_color)
        
        # Holographic displays
        holo_y = height // 10
        holo_height = height // 5
        
        # Left display
        self._draw_holographic_display(
            draw, width // 10, holo_y, width // 4, holo_height, t, "SYSTEM STATUS"
        )
        
        # Right display
        self._draw_holographic_display(
            draw, width * 6 // 10, holo_y, width // 4, holo_height, t, "NETWORK TRAFFIC"
        )
        
        return self._apply_frame_style(img, style)
    
    def _draw_holographic_display(
        self,
        draw: ImageDraw.Draw,
        x: int,
        y: int,
        width: int,
        height: int,
        t: float,
        title: str
    ):
        """Draw animated holographic display."""
        
        # Display frame
        draw.rectangle(
            [(x, y), (x + width, y + height)],
            fill=(10, 20, 30),
            outline=(0, 100, 200)
        )
        
        # Title
        draw.text((x + 10, y + 5), title, fill=(0, 200, 255))
        
        # Animated data visualization
        data_points = 20
        for i in range(data_points):
            px = x + 10 + i * (width - 20) / data_points
            value = np.sin(t * 2 + i * 0.5) * 0.5 + 0.5
            py = y + height - 10 - int(value * (height - 40))
            
            # Data point
            draw.ellipse([(px-2, py-2), (px+2, py+2)], fill=(0, 255, 200))
            
            # Connecting line
            if i > 0:
                prev_value = np.sin(t * 2 + (i-1) * 0.5) * 0.5 + 0.5
                prev_py = y + height - 10 - int(prev_value * (height - 40))
                prev_px = x + 10 + (i-1) * (width - 20) / data_points
                draw.line([(prev_px, prev_py), (px, py)], fill=(0, 150, 255), width=2)
        
        # Scanline effect
        scan_y = y + int((t * 100) % height)
        draw.line([(x, scan_y), (x + width, scan_y)], fill=(0, 255, 100), width=1)
    
    def _apply_frame_style(self, img: Image.Image, style: str) -> Image.Image:
        """Apply style-specific effects to frame."""
        
        # Convert to numpy for processing
        img_array = np.array(img)
        
        if style == "noir":
            # Black and white with high contrast
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)
            img_array = cv2.cvtColor(binary, cv2.COLOR_GRAY2RGB)
            
        elif style == "cyberpunk":
            # Neon color shift
            img_array[:, :, 0] = np.clip(img_array[:, :, 0] * 0.7, 0, 255)
            img_array[:, :, 2] = np.clip(img_array[:, :, 2] * 1.5, 0, 255)
            
        elif style == "apocalyptic":
            # Desaturated and dark
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            img_array = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
            img_array = (img_array * 0.7).astype(np.uint8)
            # Add sepia tone
            img_array[:, :, 0] = np.clip(img_array[:, :, 0] * 1.2, 0, 255)
            img_array[:, :, 1] = np.clip(img_array[:, :, 1] * 1.0, 0, 255)
            img_array[:, :, 2] = np.clip(img_array[:, :, 2] * 0.8, 0, 255)
        
        # Add grain to all styles
        noise = np.random.randint(-10, 10, img_array.shape)
        img_array = np.clip(img_array.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        
        return Image.fromarray(img_array)