"""
High-quality scene generator with realistic environments.
Creates detailed procedural scenes with physics, lighting, and environmental effects.
"""

import numpy as np
import math
import random
from typing import Dict, Any, List, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from dataclasses import dataclass
from enum import Enum
import noise
import cv2
from datetime import datetime

from .visual_effects_engine import VisualEffectsEngine, ParticleType, LightType
from ..config.visual_styles import VisualStyle
from ..terminal_sim.font_manager import FontManager


class EnvironmentType(Enum):
    """Types of environments."""
    URBAN = "urban"
    NATURE = "nature"
    INDOOR = "indoor"
    INDUSTRIAL = "industrial"
    FUTURISTIC = "futuristic"
    APOCALYPTIC = "apocalyptic"
    UNDERWATER = "underwater"
    SPACE = "space"


class TimeOfDay(Enum):
    """Time of day for lighting."""
    DAWN = "dawn"
    MORNING = "morning"
    NOON = "noon"
    AFTERNOON = "afternoon"
    DUSK = "dusk"
    NIGHT = "night"
    BLUE_HOUR = "blue_hour"
    GOLDEN_HOUR = "golden_hour"


class Weather(Enum):
    """Weather conditions."""
    CLEAR = "clear"
    CLOUDY = "cloudy"
    RAIN = "rain"
    STORM = "storm"
    SNOW = "snow"
    FOG = "fog"
    SANDSTORM = "sandstorm"


@dataclass
class SceneElement:
    """Individual element in a scene."""
    type: str
    position: Tuple[float, float, float]  # x, y, z (depth)
    size: Tuple[float, float]
    rotation: float
    color: Tuple[int, int, int]
    texture: Optional[str] = None
    animation: Optional[Dict[str, Any]] = None
    physics: Optional[Dict[str, Any]] = None


