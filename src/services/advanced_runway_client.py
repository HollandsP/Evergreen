"""
Advanced Runway API client with AI video generation and visual effects.
Integrates Stable Diffusion Video, ModelScope, GPU acceleration, and visual effects.
"""

import os
import time
import uuid
import random
import logging
import asyncio
from typing import Dict, List, Any, Optional, BinaryIO, Tuple
from datetime import datetime
import tempfile
from pathlib import Path

from .stable_video_diffusion import StableVideoDiffusionService
from .modelscope_video import ModelScopeVideoService
from .visual_effects_engine import VisualEffectsEngine, ParticleType, LightType
from .gpu_accelerated_ffmpeg import GPUAcceleratedFFmpeg
from ..config.visual_styles import VisualStyleManager, StyleCategory
from ..terminal_sim.advanced_effects import MatrixRainEffect, HologramEffect, RetroComputerEffect
from ..terminal_sim.font_manager import FontManager
from .ffmpeg_service import FFmpegService

logger = logging.getLogger(__name__)


class AdvancedRunwayClient:
    """
    Advanced client for AI video generation with multiple backends and effects.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize advanced runway client with all services."""
        self.api_key = api_key or os.getenv('RUNWAY_API_KEY', 'dummy_key')
        self.base_url = os.getenv('RUNWAY_API_URL', 'https://api.runway.ml/v1')
        
        # Initialize services
        self.svd_service = StableVideoDiffusionService()
        self.modelscope_service = ModelScopeVideoService()
        self.effects_engine = VisualEffectsEngine()
        self.gpu_ffmpeg = GPUAcceleratedFFmpeg()
        self.style_manager = VisualStyleManager()
        self.font_manager = FontManager()
        self.ffmpeg = FFmpegService()
        
        # Job storage
        self._jobs = {}
        
        # Configuration
        self.use_gpu = self.gpu_ffmpeg.gpu_info['vendor'] is not None
        self.preferred_backend = os.getenv('VIDEO_BACKEND', 'auto')  # auto, svd, modelscope, enhanced
        
        logger.info(f"Initialized Advanced Runway Client (GPU: {self.use_gpu})")
    
    async def initialize(self):
        """Initialize all async services."""
        await self.svd_service.initialize()
        await self.modelscope_service.initialize()
        logger.info("All video generation services initialized")
    
    async def generate_video(
        self,
        prompt: str,
        duration: float = 3.0,
        resolution: str = '1920x1080',
        fps: int = 30,
        style: str = 'cinematic',
        camera_movement: str = 'static',
        seed: Optional[int] = None,
        backend: Optional[str] = None,
        visual_style: Optional[str] = None,
        effects: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate video with advanced AI and effects.
        
        Args:
            prompt: Text description of the video
            duration: Video duration in seconds
            resolution: Video resolution
            fps: Frames per second
            style: Basic style (cinematic, anime, etc.)
            camera_movement: Camera movement type
            seed: Random seed
            backend: Video generation backend (auto, svd, modelscope, enhanced)
            visual_style: Advanced visual style name from style manager
            effects: List of effects to apply (particles, lighting, etc.)
            **kwargs: Additional parameters
        
        Returns:
            Generation job information
        """
        job_id = str(uuid.uuid4())
        
        # Parse resolution
        width, height = map(int, resolution.split('x'))
        
        # Determine backend
        if backend is None:
            backend = self.preferred_backend
        
        if backend == 'auto':
            # Auto-select based on availability
            if self.svd_service._initialized:
                backend = 'svd'
            elif self.modelscope_service._initialized:
                backend = 'modelscope'
            else:
                backend = 'enhanced'
        
        # Get visual style configuration
        if visual_style:
            style_config = self.style_manager.get_style(visual_style)
        else:
            # Map basic style to visual style
            style_mapping = {
                'cinematic': 'cinematic_default',
                'noir': 'film_noir',
                'cyberpunk': 'blade_runner_2049',
                'anime': 'anime_vibrant',
                'horror': 'horror_dark',
                'retro': '80s_retro'
            }
            style_config = self.style_manager.get_style(
                style_mapping.get(style, 'cinematic_default')
            )
        
        # Create job
        job_data = {
            'id': job_id,
            'status': 'processing',
            'prompt': prompt,
            'duration': duration,
            'resolution': resolution,
            'fps': fps,
            'style': style,
            'visual_style': style_config.name,
            'camera_movement': camera_movement,
            'seed': seed or random.randint(1, 1000000),
            'backend': backend,
            'effects': effects or [],
            'created_at': datetime.utcnow().isoformat(),
            'progress': 0,
            'estimated_time': duration * 10
        }
        
        self._jobs[job_id] = job_data
        
        # Start async generation
        asyncio.create_task(self._generate_video_async(job_id, job_data))
        
        logger.info(f"Started advanced video generation job: {job_id} (backend: {backend})")
        return job_data
    
    async def _generate_video_async(self, job_id: str, job_data: Dict[str, Any]):
        """Generate video asynchronously."""
        try:
            backend = job_data['backend']
            prompt = job_data['prompt']
            duration = job_data['duration']
            width, height = map(int, job_data['resolution'].split('x'))
            fps = job_data['fps']
            style_config = self.style_manager.get_style(job_data['visual_style'])
            
            # Generate base video
            if backend == 'svd':
                video_path = await self.svd_service.generate_scene_video(
                    prompt, duration, job_data['style'], (width, height), fps
                )
            elif backend == 'modelscope':
                video_path = await self.modelscope_service.generate_scene_video(
                    prompt, duration, job_data['style'], (width, height), fps
                )
            else:
                # Enhanced procedural generation
                video_path = await self._generate_enhanced_video(
                    prompt, duration, job_data['style'], (width, height), fps, style_config
                )
            
            job_data['progress'] = 50
            
            # Apply visual style
            if style_config.name != 'cinematic_default':
                video_path = await self._apply_visual_style(video_path, style_config)
            
            job_data['progress'] = 70
            
            # Apply effects
            if job_data['effects']:
                video_path = await self._apply_effects(
                    video_path, job_data['effects'], duration, fps
                )
            
            job_data['progress'] = 90
            
            # Final optimization
            if self.use_gpu:
                video_path = await self._optimize_video_gpu(video_path)
            else:
                video_path = await self._optimize_video_cpu(video_path)
            
            # Complete job
            job_data['status'] = 'completed'
            job_data['progress'] = 100
            job_data['video_path'] = video_path
            job_data['completed_at'] = datetime.utcnow().isoformat()
            
            logger.info(f"Completed video generation job: {job_id}")
            
        except Exception as e:
            logger.error(f"Video generation failed for job {job_id}: {e}")
            job_data['status'] = 'failed'
            job_data['error'] = str(e)
    
    async def _generate_enhanced_video(
        self,
        prompt: str,
        duration: float,
        style: str,
        resolution: Tuple[int, int],
        fps: int,
        style_config: Any
    ) -> str:
        """Generate enhanced video with advanced procedural techniques."""
        
        width, height = resolution
        output_path = tempfile.mktemp(suffix=".mp4")
        
        # Create high-quality scene based on prompt
        scene_type = self._analyze_prompt(prompt)
        
        # Generate scene with particles and lighting
        frames = []
        total_frames = int(duration * fps)
        
        # Initialize particle systems
        particles = []
        if 'rain' in prompt.lower() or scene_type == 'rooftop':
            rain_particles = await self.effects_engine.create_particle_system(
                ParticleType.RAIN, count=2000, bounds=(0, 0, width, height),
                wind=10.0, gravity=500.0
            )
            particles.extend(rain_particles)
        
        if 'fire' in prompt.lower() or scene_type == 'apocalyptic':
            fire_particles = await self.effects_engine.create_particle_system(
                ParticleType.FIRE, count=500, bounds=(width//3, height//2, 2*width//3, height),
                gravity=-200.0
            )
            particles.extend(fire_particles)
        
        if 'snow' in prompt.lower():
            snow_particles = await self.effects_engine.create_particle_system(
                ParticleType.SNOW, count=1500, bounds=(0, 0, width, height),
                wind=5.0, gravity=50.0
            )
            particles.extend(snow_particles)
        
        # Add lighting
        lights = []
        if scene_type == 'server':
            # Add server room lighting
            for i in range(5):
                x = (i + 1) * width // 6
                self.effects_engine.add_light_source(
                    LightType.NEON, (x, height//2), intensity=0.8,
                    color=(0, 200, 255), radius=200.0, flicker=0.1
                )
        elif scene_type == 'rooftop':
            # City lights
            for _ in range(20):
                x = random.randint(0, width)
                y = random.randint(height//2, height)
                self.effects_engine.add_light_source(
                    LightType.POINT, (x, y), intensity=0.5,
                    color=(255, 200, 100), radius=100.0
                )
        
        # Generate frames
        for frame_idx in range(total_frames):
            t = frame_idx / fps
            
            # Create base frame
            from PIL import Image, ImageDraw
            frame = Image.new('RGB', (width, height), style_config.background_color)
            
            # Draw scene elements
            if scene_type == 'rooftop':
                frame = self._draw_rooftop_scene(frame, t, style_config)
            elif scene_type == 'server':
                frame = self._draw_server_scene(frame, t, style_config)
            elif scene_type == 'concrete':
                frame = self._draw_concrete_scene(frame, t, style_config)
            else:
                frame = self._draw_generic_scene(frame, t, style_config)
            
            # Update and render particles
            self.effects_engine.update_particles(particles, 1/fps)
            self.effects_engine.render_particles(frame, particles)
            
            # Apply lighting
            frame = self.effects_engine.render_lighting(
                frame, self.effects_engine.lights,
                style_config.ambient_light_color, t
            )
            
            # Apply atmospheric effects
            frame = self.effects_engine.apply_atmospheric_effects(
                frame, style_config.fog_density,
                style_config.ambient_light_color
            )
            
            # Apply post-processing
            frame = self.effects_engine.apply_post_processing(
                frame,
                bloom_intensity=style_config.bloom_intensity,
                chromatic_aberration=style_config.chromatic_aberration,
                vignette_intensity=style_config.vignette_intensity,
                grain_amount=style_config.grain_amount,
                color_grading={
                    'temperature': style_config.temperature,
                    'tint': style_config.tint,
                    'contrast': style_config.contrast,
                    'saturation': style_config.saturation
                }
            )
            
            frames.append(frame)
        
        # Save frames as video
        import imageio
        imageio.mimsave(output_path, frames, fps=fps, quality=9)
        
        return output_path
    
    def _analyze_prompt(self, prompt: str) -> str:
        """Analyze prompt to determine scene type."""
        prompt_lower = prompt.lower()
        
        if 'rooftop' in prompt_lower or 'roof' in prompt_lower:
            return 'rooftop'
        elif 'server' in prompt_lower or 'data' in prompt_lower:
            return 'server'
        elif 'concrete' in prompt_lower or 'message' in prompt_lower:
            return 'concrete'
        elif 'control' in prompt_lower or 'operator' in prompt_lower:
            return 'control'
        elif 'office' in prompt_lower or 'cubicle' in prompt_lower:
            return 'office'
        elif 'apocalyptic' in prompt_lower or 'destroyed' in prompt_lower:
            return 'apocalyptic'
        else:
            return 'generic'
    
    def _draw_rooftop_scene(self, frame: Image.Image, t: float, style_config: Any) -> Image.Image:
        """Draw atmospheric rooftop scene."""
        draw = ImageDraw.Draw(frame)
        width, height = frame.size
        
        # Sky gradient with animation
        for y in range(height//2):
            darkness = int(style_config.background_color[0] + 
                         (y / (height//2)) * 30 * (1 + 0.1 * math.sin(t)))
            draw.rectangle([(0, y), (width, y+1)], 
                         fill=(darkness, darkness, darkness+10))
        
        # Animated city skyline
        building_count = 20
        for i in range(building_count):
            x = int(i * width / building_count)
            building_height = int(height * (0.3 + 0.5 * abs(math.sin(i * 0.5))))
            building_width = width // 25
            
            # Building with depth
            draw.polygon([
                (x, height),
                (x, height - building_height),
                (x + building_width - 5, height - building_height - 5),
                (x + building_width - 5, height)
            ], fill=(20, 20, 25))
            
            # Building face
            draw.rectangle(
                [(x, height - building_height), (x + building_width, height)],
                fill=(15, 15, 20)
            )
            
            # Windows with flickering lights
            window_rows = building_height // 30
            window_cols = building_width // 20
            for row in range(window_rows):
                for col in range(window_cols):
                    if random.random() > 0.3:
                        wx = x + col * 20 + 5
                        wy = height - building_height + row * 30 + 5
                        
                        # Animate some windows
                        flicker = random.random() < 0.02
                        brightness = 255 if flicker else random.randint(180, 230)
                        
                        color = (brightness, brightness - 20, brightness - 40)
                        draw.rectangle([(wx, wy), (wx+12, wy+20)], fill=color)
        
        return frame
    
    def _draw_server_scene(self, frame: Image.Image, t: float, style_config: Any) -> Image.Image:
        """Draw high-tech server room scene."""
        draw = ImageDraw.Draw(frame)
        width, height = frame.size
        
        # Perspective floor grid
        for i in range(0, width, 50):
            x_top = width//2 + (i - width//2) * 0.5
            x_bottom = i
            draw.line([(x_top, height//3), (x_bottom, height)], 
                     fill=(40, 40, 50), width=1)
        
        # Server racks with 3D effect
        rack_width = width // 8
        rack_spacing = width // 6
        
        for i in range(5):
            x = rack_spacing * (i + 1) - rack_width // 2
            rack_height = height * 0.6
            rack_y = height * 0.2
            
            # Rack shadow
            draw.polygon([
                (x + 10, rack_y + rack_height),
                (x + rack_width + 10, rack_y + rack_height),
                (x + rack_width + 20, height),
                (x + 20, height)
            ], fill=(5, 5, 10))
            
            # Rack side
            draw.polygon([
                (x + rack_width, rack_y),
                (x + rack_width + 10, rack_y - 10),
                (x + rack_width + 10, rack_y + rack_height - 10),
                (x + rack_width, rack_y + rack_height)
            ], fill=(30, 30, 35))
            
            # Rack front
            draw.rectangle(
                [(x, rack_y), (x + rack_width, rack_y + rack_height)],
                fill=(25, 25, 30),
                outline=(50, 50, 55),
                width=2
            )
            
            # Animated LED matrix
            units = 20
            for unit in range(units):
                unit_y = rack_y + unit * (rack_height / units)
                unit_height = (rack_height / units) - 4
                
                # Server unit
                draw.rectangle(
                    [(x + 5, unit_y), (x + rack_width - 5, unit_y + unit_height)],
                    fill=(35, 35, 40),
                    outline=(60, 60, 65)
                )
                
                # Animated LED indicators
                for led in range(10):
                    led_x = x + 10 + led * 12
                    led_y = unit_y + unit_height // 2
                    
                    # Complex animation pattern
                    phase = math.sin(t * 3 + i + unit * 0.2 + led * 0.1)
                    
                    if phase > 0.5:
                        color = (0, 255, 0)  # Green - active
                    elif phase > 0:
                        color = (0, 150, 255)  # Blue - data transfer
                    elif phase > -0.5:
                        color = (255, 150, 0)  # Orange - processing
                    else:
                        color = (100, 100, 100)  # Gray - idle
                    
                    # LED with glow effect
                    for glow in range(3):
                        glow_size = 2 + glow
                        glow_alpha = int(100 - glow * 30)
                        draw.ellipse(
                            [(led_x - glow_size, led_y - glow_size),
                             (led_x + glow_size, led_y + glow_size)],
                            fill=(*color, glow_alpha)
                        )
        
        return frame
    
    async def _apply_visual_style(self, video_path: str, style_config: Any) -> str:
        """Apply visual style to video."""
        output_path = tempfile.mktemp(suffix=".mp4")
        
        # Get FFmpeg filters for style
        style_filters = self.style_manager.get_style_ffmpeg_filters(style_config)
        
        # Apply filters using GPU if available
        if self.use_gpu:
            await self.gpu_ffmpeg.apply_gpu_filters(
                video_path, output_path,
                [{'name': 'custom', 'params': {'filter': style_filters}}]
            )
        else:
            # CPU fallback
            cmd = [
                'ffmpeg', '-y',
                '-i', video_path,
                '-vf', style_filters,
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
            
            await process.communicate()
        
        if os.path.exists(video_path):
            os.unlink(video_path)
        
        return output_path
    
    async def _apply_effects(
        self,
        video_path: str,
        effects: List[str],
        duration: float,
        fps: int
    ) -> str:
        """Apply special effects to video."""
        
        # Load video frames
        import cv2
        cap = cv2.VideoCapture(video_path)
        frames = []
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            # Convert BGR to RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frames.append(frame)
        
        cap.release()
        
        # Apply effects frame by frame
        effect_instances = []
        
        for effect_name in effects:
            if effect_name == 'matrix':
                effect_instances.append(MatrixRainEffect())
            elif effect_name == 'hologram':
                effect_instances.append(HologramEffect())
            elif effect_name == 'retro':
                effect_instances.append(RetroComputerEffect())
        
        # Process frames
        processed_frames = []
        for i, frame in enumerate(frames):
            t = i / fps
            
            # Apply each effect
            for effect in effect_instances:
                frame = effect.apply(frame, t, 1/fps)
            
            processed_frames.append(frame)
        
        # Save as video
        output_path = tempfile.mktemp(suffix=".mp4")
        height, width = processed_frames[0].shape[:2]
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        for frame in processed_frames:
            # Convert RGB back to BGR for OpenCV
            frame_bgr = cv2.cvtColor(frame.astype('uint8'), cv2.COLOR_RGB2BGR)
            out.write(frame_bgr)
        
        out.release()
        
        if os.path.exists(video_path):
            os.unlink(video_path)
        
        return output_path
    
    async def _optimize_video_gpu(self, video_path: str) -> str:
        """Optimize video using GPU acceleration."""
        output_path = tempfile.mktemp(suffix=".mp4")
        
        # Get optimization parameters
        params = self.gpu_ffmpeg.get_optimization_params('quality')
        
        # Transcode with GPU
        success = await self.gpu_ffmpeg.transcode_with_gpu(
            video_path, output_path, params
        )
        
        if success and os.path.exists(output_path):
            if os.path.exists(video_path):
                os.unlink(video_path)
            return output_path
        else:
            # Fallback to CPU
            return await self._optimize_video_cpu(video_path)
    
    async def _optimize_video_cpu(self, video_path: str) -> str:
        """Optimize video using CPU."""
        output_path = tempfile.mktemp(suffix=".mp4")
        
        cmd = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-c:v', 'libx264',
            '-preset', 'slow',
            '-crf', '18',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-movflags', '+faststart',
            output_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        await process.communicate()
        
        if os.path.exists(output_path):
            if os.path.exists(video_path):
                os.unlink(video_path)
            return output_path
        else:
            return video_path
    
    def get_generation_status(self, generation_id: str) -> Dict[str, Any]:
        """Get status of a video generation job."""
        if generation_id not in self._jobs:
            raise ValueError(f"Generation job {generation_id} not found")
        
        return self._jobs[generation_id]
    
    async def download_video(self, job_id: str) -> bytes:
        """Download generated video."""
        job = self.get_generation_status(job_id)
        
        if job['status'] != 'completed':
            raise ValueError(f"Job {job_id} is not completed yet")
        
        video_path = job.get('video_path')
        if not video_path or not os.path.exists(video_path):
            raise ValueError(f"Video file not found for job {job_id}")
        
        with open(video_path, 'rb') as f:
            video_data = f.read()
        
        logger.info(f"Downloaded video for job {job_id}: {len(video_data)} bytes")
        return video_data
    
    def list_styles(self) -> List[Dict[str, Any]]:
        """List available visual styles."""
        styles = []
        
        for style_name in self.style_manager.styles:
            preview = self.style_manager.get_style_preview(style_name)
            styles.append(preview)
        
        return styles
    
    def list_effects(self) -> List[Dict[str, str]]:
        """List available effects."""
        return [
            {'name': 'matrix', 'description': 'Matrix digital rain effect'},
            {'name': 'hologram', 'description': 'Holographic display effect'},
            {'name': 'retro', 'description': 'Retro computer boot sequence'},
            {'name': 'particles', 'description': 'Particle system effects'},
            {'name': 'lighting', 'description': 'Advanced lighting effects'}
        ]
    
    def get_gpu_info(self) -> Dict[str, Any]:
        """Get GPU information and capabilities."""
        return {
            'gpu_available': self.use_gpu,
            'gpu_info': self.gpu_ffmpeg.gpu_info,
            'gpu_capabilities': self.gpu_ffmpeg.gpu_capabilities,
            'available_encoders': {
                'h264': self.gpu_ffmpeg.get_gpu_encoder('h264'),
                'hevc': self.gpu_ffmpeg.get_gpu_encoder('hevc')
            }
        }
    
    async def benchmark_performance(self) -> Dict[str, Any]:
        """Benchmark video generation performance."""
        results = {
            'gpu_encoding': self.gpu_ffmpeg.benchmark_gpu_performance() if self.use_gpu else {},
            'backends': {}
        }
        
        # Test each backend
        test_prompt = "A futuristic cityscape at night"
        test_duration = 2.0
        
        for backend in ['svd', 'modelscope', 'enhanced']:
            try:
                start_time = time.time()
                
                job = await self.generate_video(
                    test_prompt,
                    duration=test_duration,
                    resolution='1280x720',
                    fps=24,
                    backend=backend
                )
                
                # Wait for completion
                while self.get_generation_status(job['id'])['status'] == 'processing':
                    await asyncio.sleep(0.5)
                
                end_time = time.time()
                
                results['backends'][backend] = {
                    'time': end_time - start_time,
                    'fps': (test_duration * 24) / (end_time - start_time),
                    'status': 'success'
                }
                
            except Exception as e:
                results['backends'][backend] = {
                    'status': 'failed',
                    'error': str(e)
                }
        
        return results