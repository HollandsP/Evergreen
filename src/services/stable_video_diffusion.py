"""
Stable Video Diffusion integration for AI video generation.
Provides high-quality video generation using open-source models.
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
from diffusers import StableVideoDiffusionPipeline, DPMSolverMultistepScheduler
from diffusers.utils import export_to_video
import imageio
from transformers import pipeline

from ..config import settings
from .ffmpeg_service import FFmpegService

logger = logging.getLogger(__name__)


class StableVideoDiffusionService:
    """Service for generating videos using Stable Video Diffusion."""
    
    def __init__(self):
        self.ffmpeg = FFmpegService()
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.pipe = None
        self.image_generator = None
        self._initialized = False
        
    async def initialize(self):
        """Initialize the video generation pipeline."""
        if self._initialized:
            return
            
        try:
            logger.info(f"Initializing Stable Video Diffusion on {self.device}")
            
            # Load Stable Video Diffusion model
            self.pipe = StableVideoDiffusionPipeline.from_pretrained(
                "stabilityai/stable-video-diffusion-img2vid",
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                variant="fp16" if self.device == "cuda" else None
            )
            self.pipe = self.pipe.to(self.device)
            
            # Optimize scheduler for faster generation
            self.pipe.scheduler = DPMSolverMultistepScheduler.from_config(
                self.pipe.scheduler.config
            )
            
            # Initialize image generator for creating initial frames
            self.image_generator = pipeline(
                "text-to-image",
                model="stabilityai/stable-diffusion-xl-base-1.0",
                device=0 if self.device == "cuda" else -1
            )
            
            # Enable memory efficient attention if available
            if hasattr(self.pipe, "enable_model_cpu_offload"):
                self.pipe.enable_model_cpu_offload()
            
            self._initialized = True
            logger.info("Stable Video Diffusion initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Stable Video Diffusion: {e}")
            # Fallback to enhanced cinematic mode
            self._initialized = False
    
    async def generate_scene_video(
        self,
        scene_description: str,
        duration: float = 3.0,
        style: str = "cinematic",
        resolution: Tuple[int, int] = (1024, 576),
        fps: int = 24
    ) -> str:
        """Generate a video for a scene using AI."""
        
        # Initialize if not already done
        await self.initialize()
        
        if not self._initialized:
            # Fallback to ultra-enhanced cinematic mode
            return await self._generate_ultra_cinematic_fallback(
                scene_description, duration, style, resolution, fps
            )
        
        try:
            # Generate initial frame from text description
            initial_frame = await self._generate_initial_frame(
                scene_description, style, resolution
            )
            
            # Generate video from initial frame
            num_frames = int(duration * fps)
            
            # Run generation
            frames = self.pipe(
                initial_frame,
                decode_chunk_size=8,
                num_frames=min(num_frames, 25),  # SVD limit
                motion_bucket_id=127,  # Higher motion
                noise_aug_strength=0.02,
                generator=torch.manual_seed(42)
            ).frames[0]
            
            # Save frames as video
            output_path = tempfile.mktemp(suffix=".mp4")
            export_to_video(frames, output_path, fps=fps)
            
            # If we need more frames, interpolate
            if num_frames > 25:
                output_path = await self._interpolate_frames(
                    output_path, num_frames, fps
                )
            
            # Apply post-processing effects
            output_path = await self._apply_cinematic_effects(
                output_path, style
            )
            
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to generate video with SVD: {e}")
            # Fallback to ultra-enhanced cinematic mode
            return await self._generate_ultra_cinematic_fallback(
                scene_description, duration, style, resolution, fps
            )
    
    async def _generate_initial_frame(
        self,
        description: str,
        style: str,
        resolution: Tuple[int, int]
    ) -> Image.Image:
        """Generate initial frame using text-to-image."""
        
        # Enhance prompt with style modifiers
        style_prompts = {
            "cinematic": "cinematic lighting, dramatic atmosphere, film grain, professional cinematography",
            "noir": "film noir style, high contrast black and white, dramatic shadows, venetian blinds",
            "cyberpunk": "cyberpunk aesthetic, neon lights, rain, futuristic city, blade runner style",
            "apocalyptic": "post-apocalyptic atmosphere, destroyed buildings, dark sky, abandoned",
            "tech": "high tech environment, holographic displays, clean modern design, sci-fi"
        }
        
        enhanced_prompt = f"{description}, {style_prompts.get(style, style_prompts['cinematic'])}"
        enhanced_prompt += ", highly detailed, 8k, photorealistic, professional"
        
        if self.image_generator:
            result = self.image_generator(
                enhanced_prompt,
                num_inference_steps=30,
                guidance_scale=7.5
            )
            image = result[0]["image"]
            return image.resize(resolution, Image.Resampling.LANCZOS)
        else:
            # Create high-quality procedural initial frame
            return self._create_procedural_frame(description, style, resolution)
    
    def _create_procedural_frame(
        self,
        description: str,
        style: str,
        resolution: Tuple[int, int]
    ) -> Image.Image:
        """Create a high-quality procedural frame when AI generation unavailable."""
        
        width, height = resolution
        img = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(img)
        
        # Scene-specific generation
        if "rooftop" in description.lower():
            # Atmospheric rooftop scene
            self._draw_rooftop_scene(draw, width, height, style)
        elif "server" in description.lower():
            # High-tech server room
            self._draw_server_room(draw, width, height, style)
        elif "message" in description.lower() or "concrete" in description.lower():
            # Concrete message wall
            self._draw_concrete_message(draw, width, height, style)
        elif "control" in description.lower():
            # Control room scene
            self._draw_control_room(draw, width, height, style)
        else:
            # Generic cinematic scene
            self._draw_generic_cinematic(draw, width, height, style)
        
        # Apply post-processing
        img = self._apply_image_effects(img, style)
        
        return img
    
    def _draw_rooftop_scene(self, draw: ImageDraw.Draw, width: int, height: int, style: str):
        """Draw atmospheric rooftop scene with city lights."""
        
        # Sky gradient
        for y in range(height):
            darkness = int(20 + (y / height) * 30)
            draw.rectangle([(0, y), (width, y+1)], fill=(darkness, darkness, darkness+10))
        
        # City skyline
        building_count = 15
        for i in range(building_count):
            x = int(i * width / building_count)
            building_height = np.random.randint(height//3, int(height * 0.8))
            building_width = np.random.randint(width//20, width//10)
            
            # Building
            draw.rectangle(
                [(x, height - building_height), (x + building_width, height)],
                fill=(10, 10, 15)
            )
            
            # Windows with lights
            window_rows = building_height // 20
            window_cols = building_width // 15
            for row in range(window_rows):
                for col in range(window_cols):
                    if np.random.random() > 0.3:  # 70% lights on
                        wx = x + col * 15 + 5
                        wy = height - building_height + row * 20 + 5
                        brightness = np.random.randint(180, 255)
                        color = (brightness, brightness - 20, brightness - 40)
                        draw.rectangle([(wx, wy), (wx+8, wy+12)], fill=color)
        
        # Rain effect
        if "rain" in style.lower() or style == "noir":
            for _ in range(500):
                x = np.random.randint(0, width)
                y = np.random.randint(0, height)
                length = np.random.randint(10, 30)
                draw.line([(x, y), (x-2, y+length)], fill=(150, 150, 170, 100), width=1)
        
        # Fog/atmosphere
        for i in range(3):
            y_pos = height - np.random.randint(50, 200)
            draw.ellipse(
                [(0, y_pos), (width, y_pos + 100)],
                fill=(40, 40, 50, 30)
            )
    
    def _draw_server_room(self, draw: ImageDraw.Draw, width: int, height: int, style: str):
        """Draw high-tech server room with LED patterns."""
        
        # Dark background
        draw.rectangle([(0, 0), (width, height)], fill=(5, 5, 10))
        
        # Server racks
        rack_width = width // 6
        rack_spacing = width // 5
        
        for i in range(4):
            x = rack_spacing * (i + 1) - rack_width // 2
            
            # Rack frame
            draw.rectangle(
                [(x, height//10), (x + rack_width, height - height//10)],
                fill=(20, 20, 25),
                outline=(40, 40, 45),
                width=2
            )
            
            # Server units with blinking LEDs
            units = 20
            for unit in range(units):
                y = height//10 + unit * (height * 0.8 / units)
                unit_height = (height * 0.8 / units) - 2
                
                # Server unit
                draw.rectangle(
                    [(x + 5, y), (x + rack_width - 5, y + unit_height)],
                    fill=(30, 30, 35),
                    outline=(50, 50, 55)
                )
                
                # LED indicators
                for led in range(8):
                    led_x = x + 10 + led * 15
                    led_y = y + unit_height // 2
                    
                    if np.random.random() > 0.2:
                        # Active LED
                        color_choices = [
                            (0, 255, 0),    # Green
                            (0, 200, 255),  # Cyan
                            (255, 100, 0),  # Orange
                            (255, 0, 0)     # Red (rare)
                        ]
                        weights = [0.6, 0.3, 0.08, 0.02]
                        color = np.random.choice(len(color_choices), p=weights)
                        led_color = color_choices[color]
                        
                        # LED glow effect
                        for glow in range(3):
                            glow_size = 3 + glow * 2
                            glow_alpha = 100 - glow * 30
                            draw.ellipse(
                                [(led_x - glow_size, led_y - glow_size),
                                 (led_x + glow_size, led_y + glow_size)],
                                fill=(*led_color, glow_alpha)
                            )
        
        # Floor reflection
        for i in range(height - height//10, height):
            alpha = int(50 * (1 - (i - (height - height//10)) / (height//10)))
            draw.rectangle([(0, i), (width, i+1)], fill=(20, 20, 30, alpha))
    
    def _apply_image_effects(self, img: Image.Image, style: str) -> Image.Image:
        """Apply cinematic post-processing effects to image."""
        
        # Convert to numpy for advanced processing
        img_array = np.array(img)
        
        # Style-specific effects
        if style == "noir":
            # Convert to high-contrast black and white
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            # Increase contrast
            gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=-50)
            img_array = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
            
        elif style == "cyberpunk":
            # Add neon color grading
            img_array[:, :, 0] = np.clip(img_array[:, :, 0] * 0.7, 0, 255)  # Reduce red
            img_array[:, :, 2] = np.clip(img_array[:, :, 2] * 1.3, 0, 255)  # Boost blue
            
            # Add chromatic aberration
            shift = 3
            img_array[shift:, :, 0] = img_array[:-shift, :, 0]  # Shift red channel
            img_array[:, shift:, 2] = img_array[:, :-shift, 2]  # Shift blue channel
        
        # Film grain for all styles
        noise = np.random.normal(0, 5, img_array.shape)
        img_array = np.clip(img_array + noise, 0, 255).astype(np.uint8)
        
        # Vignette effect
        rows, cols = img_array.shape[:2]
        kernel_x = cv2.getGaussianKernel(cols, cols/2)
        kernel_y = cv2.getGaussianKernel(rows, rows/2)
        kernel = kernel_y * kernel_x.T
        mask = kernel / kernel.max()
        mask = np.stack([mask] * 3, axis=2)
        img_array = (img_array * mask).astype(np.uint8)
        
        return Image.fromarray(img_array)
    
    async def _interpolate_frames(
        self,
        video_path: str,
        target_frames: int,
        fps: int
    ) -> str:
        """Interpolate frames to achieve target duration."""
        
        # Use advanced frame interpolation
        output_path = tempfile.mktemp(suffix=".mp4")
        
        filter_complex = (
            f"minterpolate=fps={fps}:mi_mode=mci:mc_mode=aobmc:"
            f"me_mode=bidir:vsbmc=1:scd=none"
        )
        
        cmd = [
            'ffmpeg', '-i', video_path,
            '-filter_complex', filter_complex,
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '18',
            '-pix_fmt', 'yuv420p',
            output_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            logger.error(f"Frame interpolation failed: {stderr.decode()}")
            return video_path
        
        os.unlink(video_path)
        return output_path
    
    async def _apply_cinematic_effects(self, video_path: str, style: str) -> str:
        """Apply cinematic post-processing effects to video."""
        
        output_path = tempfile.mktemp(suffix=".mp4")
        
        # Build filter chain based on style
        filters = []
        
        # Base cinematic look
        filters.append("curves=preset=increase_contrast")
        
        if style == "noir":
            filters.extend([
                "colorchannelmixer=.3:.4:.3:0:.3:.4:.3:0:.3:.4:.3",  # B&W
                "curves=preset=darker",
                "unsharp=5:5:1.5:5:5:0.0"  # Sharp contrast
            ])
        elif style == "cyberpunk":
            filters.extend([
                "colorbalance=rs=0.1:gs=-0.1:bs=0.2",  # Cyan/magenta tint
                "chromashift=crh=-5:crv=5:cbh=5:cbv=-5",  # Chromatic aberration
                "gblur=sigma=0.5"  # Slight bloom
            ])
        elif style == "apocalyptic":
            filters.extend([
                "colorbalance=rs=0.2:gs=0.1:bs=-0.1",  # Warm/desaturated
                "curves=preset=darker",
                "noise=alls=10:allf=t"  # Grunge
            ])
        
        # Film grain and vignette for all
        filters.extend([
            "noise=alls=5:allf=t+u",
            "vignette=PI/4:1.5"
        ])
        
        # Add letterbox for cinematic aspect
        filters.append("pad=iw:iw*9/16:0:(oh-ih)/2:black")
        
        filter_complex = ",".join(filters)
        
        cmd = [
            'ffmpeg', '-i', video_path,
            '-vf', filter_complex,
            '-c:v', 'libx264',
            '-preset', 'slow',
            '-crf', '18',
            '-c:a', 'copy',
            output_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            logger.error(f"Cinematic effects failed: {stderr.decode()}")
            return video_path
        
        os.unlink(video_path)
        return output_path
    
    async def _generate_ultra_cinematic_fallback(
        self,
        scene_description: str,
        duration: float,
        style: str,
        resolution: Tuple[int, int],
        fps: int
    ) -> str:
        """Generate ultra-high quality cinematic video as fallback."""
        
        logger.info("Using ultra-cinematic fallback generation")
        
        # Create high-quality animated scene
        output_path = tempfile.mktemp(suffix=".mp4")
        width, height = resolution
        
        # Scene-specific ultra-quality generation
        if "rooftop" in scene_description.lower():
            filter_complex = self._create_ultra_rooftop_scene(width, height, duration, fps)
        elif "server" in scene_description.lower():
            filter_complex = self._create_ultra_server_scene(width, height, duration, fps)
        elif "message" in scene_description.lower():
            filter_complex = self._create_ultra_message_scene(width, height, duration, fps)
        elif "control" in scene_description.lower():
            filter_complex = self._create_ultra_control_scene(width, height, duration, fps)
        else:
            filter_complex = self._create_ultra_generic_scene(width, height, duration, fps, style)
        
        # Apply style-specific color grading
        filter_complex += self._get_style_filters(style)
        
        cmd = [
            'ffmpeg',
            '-f', 'lavfi',
            '-i', f'nullsrc=s={width}x{height}:d={duration}:r={fps}',
            '-filter_complex', filter_complex,
            '-c:v', 'libx264',
            '-preset', 'slow',
            '-crf', '17',  # Higher quality
            '-pix_fmt', 'yuv420p',
            output_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise RuntimeError(f"Ultra-cinematic generation failed: {stderr.decode()}")
        
        return output_path
    
    def _create_ultra_rooftop_scene(self, width: int, height: int, duration: float, fps: int) -> str:
        """Create ultra-quality animated rooftop scene."""
        
        return f"""
        [0]
        # Animated sky with moving clouds
        gradients=n=2:s={width}x{height}:c0=0x0a0a14:c1=0x1a1a2e:x0=0:y0=0:x1=0:y1={height}[sky];
        
        # Animated clouds layer 1
        nullsrc=s={width}x{height}:d={duration}:r={fps},
        lutrgb=r='sin(2*PI*X/{width}+T)*50+50':g='sin(2*PI*X/{width}+T)*50+50':b='sin(2*PI*X/{width}+T)*60+60',
        scale={width*2}:{height//3},
        scroll=h='sin(T/5)*20':v=0,
        crop={width}:{height//3},
        colorkey=0x323246:0.3:0.2[clouds1];
        
        # Animated clouds layer 2
        nullsrc=s={width}x{height}:d={duration}:r={fps},
        lutrgb=r='sin(2*PI*X/{width}+T*1.5)*40+40':g='sin(2*PI*X/{width}+T*1.5)*40+40':b='sin(2*PI*X/{width}+T*1.5)*50+50',
        scale={width*2}:{height//4},
        scroll=h='sin(T/7)*30':v=0,
        crop={width}:{height//4},
        colorkey=0x282838:0.3:0.2[clouds2];
        
        # City skyline with animated lights
        nullsrc=s={width}x{height}:d={duration}:r={fps}[city];
        [city]
        drawbox=x=0:y={height*2//3}:w={width//10}:h={height//3}:c=0x0a0a0f:t=fill,
        drawbox=x={width//8}:y={height*3//5}:w={width//12}:h={height*2//5}:c=0x0c0c11:t=fill,
        drawbox=x={width//5}:y={height*7//10}:w={width//10}:h={height*3//10}:c=0x0a0a0f:t=fill,
        drawbox=x={width*3//10}:y={height*3//5}:w={width//15}:h={height*2//5}:c=0x0e0e13:t=fill,
        drawbox=x={width*2//5}:y={height*2//3}:w={width//10}:h={height//3}:c=0x0a0a0f:t=fill,
        drawbox=x={width//2}:y={height*3//5}:w={width//8}:h={height*2//5}:c=0x0c0c11:t=fill,
        drawbox=x={width*3//5}:y={height*7//10}:w={width//10}:h={height*3//10}:c=0x0a0a0f:t=fill,
        drawbox=x={width*7//10}:y={height*2//3}:w={width//12}:h={height//3}:c=0x0e0e13:t=fill,
        drawbox=x={width*4//5}:y={height*3//5}:w={width//10}:h={height*2//5}:c=0x0c0c11:t=fill,
        drawbox=x={width*9//10}:y={height*7//10}:w={width//10}:h={height*3//10}:c=0x0a0a0f:t=fill
        [buildings];
        
        # Animated window lights
        [buildings]
        nullsrc=s={width}x{height}:d={duration}:r={fps},
        lutrgb=r='st(1,floor(X/20)*20);st(2,floor(Y/25)*25);if(mod(ld(1)+ld(2)+T*2,7),255*random(ld(1)*ld(2)),0)':
        g='st(1,floor(X/20)*20);st(2,floor(Y/25)*25);if(mod(ld(1)+ld(2)+T*2,7),240*random(ld(1)*ld(2)),0)':
        b='st(1,floor(X/20)*20);st(2,floor(Y/25)*25);if(mod(ld(1)+ld(2)+T*2,7),180*random(ld(1)*ld(2)),0)'[lights];
        [buildings][lights]blend=multiply[city_lit];
        
        # Rain effect
        nullsrc=s={width}x{height}:d={duration}:r={fps},
        noise=alls=20:allf=t,
        lutrgb=r='if(gt(val,250),255,0)':g='if(gt(val,250),255,0)':b='if(gt(val,250),255,0)',
        scale={width}:{height*2},
        scroll=v='200+sin(T)*20':h='50+cos(T)*10',
        crop={width}:{height}[rain];
        
        # Composite all layers
        [sky][clouds1]overlay=x=0:y=0[sky_clouds1];
        [sky_clouds1][clouds2]overlay=x=0:y={height//10}[sky_complete];
        [sky_complete][city_lit]overlay[scene];
        [scene][rain]blend=screen:all_opacity=0.3[final];
        
        # Add atmospheric fog
        [final]
        gradients=n=1:s={width}x{height//3}:c0=0x000000:c1=0x303040:x0=0:y0=0:x1=0:y1={height//3}[fog];
        [final][fog]overlay=x=0:y={height*2//3}:eof_action=repeat[with_fog];
        
        # Final atmospheric adjustments
        [with_fog]
        """
    
    def _create_ultra_server_scene(self, width: int, height: int, duration: float, fps: int) -> str:
        """Create ultra-quality animated server room scene."""
        
        return f"""
        [0]
        # Dark tech background
        gradients=n=2:s={width}x{height}:c0=0x050510:c1=0x0a0a1a:x0={width//2}:y0={height//2}:x1=0:y1=0[bg];
        
        # Animated grid floor
        nullsrc=s={width}x{height}:d={duration}:r={fps},
        lutrgb=r='if(mod(X,30)*mod(Y,30),0,30)':g='if(mod(X,30)*mod(Y,30),0,30)':b='if(mod(X,30)*mod(Y,30),0,40)',
        perspective=x0=0:y0={height}:x1={width}:y1={height}:x2={width}:y2={height*3//4}:x3=0:y3={height*3//4}[grid];
        
        # Server racks with depth
        nullsrc=s={width}x{height}:d={duration}:r={fps}[racks];
        
        # Rack 1 - Left
        [racks]
        drawbox=x={width//6}:y={height//5}:w={width//8}:h={height*3//5}:c=0x1a1a25:t=fill,
        drawbox=x={width//6+5}:y={height//5+5}:w={width//8-10}:h={height*3//5-10}:c=0x252530:t=fill[rack1];
        
        # Rack 2 - Center Left
        [rack1]
        drawbox=x={width*2//6}:y={height//5}:w={width//8}:h={height*3//5}:c=0x1a1a25:t=fill,
        drawbox=x={width*2//6+5}:y={height//5+5}:w={width//8-10}:h={height*3//5-10}:c=0x252530:t=fill[rack2];
        
        # Rack 3 - Center Right
        [rack2]
        drawbox=x={width*3//6}:y={height//5}:w={width//8}:h={height*3//5}:c=0x1a1a25:t=fill,
        drawbox=x={width*3//6+5}:y={height//5+5}:w={width//8-10}:h={height*3//5-10}:c=0x252530:t=fill[rack3];
        
        # Rack 4 - Right
        [rack3]
        drawbox=x={width*4//6}:y={height//5}:w={width//8}:h={height*3//5}:c=0x1a1a25:t=fill,
        drawbox=x={width*4//6+5}:y={height//5+5}:w={width//8-10}:h={height*3//5-10}:c=0x252530:t=fill[racks_done];
        
        # Animated LED patterns
        nullsrc=s={width}x{height}:d={duration}:r={fps},
        lutrgb=
        r='st(1,floor(X/10)*10);st(2,floor(Y/15)*15);st(3,sin(ld(1)/50+T*3)*sin(ld(2)/50+T*2)+T);if(mod(ld(3),3),0,255*abs(sin(ld(3))))'
        g='st(1,floor(X/10)*10);st(2,floor(Y/15)*15);st(3,sin(ld(1)/50+T*3)*sin(ld(2)/50+T*2)+T);if(mod(ld(3),3),255*abs(sin(ld(3)*1.3)),0)'
        b='st(1,floor(X/10)*10);st(2,floor(Y/15)*15);st(3,sin(ld(1)/50+T*3)*sin(ld(2)/50+T*2)+T);if(mod(ld(3),3),255*abs(sin(ld(3)*0.7)),255*abs(sin(ld(3)*1.5)))'
        [leds];
        
        # Holographic displays
        nullsrc=s={width//4}x{height//4}:d={duration}:r={fps},
        lutrgb=r='100*sin(2*PI*Y/{height//4}+T*5)+155':g='255*sin(2*PI*Y/{height//4}+T*5)':b='200*sin(2*PI*Y/{height//4}+T*5)+55',
        boxblur=5:1[holo];
        
        # Composite scene
        [bg][grid]overlay=y={height*3//4}:all_opacity=0.5[bg_grid];
        [bg_grid][racks_done]overlay[with_racks];
        [with_racks][leds]blend=screen:all_opacity=0.7[with_leds];
        [with_leds][holo]overlay=x={width//10}:y={height//10}:all_opacity=0.4[scene1];
        [scene1][holo]overlay=x={width*7//10}:y={height//10}:all_opacity=0.4[scene2];
        
        # Scanlines and CRT effect
        [scene2]
        nullsrc=s={width}x{height}:d={duration}:r={fps},
        lutrgb=r='if(mod(Y,2),0,255)':g='if(mod(Y,2),0,255)':b='if(mod(Y,2),0,255)'[scanlines];
        [scene2][scanlines]blend=multiply:all_opacity=0.05[with_scan];
        
        # Glow effect
        [with_scan]
        split[main][glow_src];
        [glow_src]
        colorkey=black:0.3:0.2,
        boxblur=10:2,
        colorchannelmixer=2:0:0:0:0:2:0:0:0:0:2[glow];
        [main][glow]blend=screen[final];
        
        [final]
        """
    
    def _get_style_filters(self, style: str) -> str:
        """Get style-specific color grading filters."""
        
        filters = {
            "cinematic": """
                curves=preset=increase_contrast,
                colorbalance=rs=-0.05:gs=0:bs=0.05,
                vignette=PI/4:1.3
            """,
            "noir": """
                colorchannelmixer=.3:.4:.3:0:.3:.4:.3:0:.3:.4:.3,
                curves=preset=strong_contrast,
                unsharp=5:5:2:5:5:0,
                vignette=PI/4:2
            """,
            "cyberpunk": """
                colorbalance=rs=0.2:gs=-0.1:bs=0.3,
                chromashift=crh=-5:crv=5:cbh=5:cbv=-5,
                curves=preset=increase_contrast,
                gblur=sigma=1:steps=1,
                vignette=PI/4:1.5
            """,
            "apocalyptic": """
                colorbalance=rs=0.3:gs=0.1:bs=-0.2,
                curves=preset=darker,
                noise=alls=15:allf=t,
                vignette=PI/4:1.8
            """,
            "tech": """
                curves=preset=linear_contrast,
                colorbalance=rs=-0.1:gs=0:bs=0.2,
                sharpen=5:0.8,
                vignette=PI/4:1.2
            """
        }
        
        base_filter = filters.get(style, filters["cinematic"])
        
        # Add film grain and final adjustments
        return f""",
            {base_filter},
            noise=alls=8:allf=t+u,
            format=yuv420p
        """