class RealisticSceneGenerator:
    """Generates high-quality realistic scenes."""
    
    def __init__(self):
        self.effects_engine = VisualEffectsEngine()
        self.font_manager = FontManager()
        self.scene_elements: List[SceneElement] = []
        
    def generate_scene(
        self,
        environment: EnvironmentType,
        time_of_day: TimeOfDay,
        weather: Weather,
        resolution: Tuple[int, int],
        style: VisualStyle,
        camera_angle: str = "medium",
        camera_movement: Optional[Dict[str, Any]] = None
    ) -> Image.Image:
        """Generate a complete scene."""
        
        width, height = resolution
        
        # Create base image
        base_color = self._get_sky_color(time_of_day, weather)
        img = Image.new('RGB', (width, height), base_color)
        
        # Generate environment-specific elements
        if environment == EnvironmentType.URBAN:
            img = self._generate_urban_scene(img, time_of_day, weather, style)
        elif environment == EnvironmentType.NATURE:
            img = self._generate_nature_scene(img, time_of_day, weather, style)
        elif environment == EnvironmentType.INDOOR:
            img = self._generate_indoor_scene(img, time_of_day, style)
        elif environment == EnvironmentType.INDUSTRIAL:
            img = self._generate_industrial_scene(img, time_of_day, weather, style)
        elif environment == EnvironmentType.FUTURISTIC:
            img = self._generate_futuristic_scene(img, time_of_day, weather, style)
        elif environment == EnvironmentType.APOCALYPTIC:
            img = self._generate_apocalyptic_scene(img, time_of_day, weather, style)
        elif environment == EnvironmentType.UNDERWATER:
            img = self._generate_underwater_scene(img, time_of_day, style)
        elif environment == EnvironmentType.SPACE:
            img = self._generate_space_scene(img, style)
        
        # Apply weather effects
        img = self._apply_weather_effects(img, weather, time_of_day)
        
        # Apply camera effects
        if camera_angle != "medium":
            img = self._apply_camera_angle(img, camera_angle)
        
        # Apply depth of field if enabled
        if style.depth_of_field:
            img = self._apply_depth_of_field(img)
        
        return img
    
    def _get_sky_color(self, time_of_day: TimeOfDay, weather: Weather) -> Tuple[int, int, int]:
        """Get appropriate sky color based on time and weather."""
        
        # Base colors for different times
        sky_colors = {
            TimeOfDay.DAWN: (50, 80, 120),
            TimeOfDay.MORNING: (135, 206, 235),
            TimeOfDay.NOON: (180, 220, 255),
            TimeOfDay.AFTERNOON: (160, 200, 240),
            TimeOfDay.DUSK: (255, 150, 100),
            TimeOfDay.NIGHT: (10, 20, 40),
            TimeOfDay.BLUE_HOUR: (40, 60, 100),
            TimeOfDay.GOLDEN_HOUR: (255, 200, 150)
        }
        
        base_color = sky_colors.get(time_of_day, (100, 150, 200))
        
        # Modify for weather
        if weather == Weather.CLOUDY:
            # Desaturate and darken
            base_color = tuple(int(c * 0.7) for c in base_color)
        elif weather == Weather.STORM:
            # Very dark
            base_color = tuple(int(c * 0.3) for c in base_color)
        elif weather == Weather.FOG:
            # Grayish
            avg = sum(base_color) // 3
            base_color = (avg, avg, avg + 10)
        
        return base_color
    
    def _generate_urban_scene(
        self,
        img: Image.Image,
        time_of_day: TimeOfDay,
        weather: Weather,
        style: VisualStyle
    ) -> Image.Image:
        """Generate urban cityscape."""
        
        draw = ImageDraw.Draw(img)
        width, height = img.size
        
        # Generate city skyline with parallax layers
        layers = 3
        for layer in range(layers):
            depth = layer / layers
            
            # Building properties based on depth
            building_height_range = (
                int(height * (0.3 - depth * 0.1)),
                int(height * (0.8 - depth * 0.3))
            )
            building_width_range = (
                int(width * (0.05 + depth * 0.02)),
                int(width * (0.15 + depth * 0.05))
            )
            
            # Color based on depth (atmospheric perspective)
            base_building_color = (50, 50, 60)
            fog_color = self._get_sky_color(time_of_day, weather)
            building_color = self._blend_colors(base_building_color, fog_color, depth * 0.5)
            
            # Generate buildings
            x = 0
            while x < width:
                building_width = random.randint(*building_width_range)
                building_height = random.randint(*building_height_range)
                
                # Building base
                building_y = height - building_height
                
                # Add 3D effect
                if layer == 0:  # Foreground buildings only
                    # Building side (darker)
                    side_color = tuple(int(c * 0.7) for c in building_color)
                    draw.polygon([
                        (x + building_width, building_y),
                        (x + building_width + 10, building_y - 10),
                        (x + building_width + 10, height),
                        (x + building_width, height)
                    ], fill=side_color)
                    
                    # Building top
                    top_color = tuple(int(c * 1.2) for c in building_color)
                    draw.polygon([
                        (x, building_y),
                        (x + 10, building_y - 10),
                        (x + building_width + 10, building_y - 10),
                        (x + building_width, building_y)
                    ], fill=top_color)
                
                # Building front
                draw.rectangle(
                    [(x, building_y), (x + building_width, height)],
                    fill=building_color
                )
                
                # Windows
                self._draw_building_windows(
                    draw, x, building_y, building_width, building_height,
                    time_of_day, layer == 0
                )
                
                # Architectural details for foreground
                if layer == 0:
                    # Antenna
                    if random.random() < 0.3:
                        antenna_x = x + building_width // 2
                        draw.line(
                            [(antenna_x, building_y), (antenna_x, building_y - 30)],
                            fill=(100, 100, 100), width=2
                        )
                        # Blinking light
                        if time_of_day in [TimeOfDay.DUSK, TimeOfDay.NIGHT]:
                            draw.ellipse(
                                [(antenna_x - 3, building_y - 33),
                                 (antenna_x + 3, building_y - 27)],
                                fill=(255, 0, 0)
                            )
                
                x += building_width + random.randint(5, 20)
        
        # Add street level details
        self._add_street_level(draw, width, height, time_of_day)
        
        # Add vehicles and people for scale
        if weather not in [Weather.STORM, Weather.SANDSTORM]:
            self._add_urban_life(draw, width, height, time_of_day)
        
        return img
    
    def _draw_building_windows(
        self,
        draw: ImageDraw.Draw,
        x: int,
        y: int,
        width: int,
        height: int,
        time_of_day: TimeOfDay,
        is_foreground: bool
    ):
        """Draw realistic building windows."""
        
        window_width = 8 if is_foreground else 4
        window_height = 12 if is_foreground else 6
        spacing_x = 15 if is_foreground else 10
        spacing_y = 20 if is_foreground else 15
        
        # Window illumination based on time
        if time_of_day == TimeOfDay.NIGHT:
            lit_probability = 0.7
        elif time_of_day in [TimeOfDay.DUSK, TimeOfDay.DAWN]:
            lit_probability = 0.5
        else:
            lit_probability = 0.1
        
        for wx in range(x + 10, x + width - 10, spacing_x):
            for wy in range(y + 10, y + height - 10, spacing_y):
                if random.random() < lit_probability:
                    # Lit window
                    brightness = random.randint(200, 255)
                    window_color = (brightness, brightness - 20, brightness - 40)
                    
                    # Window glow
                    if is_foreground and time_of_day == TimeOfDay.NIGHT:
                        glow_size = window_width + 4
                        draw.rectangle(
                            [(wx - 2, wy - 2), (wx + glow_size, wy + window_height + 2)],
                            fill=(brightness // 2, brightness // 2 - 10, brightness // 2 - 20)
                        )
                else:
                    # Dark window
                    window_color = (30, 30, 40)
                
                draw.rectangle(
                    [(wx, wy), (wx + window_width, wy + window_height)],
                    fill=window_color
                )
                
                # Window details for foreground
                if is_foreground and random.random() < 0.2:
                    # Curtains or blinds
                    draw.rectangle(
                        [(wx, wy), (wx + window_width, wy + window_height // 3)],
                        fill=(60, 60, 70)
                    )
    
    def _add_street_level(
        self,
        draw: ImageDraw.Draw,
        width: int,
        height: int,
        time_of_day: TimeOfDay
    ):
        """Add street level details."""
        
        street_y = height - 50
        
        # Sidewalk
        draw.rectangle([(0, street_y), (width, height)], fill=(80, 80, 85))
        
        # Road
        draw.rectangle([(0, street_y + 20), (width, height)], fill=(40, 40, 45))
        
        # Road markings
        for x in range(0, width, 100):
            draw.rectangle(
                [(x, street_y + 35), (x + 50, street_y + 40)],
                fill=(200, 200, 200)
            )
        
        # Street lights
        for x in range(50, width, 200):
            # Light pole
            draw.rectangle(
                [(x, street_y - 80), (x + 5, street_y + 20)],
                fill=(60, 60, 65)
            )
            
            # Light fixture
            if time_of_day in [TimeOfDay.DUSK, TimeOfDay.NIGHT, TimeOfDay.DAWN]:
                # Glowing light
                for radius in range(30, 0, -5):
                    alpha = int(255 * (1 - radius / 30) * 0.3)
                    draw.ellipse(
                        [(x - radius, street_y - 80 - radius),
                         (x + radius, street_y - 80 + radius)],
                        fill=(255, 200, 100, alpha)
                    )
    
    def _add_urban_life(
        self,
        draw: ImageDraw.Draw,
        width: int,
        height: int,
        time_of_day: TimeOfDay
    ):
        """Add vehicles and pedestrians."""
        
        street_y = height - 30
        
        # Cars
        num_cars = random.randint(3, 6)
        for _ in range(num_cars):
            car_x = random.randint(0, width - 60)
            car_width = random.randint(40, 60)
            car_height = 20
            
            # Car body
            car_color = random.choice([
                (150, 30, 30),   # Red
                (30, 30, 150),   # Blue
                (150, 150, 150), # Silver
                (30, 30, 30),    # Black
                (200, 200, 200)  # White
            ])
            
            draw.rectangle(
                [(car_x, street_y - car_height), (car_x + car_width, street_y)],
                fill=car_color
            )
            
            # Windows
            draw.rectangle(
                [(car_x + 5, street_y - car_height + 5),
                 (car_x + car_width - 5, street_y - car_height + 10)],
                fill=(50, 50, 60)
            )
            
            # Headlights/taillights
            if time_of_day in [TimeOfDay.DUSK, TimeOfDay.NIGHT]:
                # Headlights
                draw.ellipse(
                    [(car_x + car_width - 10, street_y - 15),
                     (car_x + car_width - 5, street_y - 10)],
                    fill=(255, 255, 200)
                )
                # Taillights
                draw.ellipse(
                    [(car_x + 5, street_y - 15),
                     (car_x + 10, street_y - 10)],
                    fill=(255, 0, 0)
                )
        
        # Pedestrians
        if time_of_day not in [TimeOfDay.NIGHT]:
            num_people = random.randint(5, 10)
            sidewalk_y = height - 50
            
            for _ in range(num_people):
                person_x = random.randint(10, width - 10)
                person_height = random.randint(15, 20)
                
                # Simple silhouette
                draw.ellipse(
                    [(person_x - 3, sidewalk_y - person_height - 5),
                     (person_x + 3, sidewalk_y - person_height + 1)],
                    fill=(20, 20, 20)
                )
                draw.rectangle(
                    [(person_x - 2, sidewalk_y - person_height + 1),
                     (person_x + 2, sidewalk_y)],
                    fill=(20, 20, 20)
                )
    
    def _generate_nature_scene(
        self,
        img: Image.Image,
        time_of_day: TimeOfDay,
        weather: Weather,
        style: VisualStyle
    ) -> Image.Image:
        """Generate natural landscape."""
        
        draw = ImageDraw.Draw(img)
        width, height = img.size
        
        # Generate terrain using Perlin noise
        terrain_height = []
        for x in range(width):
            # Multiple octaves for realistic terrain
            height_value = 0
            amplitude = 1.0
            frequency = 0.005
            
            for _ in range(4):
                height_value += noise.pnoise1(x * frequency) * amplitude
                amplitude *= 0.5
                frequency *= 2
            
            terrain_y = int(height * 0.6 + height_value * height * 0.2)
            terrain_height.append(terrain_y)
        
        # Draw terrain layers (background to foreground)
        # Mountains
        mountain_color = (80, 90, 100)
        for x in range(width):
            mountain_y = terrain_height[x] - 100
            draw.line([(x, mountain_y), (x, height)], fill=mountain_color)
        
        # Hills
        hill_color = (60, 80, 60)
        for x in range(width):
            hill_y = terrain_height[x] - 50
            draw.line([(x, hill_y), (x, height)], fill=hill_color)
        
        # Foreground terrain
        grass_color = (40, 60, 40)
        for x in range(width):
            draw.line([(x, terrain_height[x]), (x, height)], fill=grass_color)
        
        # Add vegetation
        self._add_vegetation(draw, width, height, terrain_height, time_of_day)
        
        # Add water features
        if random.random() < 0.5:
            self._add_water_feature(draw, width, height, terrain_height)
        
        # Add wildlife
        if weather == Weather.CLEAR and time_of_day not in [TimeOfDay.NIGHT]:
            self._add_wildlife(draw, width, height, terrain_height)
        
        return img
    
    def _add_vegetation(
        self,
        draw: ImageDraw.Draw,
        width: int,
        height: int,
        terrain_height: List[int],
        time_of_day: TimeOfDay
    ):
        """Add trees, bushes, and grass."""
        
        # Trees
        num_trees = random.randint(10, 30)
        for _ in range(num_trees):
            tree_x = random.randint(20, width - 20)
            tree_y = terrain_height[min(tree_x, len(terrain_height) - 1)]
            tree_height = random.randint(60, 120)
            
            # Tree trunk
            trunk_width = tree_height // 10
            draw.rectangle(
                [(tree_x - trunk_width // 2, tree_y - tree_height),
                 (tree_x + trunk_width // 2, tree_y)],
                fill=(60, 40, 20)
            )
            
            # Tree foliage (multiple layers for depth)
            foliage_radius = tree_height // 3
            for layer in range(3):
                layer_offset = layer * 10
                layer_color = (
                    20 + layer * 10,
                    40 + layer * 15,
                    20 + layer * 5
                )
                
                # Irregular shape using multiple circles
                for _ in range(5):
                    offset_x = random.randint(-foliage_radius // 2, foliage_radius // 2)
                    offset_y = random.randint(-foliage_radius // 2, 0)
                    
                    draw.ellipse(
                        [(tree_x - foliage_radius + offset_x + layer_offset,
                          tree_y - tree_height + offset_y + layer_offset),
                         (tree_x + foliage_radius + offset_x - layer_offset,
                          tree_y - tree_height + foliage_radius + offset_y - layer_offset)],
                        fill=layer_color
                    )
        
        # Bushes
        num_bushes = random.randint(20, 40)
        for _ in range(num_bushes):
            bush_x = random.randint(10, width - 10)
            bush_y = terrain_height[min(bush_x, len(terrain_height) - 1)]
            bush_size = random.randint(10, 25)
            
            # Irregular bush shape
            for _ in range(3):
                offset_x = random.randint(-bush_size // 2, bush_size // 2)
                draw.ellipse(
                    [(bush_x - bush_size + offset_x, bush_y - bush_size),
                     (bush_x + bush_size + offset_x, bush_y)],
                    fill=(30, 50, 30)
                )
        
        # Grass details
        if time_of_day not in [TimeOfDay.NIGHT]:
            for _ in range(500):
                grass_x = random.randint(0, width)
                grass_y = terrain_height[min(grass_x, len(terrain_height) - 1)]
                grass_height = random.randint(3, 8)
                
                draw.line(
                    [(grass_x, grass_y), (grass_x + random.randint(-2, 2), grass_y - grass_height)],
                    fill=(50, 70, 50),
                    width=1
                )
    
    def _add_water_feature(
        self,
        draw: ImageDraw.Draw,
        width: int,
        height: int,
        terrain_height: List[int]
    ):
        """Add lake or river."""
        
        water_type = random.choice(['lake', 'river'])
        
        if water_type == 'lake':
            # Find a valley for the lake
            lake_center_x = width // 2 + random.randint(-width // 4, width // 4)
            lake_width = random.randint(width // 4, width // 2)
            lake_start_x = max(0, lake_center_x - lake_width // 2)
            lake_end_x = min(width, lake_center_x + lake_width // 2)
            
            # Find lowest point in the area
            lake_y = min(terrain_height[lake_start_x:lake_end_x])
            
            # Draw lake with reflections
            water_color = (30, 60, 90)
            for x in range(lake_start_x, lake_end_x):
                # Wavy water surface
                wave = int(math.sin((x - lake_start_x) * 0.1) * 3)
                draw.line(
                    [(x, lake_y + wave), (x, height)],
                    fill=water_color
                )
                
                # Reflection highlights
                if x % 10 < 3:
                    draw.line(
                        [(x, lake_y + wave), (x, lake_y + wave + 2)],
                        fill=(150, 180, 200)
                    )
        
        else:  # river
            # Winding river
            river_points = []
            river_x = random.randint(0, width // 4)
            
            while river_x < width:
                river_y = terrain_height[min(river_x, len(terrain_height) - 1)]
                river_points.append((river_x, river_y))
                river_x += random.randint(20, 40)
                
            # Draw river
            if len(river_points) > 2:
                for i in range(len(river_points) - 1):
                    start = river_points[i]
                    end = river_points[i + 1]
                    
                    # River width varies
                    river_width = random.randint(10, 30)
                    
                    # Draw river segment
                    for w in range(river_width):
                        color_variation = int(w / river_width * 30)
                        water_color = (30 + color_variation, 60 + color_variation, 90 + color_variation)
                        
                        draw.line(
                            [(start[0], start[1] + w), (end[0], end[1] + w)],
                            fill=water_color,
                            width=2
                        )
    
    def _generate_futuristic_scene(
        self,
        img: Image.Image,
        time_of_day: TimeOfDay,
        weather: Weather,
        style: VisualStyle
    ) -> Image.Image:
        """Generate futuristic sci-fi scene."""
        
        draw = ImageDraw.Draw(img)
        width, height = img.size
        
        # Futuristic city with unique architecture
        # Flying vehicles layer
        self._add_flying_vehicles(draw, width, height, time_of_day)
        
        # Megastructures
        num_structures = random.randint(3, 6)
        for i in range(num_structures):
            x = i * width // num_structures + random.randint(-50, 50)
            structure_width = random.randint(100, 200)
            structure_height = random.randint(height // 2, int(height * 0.9))
            
            # Unique architectural shapes
            shape_type = random.choice(['pyramid', 'cylinder', 'angular', 'organic'])
            
            if shape_type == 'pyramid':
                # Pyramid structure
                points = [
                    (x, height),
                    (x + structure_width, height),
                    (x + structure_width // 2, height - structure_height)
                ]
                draw.polygon(points, fill=(40, 50, 60))
                
                # Glowing edges
                for i in range(len(points)):
                    start = points[i]
                    end = points[(i + 1) % len(points)]
                    draw.line([start, end], fill=(0, 200, 255), width=2)
            
            elif shape_type == 'cylinder':
                # Cylindrical tower
                draw.ellipse(
                    [(x, height - 30), (x + structure_width, height + 30)],
                    fill=(30, 40, 50)
                )
                draw.rectangle(
                    [(x, height - structure_height), (x + structure_width, height)],
                    fill=(40, 50, 60)
                )
                draw.ellipse(
                    [(x, height - structure_height - 30),
                     (x + structure_width, height - structure_height + 30)],
                    fill=(50, 60, 70)
                )
            
            elif shape_type == 'angular':
                # Angular modern structure
                points = [
                    (x, height),
                    (x + structure_width * 0.8, height),
                    (x + structure_width, height - structure_height * 0.7),
                    (x + structure_width * 0.2, height - structure_height)
                ]
                draw.polygon(points, fill=(45, 55, 65))
            
            else:  # organic
                # Organic curved structure
                for y in range(height - structure_height, height, 5):
                    progress = (y - (height - structure_height)) / structure_height
                    curve = math.sin(progress * math.pi) * structure_width * 0.3
                    
                    draw.rectangle(
                        [(x + curve, y), (x + structure_width - curve, y + 5)],
                        fill=(40 + int(progress * 20), 50 + int(progress * 20), 60 + int(progress * 20))
                    )
            
            # Add glowing windows/panels
            self._add_futuristic_details(
                draw, x, height - structure_height,
                structure_width, structure_height, time_of_day
            )
        
        # Holographic displays
        num_holograms = random.randint(3, 8)
        for _ in range(num_holograms):
            holo_x = random.randint(50, width - 50)
            holo_y = random.randint(height // 3, height - 100)
            holo_size = random.randint(30, 80)
            
            # Hologram effect
            for alpha in range(100, 0, -20):
                size = holo_size * (alpha / 100)
                color = (0, 200, 255, alpha)
                
                draw.rectangle(
                    [(holo_x - size, holo_y - size),
                     (holo_x + size, holo_y + size)],
                    fill=None,
                    outline=color,
                    width=2
                )
        
        # Energy beams
        if random.random() < 0.5:
            for _ in range(random.randint(1, 3)):
                beam_x = random.randint(0, width)
                beam_color = random.choice([
                    (255, 0, 100),   # Pink
                    (0, 255, 200),   # Cyan
                    (255, 200, 0),   # Yellow
                ])
                
                # Beam with glow
                for w in range(20, 0, -2):
                    alpha = int(255 * (1 - w / 20) * 0.5)
                    draw.line(
                        [(beam_x - w, height), (beam_x - w // 2, 0)],
                        fill=(*beam_color, alpha),
                        width=w
                    )
        
        return img
    
    def _add_futuristic_details(
        self,
        draw: ImageDraw.Draw,
        x: int,
        y: int,
        width: int,
        height: int,
        time_of_day: TimeOfDay
    ):
        """Add futuristic building details."""
        
        # LED strips
        strip_spacing = 50
        for strip_y in range(y + strip_spacing, y + height, strip_spacing):
            # Animated color
            hue = (strip_y / height * 360) % 360
            strip_color = self._hsv_to_rgb(hue, 1.0, 1.0)
            
            draw.line(
                [(x + 5, strip_y), (x + width - 5, strip_y)],
                fill=strip_color,
                width=2
            )
        
        # Glowing panels
        panel_size = 20
        for px in range(x + 20, x + width - 20, 40):
            for py in range(y + 20, y + height - 20, 40):
                if random.random() < 0.7:
                    # Active panel
                    panel_color = random.choice([
                        (0, 255, 200),
                        (255, 0, 200),
                        (200, 255, 0),
                        (100, 100, 255)
                    ])
                    
                    # Glow effect
                    for glow in range(3):
                        glow_size = panel_size + glow * 2
                        alpha = int(255 * (1 - glow / 3) * 0.5)
                        draw.rectangle(
                            [(px - glow, py - glow),
                             (px + glow_size, py + glow_size)],
                            fill=(*panel_color, alpha)
                        )
                    
                    # Core panel
                    draw.rectangle(
                        [(px, py), (px + panel_size, py + panel_size)],
                        fill=panel_color
                    )
    
    def _add_flying_vehicles(
        self,
        draw: ImageDraw.Draw,
        width: int,
        height: int,
        time_of_day: TimeOfDay
    ):
        """Add flying vehicles to futuristic scene."""
        
        num_vehicles = random.randint(5, 15)
        
        for _ in range(num_vehicles):
            # Vehicle position and size
            veh_x = random.randint(0, width)
            veh_y = random.randint(50, height // 2)
            veh_size = random.randint(10, 30)
            
            # Distance-based sizing
            distance_factor = veh_y / (height // 2)
            veh_size = int(veh_size * distance_factor)
            
            # Vehicle shape
            vehicle_color = (80, 90, 100)
            
            # Streamlined body
            draw.ellipse(
                [(veh_x - veh_size, veh_y - veh_size // 3),
                 (veh_x + veh_size, veh_y + veh_size // 3)],
                fill=vehicle_color
            )
            
            # Thrusters
            if time_of_day in [TimeOfDay.DUSK, TimeOfDay.NIGHT]:
                # Glowing thrusters
                thruster_color = (100, 200, 255)
                
                # Left thruster
                draw.ellipse(
                    [(veh_x - veh_size - 5, veh_y),
                     (veh_x - veh_size, veh_y + 5)],
                    fill=thruster_color
                )
                
                # Right thruster
                draw.ellipse(
                    [(veh_x + veh_size, veh_y),
                     (veh_x + veh_size + 5, veh_y + 5)],
                    fill=thruster_color
                )
                
                # Thruster trails
                trail_length = random.randint(20, 50)
                for i in range(trail_length):
                    alpha = int(255 * (1 - i / trail_length) * 0.5)
                    trail_y = veh_y + i
                    
                    draw.line(
                        [(veh_x - veh_size - 2, trail_y),
                         (veh_x - veh_size, trail_y)],
                        fill=(*thruster_color, alpha)
                    )
                    draw.line(
                        [(veh_x + veh_size, trail_y),
                         (veh_x + veh_size + 2, trail_y)],
                        fill=(*thruster_color, alpha)
                    )
    
    def _generate_apocalyptic_scene(
        self,
        img: Image.Image,
        time_of_day: TimeOfDay,
        weather: Weather,
        style: VisualStyle
    ) -> Image.Image:
        """Generate post-apocalyptic wasteland."""
        
        draw = ImageDraw.Draw(img)
        width, height = img.size
        
        # Ruined cityscape
        # Broken buildings
        num_ruins = random.randint(5, 10)
        
        for i in range(num_ruins):
            ruin_x = i * width // num_ruins + random.randint(-30, 30)
            ruin_width = random.randint(60, 120)
            original_height = random.randint(height // 2, int(height * 0.8))
            
            # Damaged height
            ruin_height = random.randint(original_height // 3, int(original_height * 0.7))
            ruin_y = height - ruin_height
            
            # Main structure (damaged)
            ruin_color = (60, 55, 50)
            draw.rectangle(
                [(ruin_x, ruin_y), (ruin_x + ruin_width, height)],
                fill=ruin_color
            )
            
            # Exposed framework
            for beam_x in range(ruin_x + 10, ruin_x + ruin_width - 10, 20):
                draw.line(
                    [(beam_x, ruin_y), (beam_x, ruin_y - 30)],
                    fill=(40, 35, 30),
                    width=2
                )
            
            # Broken edges
            break_points = []
            for _ in range(random.randint(3, 8)):
                break_x = ruin_x + random.randint(0, ruin_width)
                break_y = ruin_y + random.randint(-20, 20)
                break_points.append((break_x, break_y))
            
            if break_points:
                break_points.sort(key=lambda p: p[0])
                break_points.insert(0, (ruin_x, ruin_y))
                break_points.append((ruin_x + ruin_width, ruin_y))
                
                # Draw jagged top
                draw.polygon(
                    break_points + [(ruin_x + ruin_width, ruin_y + 50), (ruin_x, ruin_y + 50)],
                    fill=ruin_color
                )
            
            # Rubble at base
            for _ in range(random.randint(5, 15)):
                rubble_x = ruin_x + random.randint(-20, ruin_width + 20)
                rubble_y = height - random.randint(0, 30)
                rubble_size = random.randint(5, 15)
                
                draw.polygon(
                    [(rubble_x, rubble_y),
                     (rubble_x + rubble_size, rubble_y - rubble_size // 2),
                     (rubble_x + rubble_size // 2, rubble_y - rubble_size)],
                    fill=(50, 45, 40)
                )
        
        # Abandoned vehicles
        num_vehicles = random.randint(2, 5)
        for _ in range(num_vehicles):
            veh_x = random.randint(50, width - 100)
            veh_y = height - random.randint(20, 60)
            
            # Rusted vehicle
            draw.rectangle(
                [(veh_x, veh_y - 20), (veh_x + 60, veh_y)],
                fill=(80, 50, 30)
            )
            
            # Broken windows
            draw.rectangle(
                [(veh_x + 10, veh_y - 15), (veh_x + 25, veh_y - 10)],
                fill=(30, 30, 30)
            )
        
        # Dead vegetation
        for _ in range(random.randint(10, 20)):
            tree_x = random.randint(20, width - 20)
            tree_y = height - random.randint(0, 50)
            tree_height = random.randint(40, 80)
            
            # Dead tree trunk
            draw.line(
                [(tree_x, tree_y), (tree_x, tree_y - tree_height)],
                fill=(40, 35, 30),
                width=5
            )
            
            # Bare branches
            for _ in range(random.randint(3, 6)):
                branch_y = tree_y - random.randint(20, tree_height - 10)
                branch_length = random.randint(10, 30)
                branch_angle = random.uniform(-0.5, 0.5)
                
                end_x = tree_x + int(branch_length * math.cos(branch_angle))
                end_y = branch_y - int(branch_length * math.sin(branch_angle))
                
                draw.line(
                    [(tree_x, branch_y), (end_x, end_y)],
                    fill=(40, 35, 30),
                    width=2
                )
        
        # Ash and debris in the air
        for _ in range(200):
            ash_x = random.randint(0, width)
            ash_y = random.randint(0, height)
            ash_size = random.randint(1, 3)
            
            draw.ellipse(
                [(ash_x, ash_y), (ash_x + ash_size, ash_y + ash_size)],
                fill=(100, 95, 90)
            )
        
        # Fire and smoke
        if random.random() < 0.5:
            fire_x = random.randint(width // 4, 3 * width // 4)
            fire_y = height - random.randint(0, 100)
            
            # Smoke plume
            for i in range(50):
                smoke_y = fire_y - i * 10
                smoke_radius = 10 + i
                smoke_alpha = int(255 * (1 - i / 50) * 0.3)
                
                draw.ellipse(
                    [(fire_x - smoke_radius, smoke_y - smoke_radius),
                     (fire_x + smoke_radius, smoke_y + smoke_radius)],
                    fill=(50, 50, 50, smoke_alpha)
                )
            
            # Fire glow
            for radius in range(30, 0, -5):
                fire_alpha = int(255 * (1 - radius / 30))
                fire_color = (
                    255,
                    int(200 * (1 - radius / 30)),
                    0
                )
                
                draw.ellipse(
                    [(fire_x - radius, fire_y - radius),
                     (fire_x + radius, fire_y + radius)],
                    fill=(*fire_color, fire_alpha)
                )
        
        return img
    
    def _apply_weather_effects(
        self,
        img: Image.Image,
        weather: Weather,
        time_of_day: TimeOfDay
    ) -> Image.Image:
        """Apply weather effects to the scene."""
        
        if weather == Weather.RAIN:
            # Create rain particles
            particles = asyncio.run(
                self.effects_engine.create_particle_system(
                    ParticleType.RAIN,
                    count=2000,
                    bounds=(0, 0, img.width, img.height),
                    wind=20.0,
                    gravity=600.0
                )
            )
            
            # Update and render particles
            self.effects_engine.update_particles(particles, 1/30)
            self.effects_engine.render_particles(img, particles)
            
            # Wet surface effect
            img = img.filter(ImageFilter.GaussianBlur(radius=1))
            
        elif weather == Weather.SNOW:
            # Create snow particles
            particles = asyncio.run(
                self.effects_engine.create_particle_system(
                    ParticleType.SNOW,
                    count=1500,
                    bounds=(0, 0, img.width, img.height),
                    wind=10.0,
                    gravity=50.0
                )
            )
            
            self.effects_engine.update_particles(particles, 1/30)
            self.effects_engine.render_particles(img, particles)
            
        elif weather == Weather.FOG:
            # Apply fog effect
            img = self.effects_engine.apply_atmospheric_effects(
                img,
                fog_density=0.5,
                fog_color=(150, 150, 160)
            )
            
        elif weather == Weather.STORM:
            # Dark atmosphere
            img = img.point(lambda p: p * 0.6)
            
            # Lightning flash occasionally
            if random.random() < 0.1:
                # Create lightning overlay
                lightning = Image.new('RGBA', img.size, (255, 255, 255, 100))
                img = Image.alpha_composite(img.convert('RGBA'), lightning).convert('RGB')
        
        return img
    
    def _apply_camera_angle(self, img: Image.Image, angle: str) -> Image.Image:
        """Apply camera angle perspective transform."""
        
        if angle == "low":
            # Low angle - compress top, expand bottom
            img = img.transform(
                img.size,
                Image.PERSPECTIVE,
                (0, 0.2, 0, 0, 1, -0.2, 0, 0),
                Image.BICUBIC
            )
        elif angle == "high":
            # High angle - compress bottom, expand top
            img = img.transform(
                img.size,
                Image.PERSPECTIVE,
                (0, -0.2, 0, 0, 1, 0.2, 0, 0),
                Image.BICUBIC
            )
        elif angle == "dutch":
            # Dutch angle - rotate slightly
            img = img.rotate(random.uniform(-15, 15), expand=False, fillcolor=(0, 0, 0))
        
        return img
    
    def _apply_depth_of_field(self, img: Image.Image) -> Image.Image:
        """Apply depth of field blur effect."""
        
        # Create depth map (simple gradient for now)
        width, height = img.size
        depth_map = Image.new('L', (width, height))
        draw = ImageDraw.Draw(depth_map)
        
        # Gradient from top to bottom
        for y in range(height):
            gray = int(255 * y / height)
            draw.line([(0, y), (width, y)], fill=gray)
        
        # Apply variable blur based on depth
        result = img.copy()
        
        # Split into depth layers
        layers = 5
        for i in range(layers):
            # Create mask for this depth layer
            min_depth = i * 255 // layers
            max_depth = (i + 1) * 255 // layers
            
            mask = Image.eval(depth_map, lambda x: 255 if min_depth <= x < max_depth else 0)
            
            # Blur amount based on depth
            if i == layers // 2:
                # Focus plane - no blur
                continue
            else:
                blur_radius = abs(i - layers // 2) * 2
                layer = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
                
                # Composite blurred layer
                result = Image.composite(layer, result, mask)
        
        return result
    
    def _blend_colors(
        self,
        color1: Tuple[int, int, int],
        color2: Tuple[int, int, int],
        factor: float
    ) -> Tuple[int, int, int]:
        """Blend two colors together."""
        return tuple(
            int(color1[i] * (1 - factor) + color2[i] * factor)
            for i in range(3)
        )
    
    def _hsv_to_rgb(self, h: float, s: float, v: float) -> Tuple[int, int, int]:
        """Convert HSV to RGB color."""
        import colorsys
        rgb = colorsys.hsv_to_rgb(h / 360, s, v)
        return tuple(int(c * 255) for c in rgb)
    
    def generate_animated_scene(
        self,
        environment: EnvironmentType,
        time_of_day: TimeOfDay,
        weather: Weather,
        resolution: Tuple[int, int],
        style: VisualStyle,
        duration: float,
        fps: int = 30
    ) -> List[Image.Image]:
        """Generate animated scene sequence."""
        
        frames = []
        total_frames = int(duration * fps)
        
        # Initialize dynamic elements
        if weather == Weather.RAIN:
            rain_particles = asyncio.run(
                self.effects_engine.create_particle_system(
                    ParticleType.RAIN,
                    count=2000,
                    bounds=(0, 0, resolution[0], resolution[1])
                )
            )
        else:
            rain_particles = []
        
        # Generate frames
        for frame_idx in range(total_frames):
            t = frame_idx / fps
            
            # Generate base scene
            frame = self.generate_scene(
                environment, time_of_day, weather,
                resolution, style
            )
            
            # Animate dynamic elements
            if rain_particles:
                self.effects_engine.update_particles(rain_particles, 1/fps)
                self.effects_engine.render_particles(frame, rain_particles)
            
            # Add time-based animations
            # Blinking lights, moving vehicles, etc.
            self._add_frame_animations(frame, t, environment, time_of_day)
            
            frames.append(frame)
        
        return frames
    
    def _add_frame_animations(
        self,
        frame: Image.Image,
        t: float,
        environment: EnvironmentType,
        time_of_day: TimeOfDay
    ):
        """Add frame-specific animations."""
        
        draw = ImageDraw.Draw(frame)
        width, height = frame.size
        
        # Blinking lights for night scenes
        if time_of_day in [TimeOfDay.NIGHT, TimeOfDay.DUSK]:
            # City lights blinking
            if environment == EnvironmentType.URBAN:
                for _ in range(20):
                    if random.random() < 0.05:  # 5% chance to toggle
                        light_x = random.randint(0, width)
                        light_y = random.randint(height // 2, height)
                        
                        draw.ellipse(
                            [(light_x - 2, light_y - 2), (light_x + 2, light_y + 2)],
                            fill=(255, 255, 200) if int(t * 2) % 2 else (100, 100, 100)
                        )
        
        # Moving elements
        if environment == EnvironmentType.FUTURISTIC:
            # Animated hologram
            holo_y = height // 2 + int(math.sin(t * 2) * 50)
            holo_alpha = int(128 + 127 * math.sin(t * 3))
            
            draw.rectangle(
                [(width // 2 - 50, holo_y - 50), (width // 2 + 50, holo_y + 50)],
                fill=None,
                outline=(0, 200, 255, holo_alpha),
                width=2
            )