"""
Advanced Visual Effects Engine for high-quality video generation.
Provides particle systems, lighting effects, textures, and advanced rendering.
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional, List, Tuple, Union
from datetime import datetime
import tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageChops
import cv2
import noise
from dataclasses import dataclass
from enum import Enum
import math
import random

from ..config import settings
from .ffmpeg_service import FFmpegService

logger = logging.getLogger(__name__)


class ParticleType(Enum):
    """Types of particles for different effects."""
    RAIN = "rain"
    SNOW = "snow"
    FIRE = "fire"
    SMOKE = "smoke"
    SPARKS = "sparks"
    DUST = "dust"
    STARS = "stars"
    EMBERS = "embers"
    LIGHTNING = "lightning"
    BUBBLES = "bubbles"


class LightType(Enum):
    """Types of lighting effects."""
    POINT = "point"
    DIRECTIONAL = "directional"
    SPOT = "spot"
    AMBIENT = "ambient"
    VOLUMETRIC = "volumetric"
    NEON = "neon"
    FIRE = "fire"
    HOLOGRAPHIC = "holographic"


@dataclass
class Particle:
    """Individual particle properties."""
    x: float
    y: float
    vx: float  # velocity x
    vy: float  # velocity y
    size: float
    color: Tuple[int, int, int]
    alpha: float
    lifetime: float
    age: float = 0.0
    gravity: float = 0.0
    wind: float = 0.0
    turbulence: float = 0.0


@dataclass
class Light:
    """Light source properties."""
    type: LightType
    x: float
    y: float
    intensity: float
    color: Tuple[int, int, int]
    radius: float
    angle: float = 0.0  # For spot/directional lights
    spread: float = 45.0  # For spot lights
    flicker: float = 0.0  # Animation intensity


class VisualEffectsEngine:
    """Advanced visual effects engine for cinematic quality."""
    
    def __init__(self):
        self.ffmpeg = FFmpegService()
        self.particles: List[Particle] = []
        self.lights: List[Light] = []
        self.textures: Dict[str, Image.Image] = {}
        self._load_textures()
    
    def _load_textures(self):
        """Load or generate textures for effects."""
        # Generate procedural textures
        self.textures['noise'] = self._generate_noise_texture(512, 512)
        self.textures['clouds'] = self._generate_cloud_texture(1024, 1024)
        self.textures['concrete'] = self._generate_concrete_texture(512, 512)
        self.textures['metal'] = self._generate_metal_texture(512, 512)
        self.textures['glass'] = self._generate_glass_texture(256, 256)
        self.textures['hologram'] = self._generate_hologram_texture(512, 512)
    
    def _generate_noise_texture(self, width: int, height: int) -> Image.Image:
        """Generate Perlin noise texture."""
        img = Image.new('RGB', (width, height))
        pixels = img.load()
        
        scale = 0.01
        octaves = 4
        persistence = 0.5
        lacunarity = 2.0
        
        for x in range(width):
            for y in range(height):
                value = noise.pnoise2(
                    x * scale,
                    y * scale,
                    octaves=octaves,
                    persistence=persistence,
                    lacunarity=lacunarity,
                    repeatx=width,
                    repeaty=height,
                    base=0
                )
                # Normalize to 0-255
                color_value = int((value + 1) * 127.5)
                pixels[x, y] = (color_value, color_value, color_value)
        
        return img
    
    def _generate_cloud_texture(self, width: int, height: int) -> Image.Image:
        """Generate realistic cloud texture."""
        img = Image.new('RGB', (width, height))
        pixels = img.load()
        
        # Multiple noise layers for realistic clouds
        for x in range(width):
            for y in range(height):
                # Large scale structure
                cloud1 = noise.pnoise2(x * 0.003, y * 0.003, octaves=2)
                # Medium detail
                cloud2 = noise.pnoise2(x * 0.01, y * 0.01, octaves=4) * 0.5
                # Fine detail
                cloud3 = noise.pnoise2(x * 0.05, y * 0.05, octaves=2) * 0.25
                
                value = (cloud1 + cloud2 + cloud3) / 1.75
                # Apply contrast
                value = (value + 1) / 2
                value = value ** 2  # Increase contrast
                
                color_value = int(value * 255)
                pixels[x, y] = (color_value, color_value, color_value + 10)
        
        # Apply gaussian blur for softer clouds
        img = img.filter(ImageFilter.GaussianBlur(radius=2))
        
        return img
    
    def _generate_concrete_texture(self, width: int, height: int) -> Image.Image:
        """Generate realistic concrete texture."""
        img = Image.new('RGB', (width, height), (128, 128, 128))
        draw = ImageDraw.Draw(img)
        
        # Add noise for concrete grain
        pixels = img.load()
        for x in range(width):
            for y in range(height):
                # Base concrete color with variation
                base = 128 + noise.pnoise2(x * 0.02, y * 0.02) * 20
                # Add fine grain
                grain = random.randint(-15, 15)
                color = int(base + grain)
                pixels[x, y] = (color, color, color - 5)
        
        # Add cracks
        for _ in range(5):
            start_x = random.randint(0, width)
            start_y = random.randint(0, height)
            
            points = [(start_x, start_y)]
            for _ in range(random.randint(3, 8)):
                last_x, last_y = points[-1]
                new_x = last_x + random.randint(-50, 50)
                new_y = last_y + random.randint(-50, 50)
                points.append((new_x, new_y))
            
            # Draw crack
            for i in range(len(points) - 1):
                draw.line([points[i], points[i+1]], fill=(80, 80, 75), width=2)
        
        # Add stains and weathering
        for _ in range(10):
            x = random.randint(0, width)
            y = random.randint(0, height)
            radius = random.randint(20, 60)
            
            # Create stain with gradient
            for px in range(max(0, x-radius), min(width, x+radius)):
                for py in range(max(0, y-radius), min(height, y+radius)):
                    dist = math.sqrt((px-x)**2 + (py-y)**2)
                    if dist < radius:
                        fade = 1 - (dist / radius)
                        current = pixels[px, py]
                        stain_color = random.choice([
                            (100, 95, 90),   # Dark stain
                            (140, 135, 130), # Light stain
                            (110, 105, 95)   # Oil stain
                        ])
                        pixels[px, py] = tuple(
                            int(current[i] * (1-fade*0.3) + stain_color[i] * fade*0.3)
                            for i in range(3)
                        )
        
        return img
    
    def _generate_metal_texture(self, width: int, height: int) -> Image.Image:
        """Generate brushed metal texture."""
        img = Image.new('RGB', (width, height), (180, 180, 185))
        pixels = img.load()
        
        # Horizontal brushing
        for y in range(height):
            base_color = 180 + noise.pnoise1(y * 0.1) * 20
            for x in range(width):
                # Add horizontal streaks
                variation = random.randint(-10, 10)
                color = int(base_color + variation)
                pixels[x, y] = (color, color, color + 5)
        
        # Add some vertical scratches
        for _ in range(20):
            x = random.randint(0, width)
            length = random.randint(50, height)
            start_y = random.randint(0, height - length)
            
            for y in range(start_y, start_y + length):
                if 0 <= y < height:
                    current = pixels[x, y]
                    scratch_intensity = random.randint(20, 40)
                    pixels[x, y] = tuple(c - scratch_intensity for c in current)
        
        # Add slight reflection gradient
        for y in range(height):
            reflection = int(20 * math.sin(y / height * math.pi))
            for x in range(width):
                current = pixels[x, y]
                pixels[x, y] = tuple(min(255, c + reflection) for c in current)
        
        return img
    
    def _generate_glass_texture(self, width: int, height: int) -> Image.Image:
        """Generate glass/crystal texture with refraction."""
        img = Image.new('RGBA', (width, height), (200, 200, 255, 100))
        
        # Add refraction pattern
        for x in range(width):
            for y in range(height):
                # Simulate light refraction
                refraction = noise.pnoise2(x * 0.02, y * 0.02) * 30
                alpha = 100 + int(refraction)
                
                # Slight color variation for prismatic effect
                r = 200 + int(refraction * 0.5)
                g = 200 + int(refraction * 0.3)
                b = 255
                
                img.putpixel((x, y), (r, g, b, alpha))
        
        # Add specular highlights
        draw = ImageDraw.Draw(img)
        for _ in range(5):
            x = random.randint(width//4, 3*width//4)
            y = random.randint(height//4, 3*height//4)
            radius = random.randint(5, 15)
            
            # Gradient highlight
            for r in range(radius, 0, -1):
                alpha = int(255 * (r / radius) ** 2)
                draw.ellipse(
                    [(x-r, y-r), (x+r, y+r)],
                    fill=(255, 255, 255, alpha)
                )
        
        return img
    
    def _generate_hologram_texture(self, width: int, height: int) -> Image.Image:
        """Generate holographic display texture."""
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Scan lines
        for y in range(0, height, 3):
            alpha = 50 + int(30 * math.sin(y / 10))
            draw.line([(0, y), (width, y)], fill=(0, 255, 200, alpha))
        
        # Grid pattern
        for x in range(0, width, 20):
            draw.line([(x, 0), (x, height)], fill=(0, 200, 255, 30))
        for y in range(0, height, 20):
            draw.line([(0, y), (width, y)], fill=(0, 200, 255, 30))
        
        # Add interference pattern
        pixels = img.load()
        for x in range(width):
            for y in range(height):
                current = pixels[x, y]
                interference = noise.pnoise2(x * 0.05, y * 0.05) * 50
                new_alpha = min(255, max(0, current[3] + int(interference)))
                pixels[x, y] = (current[0], current[1], current[2], new_alpha)
        
        return img
    
    async def create_particle_system(
        self,
        particle_type: ParticleType,
        count: int = 1000,
        bounds: Tuple[int, int, int, int] = (0, 0, 1920, 1080),
        wind: float = 0.0,
        gravity: float = 9.8,
        turbulence: float = 0.0
    ) -> List[Particle]:
        """Create a particle system with specified parameters."""
        
        particles = []
        x_min, y_min, x_max, y_max = bounds
        
        for _ in range(count):
            if particle_type == ParticleType.RAIN:
                particle = Particle(
                    x=random.uniform(x_min - 100, x_max + 100),
                    y=random.uniform(y_min - 200, y_min),
                    vx=wind + random.uniform(-1, 1),
                    vy=random.uniform(15, 25),
                    size=random.uniform(1, 3),
                    color=(150, 150, 200),
                    alpha=random.uniform(0.3, 0.7),
                    lifetime=random.uniform(2, 4),
                    gravity=gravity,
                    wind=wind,
                    turbulence=turbulence
                )
            
            elif particle_type == ParticleType.SNOW:
                particle = Particle(
                    x=random.uniform(x_min - 50, x_max + 50),
                    y=random.uniform(y_min - 100, y_min),
                    vx=wind + random.uniform(-0.5, 0.5),
                    vy=random.uniform(1, 3),
                    size=random.uniform(2, 5),
                    color=(255, 255, 255),
                    alpha=random.uniform(0.6, 0.9),
                    lifetime=random.uniform(5, 10),
                    gravity=gravity * 0.1,
                    wind=wind,
                    turbulence=turbulence * 2
                )
            
            elif particle_type == ParticleType.FIRE:
                particle = Particle(
                    x=random.uniform(x_min, x_max),
                    y=y_max,
                    vx=random.uniform(-2, 2),
                    vy=random.uniform(-8, -4),
                    size=random.uniform(3, 8),
                    color=(255, random.randint(100, 200), 0),
                    alpha=random.uniform(0.7, 1.0),
                    lifetime=random.uniform(0.5, 1.5),
                    gravity=-gravity * 0.5,
                    wind=wind * 0.5,
                    turbulence=turbulence * 3
                )
            
            elif particle_type == ParticleType.SMOKE:
                particle = Particle(
                    x=random.uniform(x_min, x_max),
                    y=y_max,
                    vx=random.uniform(-1, 1),
                    vy=random.uniform(-3, -1),
                    size=random.uniform(10, 20),
                    color=(100, 100, 100),
                    alpha=random.uniform(0.2, 0.4),
                    lifetime=random.uniform(3, 6),
                    gravity=-gravity * 0.2,
                    wind=wind,
                    turbulence=turbulence * 2
                )
            
            elif particle_type == ParticleType.SPARKS:
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(5, 15)
                particle = Particle(
                    x=x_max // 2,
                    y=y_max // 2,
                    vx=math.cos(angle) * speed,
                    vy=math.sin(angle) * speed,
                    size=random.uniform(1, 3),
                    color=(255, random.randint(200, 255), 0),
                    alpha=1.0,
                    lifetime=random.uniform(0.5, 1.0),
                    gravity=gravity,
                    wind=0,
                    turbulence=0
                )
            
            elif particle_type == ParticleType.STARS:
                particle = Particle(
                    x=random.uniform(x_min, x_max),
                    y=random.uniform(y_min, y_max * 0.6),
                    vx=0,
                    vy=0,
                    size=random.uniform(1, 3),
                    color=(255, 255, 200),
                    alpha=random.uniform(0.3, 1.0),
                    lifetime=float('inf'),
                    gravity=0,
                    wind=0,
                    turbulence=0
                )
            
            particles.append(particle)
        
        return particles
    
    def update_particles(self, particles: List[Particle], dt: float):
        """Update particle positions and properties."""
        
        for particle in particles[:]:
            # Update age
            particle.age += dt
            
            # Remove dead particles
            if particle.age >= particle.lifetime and particle.lifetime != float('inf'):
                particles.remove(particle)
                continue
            
            # Apply forces
            particle.vx += particle.wind * dt
            particle.vy += particle.gravity * dt
            
            # Apply turbulence
            if particle.turbulence > 0:
                particle.vx += random.uniform(-particle.turbulence, particle.turbulence) * dt
                particle.vy += random.uniform(-particle.turbulence, particle.turbulence) * dt
            
            # Update position
            particle.x += particle.vx * dt * 60  # 60 fps base
            particle.y += particle.vy * dt * 60
            
            # Fade out over lifetime
            if particle.lifetime != float('inf'):
                particle.alpha = (1 - particle.age / particle.lifetime) * particle.alpha
    
    def render_particles(
        self,
        img: Image.Image,
        particles: List[Particle],
        motion_blur: bool = True
    ):
        """Render particles onto image with effects."""
        
        # Create a separate layer for particles
        particle_layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(particle_layer)
        
        for particle in particles:
            if particle.alpha <= 0:
                continue
            
            # Motion blur effect
            if motion_blur and (abs(particle.vx) > 2 or abs(particle.vy) > 2):
                # Draw motion trail
                trail_length = int(math.sqrt(particle.vx**2 + particle.vy**2))
                for i in range(trail_length):
                    t = i / trail_length
                    trail_x = particle.x - particle.vx * t
                    trail_y = particle.y - particle.vy * t
                    trail_alpha = int(particle.alpha * 255 * (1 - t))
                    
                    draw.ellipse(
                        [(trail_x - particle.size/2, trail_y - particle.size/2),
                         (trail_x + particle.size/2, trail_y + particle.size/2)],
                        fill=(*particle.color, trail_alpha)
                    )
            else:
                # Draw particle
                alpha = int(particle.alpha * 255)
                draw.ellipse(
                    [(particle.x - particle.size/2, particle.y - particle.size/2),
                     (particle.x + particle.size/2, particle.y + particle.size/2)],
                    fill=(*particle.color, alpha)
                )
        
        # Composite particle layer onto main image
        img.paste(particle_layer, (0, 0), particle_layer)
    
    def add_light_source(
        self,
        light_type: LightType,
        position: Tuple[float, float],
        intensity: float = 1.0,
        color: Tuple[int, int, int] = (255, 255, 255),
        radius: float = 200.0,
        angle: float = 0.0,
        spread: float = 45.0,
        flicker: float = 0.0
    ) -> Light:
        """Add a light source to the scene."""
        
        light = Light(
            type=light_type,
            x=position[0],
            y=position[1],
            intensity=intensity,
            color=color,
            radius=radius,
            angle=angle,
            spread=spread,
            flicker=flicker
        )
        
        self.lights.append(light)
        return light
    
    def render_lighting(
        self,
        img: Image.Image,
        lights: List[Light],
        ambient: Tuple[int, int, int] = (20, 20, 30),
        time: float = 0.0
    ):
        """Render lighting effects onto image."""
        
        # Create light map
        light_map = Image.new('RGB', img.size, ambient)
        light_pixels = light_map.load()
        width, height = img.size
        
        for light in lights:
            # Animate light intensity with flicker
            intensity = light.intensity
            if light.flicker > 0:
                intensity *= (1 + light.flicker * math.sin(time * 10 + random.random()))
            
            if light.type == LightType.POINT:
                # Radial light falloff
                for x in range(max(0, int(light.x - light.radius)), 
                              min(width, int(light.x + light.radius))):
                    for y in range(max(0, int(light.y - light.radius)), 
                                  min(height, int(light.y + light.radius))):
                        dist = math.sqrt((x - light.x)**2 + (y - light.y)**2)
                        if dist < light.radius:
                            falloff = 1 - (dist / light.radius) ** 2
                            current = light_pixels[x, y]
                            light_pixels[x, y] = tuple(
                                min(255, int(current[i] + light.color[i] * intensity * falloff))
                                for i in range(3)
                            )
            
            elif light.type == LightType.SPOT:
                # Spot light with cone
                for x in range(max(0, int(light.x - light.radius)), 
                              min(width, int(light.x + light.radius))):
                    for y in range(max(0, int(light.y - light.radius)), 
                                  min(height, int(light.y + light.radius))):
                        dist = math.sqrt((x - light.x)**2 + (y - light.y)**2)
                        if dist < light.radius:
                            # Check if point is within cone
                            angle_to_point = math.degrees(math.atan2(y - light.y, x - light.x))
                            angle_diff = abs((angle_to_point - light.angle + 180) % 360 - 180)
                            
                            if angle_diff < light.spread / 2:
                                falloff = (1 - (dist / light.radius) ** 2) * (1 - angle_diff / (light.spread / 2))
                                current = light_pixels[x, y]
                                light_pixels[x, y] = tuple(
                                    min(255, int(current[i] + light.color[i] * intensity * falloff))
                                    for i in range(3)
                                )
            
            elif light.type == LightType.VOLUMETRIC:
                # Volumetric light rays
                ray_count = 50
                for ray in range(ray_count):
                    angle = light.angle + random.uniform(-light.spread/2, light.spread/2)
                    
                    # Trace ray
                    for r in range(0, int(light.radius), 5):
                        x = int(light.x + r * math.cos(math.radians(angle)))
                        y = int(light.y + r * math.sin(math.radians(angle)))
                        
                        if 0 <= x < width and 0 <= y < height:
                            falloff = (1 - (r / light.radius) ** 2) * 0.1
                            current = light_pixels[x, y]
                            light_pixels[x, y] = tuple(
                                min(255, int(current[i] + light.color[i] * intensity * falloff))
                                for i in range(3)
                            )
            
            elif light.type == LightType.NEON:
                # Neon glow effect
                # First pass - bright core
                draw = ImageDraw.Draw(light_map)
                for glow_radius in range(int(light.radius), 0, -5):
                    glow_intensity = (glow_radius / light.radius) ** 2
                    glow_color = tuple(
                        int(ambient[i] + light.color[i] * intensity * glow_intensity)
                        for i in range(3)
                    )
                    draw.ellipse(
                        [(light.x - glow_radius, light.y - glow_radius),
                         (light.x + glow_radius, light.y + glow_radius)],
                        fill=glow_color
                    )
        
        # Apply light map to image
        img_array = np.array(img)
        light_array = np.array(light_map)
        
        # Multiply blend mode
        blended = (img_array * (light_array / 255.0)).astype(np.uint8)
        
        return Image.fromarray(blended)
    
    def apply_atmospheric_effects(
        self,
        img: Image.Image,
        fog_density: float = 0.0,
        fog_color: Tuple[int, int, int] = (150, 150, 160),
        depth_layers: int = 3
    ) -> Image.Image:
        """Apply atmospheric perspective and fog effects."""
        
        if fog_density <= 0:
            return img
        
        width, height = img.size
        fog_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        
        # Create depth-based fog
        for layer in range(depth_layers):
            layer_y = height * (0.5 + 0.5 * layer / depth_layers)
            layer_density = fog_density * (layer + 1) / depth_layers
            
            # Gradient fog
            for y in range(int(layer_y), height):
                fog_alpha = int(255 * layer_density * ((y - layer_y) / (height - layer_y)) ** 2)
                fog_alpha = min(255, fog_alpha)
                
                draw = ImageDraw.Draw(fog_layer)
                draw.rectangle(
                    [(0, y), (width, y + 1)],
                    fill=(*fog_color, fog_alpha)
                )
        
        # Add noise to fog for realism
        fog_array = np.array(fog_layer)
        noise_array = np.random.normal(0, 10, fog_array.shape[:2])
        
        for i in range(3):
            fog_array[:, :, i] = np.clip(fog_array[:, :, i] + noise_array, 0, 255)
        
        fog_layer = Image.fromarray(fog_array.astype(np.uint8))
        
        # Composite fog onto image
        img.paste(fog_layer, (0, 0), fog_layer)
        
        return img
    
    def apply_post_processing(
        self,
        img: Image.Image,
        bloom_intensity: float = 0.0,
        chromatic_aberration: float = 0.0,
        vignette_intensity: float = 0.5,
        grain_amount: float = 0.1,
        color_grading: Optional[Dict[str, float]] = None
    ) -> Image.Image:
        """Apply cinematic post-processing effects."""
        
        # Bloom effect
        if bloom_intensity > 0:
            # Extract bright areas
            bright = img.point(lambda p: p if p > 200 else 0)
            bright = bright.filter(ImageFilter.GaussianBlur(radius=10))
            
            # Blend back
            enhancer = ImageEnhance.Brightness(bright)
            bright = enhancer.enhance(bloom_intensity)
            img = ImageChops.screen(img, bright)
        
        # Chromatic aberration
        if chromatic_aberration > 0:
            r, g, b = img.split()
            
            # Shift channels
            shift = int(chromatic_aberration * 5)
            r = ImageChops.offset(r, shift, 0)
            b = ImageChops.offset(b, -shift, 0)
            
            img = Image.merge('RGB', (r, g, b))
        
        # Vignette
        if vignette_intensity > 0:
            width, height = img.size
            
            # Create radial gradient
            vignette = Image.new('L', (width, height), 255)
            draw = ImageDraw.Draw(vignette)
            
            for i in range(min(width, height) // 2):
                alpha = int(255 * (1 - (i / (min(width, height) / 2)) ** 2))
                draw.ellipse(
                    [(i, i), (width - i, height - i)],
                    fill=int(255 - (255 - alpha) * vignette_intensity)
                )
            
            # Apply vignette
            img = Image.composite(img, Image.new('RGB', img.size, (0, 0, 0)), vignette)
        
        # Film grain
        if grain_amount > 0:
            img_array = np.array(img)
            grain = np.random.normal(0, grain_amount * 20, img_array.shape)
            img_array = np.clip(img_array + grain, 0, 255).astype(np.uint8)
            img = Image.fromarray(img_array)
        
        # Color grading
        if color_grading:
            # Adjust color channels
            r, g, b = img.split()
            
            if 'temperature' in color_grading:
                temp = color_grading['temperature']
                r = r.point(lambda p: min(255, int(p * (1 + temp * 0.1))))
                b = b.point(lambda p: min(255, int(p * (1 - temp * 0.1))))
            
            if 'tint' in color_grading:
                tint = color_grading['tint']
                g = g.point(lambda p: min(255, int(p * (1 + tint * 0.1))))
            
            if 'contrast' in color_grading:
                contrast = color_grading['contrast']
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1 + contrast)
            
            if 'saturation' in color_grading:
                saturation = color_grading['saturation']
                enhancer = ImageEnhance.Color(img)
                img = enhancer.enhance(1 + saturation)
            
            img = Image.merge('RGB', (r, g, b))
        
        return img
    
    async def create_animated_texture(
        self,
        texture_name: str,
        width: int,
        height: int,
        duration: float,
        fps: int = 30
    ) -> List[Image.Image]:
        """Create animated texture sequence."""
        
        frames = []
        total_frames = int(duration * fps)
        
        for frame in range(total_frames):
            t = frame / fps
            
            if texture_name == "water":
                img = self._create_water_frame(width, height, t)
            elif texture_name == "fire":
                img = self._create_fire_frame(width, height, t)
            elif texture_name == "electricity":
                img = self._create_electricity_frame(width, height, t)
            elif texture_name == "smoke":
                img = self._create_smoke_frame(width, height, t)
            else:
                img = Image.new('RGB', (width, height), (128, 128, 128))
            
            frames.append(img)
        
        return frames
    
    def _create_water_frame(self, width: int, height: int, t: float) -> Image.Image:
        """Create animated water texture frame."""
        
        img = Image.new('RGB', (width, height), (0, 50, 100))
        pixels = img.load()
        
        # Animated water ripples
        for x in range(width):
            for y in range(height):
                # Multiple wave frequencies
                wave1 = math.sin(x * 0.02 + t * 2) * math.cos(y * 0.02 + t * 1.5)
                wave2 = math.sin(x * 0.05 - t * 3) * math.cos(y * 0.03 + t * 2)
                wave3 = math.sin(x * 0.01 + t * 1) * math.cos(y * 0.01 - t * 0.5)
                
                combined = (wave1 + wave2 * 0.5 + wave3 * 0.3) / 1.8
                
                # Map to color
                brightness = int(128 + combined * 50)
                pixels[x, y] = (
                    max(0, brightness - 50),
                    brightness,
                    min(255, brightness + 50)
                )
        
        # Add specular highlights
        for _ in range(50):
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)
            if random.random() < 0.1:
                pixels[x, y] = (200, 220, 255)
        
        return img
    
    def _create_fire_frame(self, width: int, height: int, t: float) -> Image.Image:
        """Create animated fire texture frame."""
        
        img = Image.new('RGB', (width, height), (0, 0, 0))
        pixels = img.load()
        
        # Fire simulation
        for x in range(width):
            for y in range(height):
                # Height-based intensity
                intensity = max(0, 1 - y / height)
                
                # Add turbulence
                turb_x = x + noise.pnoise1(t * 5 + y * 0.1) * 20
                turb_y = y + noise.pnoise1(t * 3 + x * 0.1) * 10
                
                # Fire shape
                center_dist = abs(turb_x - width / 2) / (width / 2)
                flame_shape = max(0, 1 - center_dist ** 2) * intensity
                
                # Animated flickering
                flicker = noise.pnoise2(x * 0.05, t * 10) * 0.3 + 0.7
                flame_shape *= flicker
                
                # Temperature to color mapping
                if flame_shape > 0.8:
                    # White hot
                    color = (255, 255, 200)
                elif flame_shape > 0.6:
                    # Yellow
                    color = (255, 200, 0)
                elif flame_shape > 0.3:
                    # Orange
                    color = (255, 100, 0)
                elif flame_shape > 0.1:
                    # Red
                    color = (200, 0, 0)
                else:
                    color = (0, 0, 0)
                
                pixels[x, y] = tuple(int(c * flame_shape) for c in color)
        
        # Blur for smoother appearance
        img = img.filter(ImageFilter.GaussianBlur(radius=1))
        
        return img