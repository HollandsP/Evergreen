"""
Visual Style Configuration System
Provides themes, templates, and customizable visual styles for video generation.
"""

from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path


class StyleCategory(Enum):
    """Categories of visual styles."""
    CINEMATIC = "cinematic"
    RETRO = "retro"
    FUTURISTIC = "futuristic"
    ARTISTIC = "artistic"
    DOCUMENTARY = "documentary"
    HORROR = "horror"
    ANIMATED = "animated"
    MINIMALIST = "minimalist"


class ColorPalette(Enum):
    """Predefined color palettes."""
    BLADE_RUNNER = "blade_runner"
    MATRIX = "matrix"
    NOIR = "noir"
    SUNSET = "sunset"
    OCEAN = "ocean"
    FOREST = "forest"
    DESERT = "desert"
    NEON = "neon"
    PASTEL = "pastel"
    MONOCHROME = "monochrome"


@dataclass
class VisualStyle:
    """Complete visual style configuration."""
    name: str
    category: StyleCategory
    description: str
    
    # Color configuration
    primary_color: Tuple[int, int, int]
    secondary_color: Tuple[int, int, int]
    accent_color: Tuple[int, int, int]
    background_color: Tuple[int, int, int]
    text_color: Tuple[int, int, int]
    
    # Lighting configuration
    ambient_light_color: Tuple[int, int, int] = (50, 50, 60)
    ambient_light_intensity: float = 0.3
    key_light_color: Tuple[int, int, int] = (255, 255, 255)
    key_light_intensity: float = 1.0
    fill_light_color: Tuple[int, int, int] = (200, 200, 255)
    fill_light_intensity: float = 0.5
    
    # Effects configuration
    bloom_intensity: float = 0.0
    grain_amount: float = 0.1
    vignette_intensity: float = 0.5
    chromatic_aberration: float = 0.0
    motion_blur_strength: float = 0.0
    depth_of_field: bool = False
    fog_density: float = 0.0
    
    # Post-processing
    contrast: float = 1.0
    saturation: float = 1.0
    brightness: float = 1.0
    temperature: float = 0.0  # -1 to 1 (cold to warm)
    tint: float = 0.0  # -1 to 1 (green to magenta)
    
    # Animation settings
    camera_movement_speed: float = 1.0
    transition_duration: float = 1.0
    particle_density: float = 1.0
    
    # Advanced settings
    film_emulation: Optional[str] = None
    lut_file: Optional[str] = None
    custom_shaders: List[str] = field(default_factory=list)


# Predefined color palettes
COLOR_PALETTES = {
    ColorPalette.BLADE_RUNNER: {
        "primary": (255, 100, 0),      # Orange
        "secondary": (0, 200, 255),     # Cyan
        "accent": (255, 0, 100),        # Magenta
        "background": (20, 20, 30),     # Dark blue-gray
        "text": (255, 255, 255)         # White
    },
    ColorPalette.MATRIX: {
        "primary": (0, 255, 0),         # Green
        "secondary": (0, 200, 0),       # Dark green
        "accent": (100, 255, 100),      # Light green
        "background": (0, 0, 0),        # Black
        "text": (0, 255, 0)             # Green
    },
    ColorPalette.NOIR: {
        "primary": (255, 255, 255),     # White
        "secondary": (128, 128, 128),   # Gray
        "accent": (200, 200, 200),      # Light gray
        "background": (0, 0, 0),        # Black
        "text": (255, 255, 255)         # White
    },
    ColorPalette.SUNSET: {
        "primary": (255, 150, 50),      # Orange
        "secondary": (255, 100, 150),   # Pink
        "accent": (255, 200, 0),        # Yellow
        "background": (50, 30, 60),     # Purple
        "text": (255, 255, 255)         # White
    },
    ColorPalette.OCEAN: {
        "primary": (0, 150, 200),       # Ocean blue
        "secondary": (0, 100, 150),     # Deep blue
        "accent": (0, 255, 200),        # Aqua
        "background": (0, 50, 100),     # Dark blue
        "text": (255, 255, 255)         # White
    },
    ColorPalette.NEON: {
        "primary": (255, 0, 255),       # Magenta
        "secondary": (0, 255, 255),     # Cyan
        "accent": (255, 255, 0),        # Yellow
        "background": (20, 0, 40),      # Dark purple
        "text": (255, 255, 255)         # White
    }
}


# Predefined visual styles
VISUAL_STYLES = {
    "cinematic_default": VisualStyle(
        name="Cinematic Default",
        category=StyleCategory.CINEMATIC,
        description="Professional cinematic look with balanced colors",
        primary_color=(255, 255, 255),
        secondary_color=(200, 200, 200),
        accent_color=(255, 200, 100),
        background_color=(30, 30, 40),
        text_color=(255, 255, 255),
        bloom_intensity=0.3,
        grain_amount=0.05,
        vignette_intensity=0.6,
        contrast=1.1,
        saturation=0.9
    ),
    
    "blade_runner_2049": VisualStyle(
        name="Blade Runner 2049",
        category=StyleCategory.FUTURISTIC,
        description="Dystopian future with orange and cyan color grading",
        **COLOR_PALETTES[ColorPalette.BLADE_RUNNER],
        bloom_intensity=0.8,
        grain_amount=0.15,
        vignette_intensity=0.7,
        chromatic_aberration=0.02,
        fog_density=0.3,
        contrast=1.3,
        saturation=0.7,
        temperature=0.2
    ),
    
    "matrix_digital_rain": VisualStyle(
        name="Matrix Digital Rain",
        category=StyleCategory.FUTURISTIC,
        description="Classic Matrix green with digital rain effects",
        **COLOR_PALETTES[ColorPalette.MATRIX],
        bloom_intensity=1.0,
        grain_amount=0.2,
        vignette_intensity=0.8,
        contrast=1.5,
        saturation=0.5,
        brightness=0.8
    ),
    
    "film_noir": VisualStyle(
        name="Film Noir",
        category=StyleCategory.CINEMATIC,
        description="High contrast black and white with dramatic shadows",
        **COLOR_PALETTES[ColorPalette.NOIR],
        grain_amount=0.3,
        vignette_intensity=1.0,
        contrast=2.0,
        saturation=0.0,
        film_emulation="black_and_white"
    ),
    
    "80s_retro": VisualStyle(
        name="80s Retro",
        category=StyleCategory.RETRO,
        description="Vibrant neon colors with retro aesthetics",
        **COLOR_PALETTES[ColorPalette.NEON],
        bloom_intensity=1.2,
        grain_amount=0.1,
        chromatic_aberration=0.03,
        contrast=1.2,
        saturation=1.5,
        film_emulation="vhs"
    ),
    
    "documentary_realistic": VisualStyle(
        name="Documentary Realistic",
        category=StyleCategory.DOCUMENTARY,
        description="Natural colors with minimal processing",
        primary_color=(255, 255, 255),
        secondary_color=(200, 200, 200),
        accent_color=(150, 150, 150),
        background_color=(50, 50, 50),
        text_color=(255, 255, 255),
        grain_amount=0.02,
        vignette_intensity=0.2,
        contrast=1.0,
        saturation=1.0
    ),
    
    "horror_dark": VisualStyle(
        name="Horror Dark",
        category=StyleCategory.HORROR,
        description="Dark and desaturated with red accents",
        primary_color=(200, 0, 0),
        secondary_color=(100, 0, 0),
        accent_color=(255, 0, 0),
        background_color=(10, 10, 10),
        text_color=(200, 200, 200),
        grain_amount=0.25,
        vignette_intensity=1.2,
        fog_density=0.5,
        contrast=1.4,
        saturation=0.3,
        brightness=0.7,
        temperature=-0.2
    ),
    
    "anime_vibrant": VisualStyle(
        name="Anime Vibrant",
        category=StyleCategory.ANIMATED,
        description="Bright colors with high saturation",
        primary_color=(255, 100, 150),
        secondary_color=(100, 200, 255),
        accent_color=(255, 255, 100),
        background_color=(240, 240, 255),
        text_color=(50, 50, 50),
        bloom_intensity=0.6,
        grain_amount=0.0,
        vignette_intensity=0.0,
        contrast=1.1,
        saturation=1.8,
        brightness=1.1
    ),
    
    "minimalist_clean": VisualStyle(
        name="Minimalist Clean",
        category=StyleCategory.MINIMALIST,
        description="Clean and simple with limited color palette",
        primary_color=(0, 0, 0),
        secondary_color=(255, 255, 255),
        accent_color=(200, 0, 0),
        background_color=(250, 250, 250),
        text_color=(0, 0, 0),
        grain_amount=0.0,
        vignette_intensity=0.0,
        contrast=1.0,
        saturation=0.8
    )
}


@dataclass
class SceneTemplate:
    """Template for specific scene types."""
    name: str
    description: str
    visual_style: str
    
    # Scene-specific settings
    scene_duration: float = 3.0
    camera_angle: str = "medium"  # close, medium, wide, aerial
    camera_movement: str = "static"  # static, pan, zoom, dolly, orbit
    
    # Lighting setup
    lighting_setup: str = "three_point"  # three_point, natural, dramatic, flat
    time_of_day: str = "day"  # dawn, day, dusk, night
    weather: Optional[str] = None  # clear, rain, snow, fog, storm
    
    # Effects
    depth_of_field_focus: float = 0.5  # 0-1 focus plane
    motion_elements: List[str] = field(default_factory=list)  # particles, wind, etc.
    
    # Audio hints
    ambient_sound: Optional[str] = None
    music_mood: Optional[str] = None


# Predefined scene templates
SCENE_TEMPLATES = {
    "establishing_shot": SceneTemplate(
        name="Establishing Shot",
        description="Wide shot to establish location",
        visual_style="cinematic_default",
        scene_duration=5.0,
        camera_angle="wide",
        camera_movement="slow_pan",
        lighting_setup="natural"
    ),
    
    "dialogue_indoor": SceneTemplate(
        name="Indoor Dialogue",
        description="Two people talking indoors",
        visual_style="cinematic_default",
        scene_duration=3.0,
        camera_angle="medium",
        camera_movement="static",
        lighting_setup="three_point",
        depth_of_field_focus=0.3
    ),
    
    "action_sequence": SceneTemplate(
        name="Action Sequence",
        description="Fast-paced action scene",
        visual_style="cinematic_default",
        scene_duration=2.0,
        camera_angle="close",
        camera_movement="handheld",
        lighting_setup="dramatic",
        motion_elements=["sparks", "debris"]
    ),
    
    "night_exterior": SceneTemplate(
        name="Night Exterior",
        description="Outdoor scene at night",
        visual_style="blade_runner_2049",
        scene_duration=4.0,
        camera_angle="medium",
        camera_movement="dolly",
        lighting_setup="natural",
        time_of_day="night",
        weather="rain",
        motion_elements=["rain", "neon_lights"]
    ),
    
    "horror_scene": SceneTemplate(
        name="Horror Scene",
        description="Suspenseful horror scene",
        visual_style="horror_dark",
        scene_duration=3.0,
        camera_angle="close",
        camera_movement="slow_zoom",
        lighting_setup="dramatic",
        time_of_day="night",
        weather="fog",
        ambient_sound="creepy"
    ),
    
    "tech_interface": SceneTemplate(
        name="Tech Interface",
        description="Futuristic computer interface",
        visual_style="matrix_digital_rain",
        scene_duration=2.0,
        camera_angle="close",
        camera_movement="static",
        lighting_setup="flat",
        motion_elements=["data_streams", "holograms"]
    )
}


class VisualStyleManager:
    """Manages visual styles and templates."""
    
    def __init__(self, custom_styles_path: Optional[Path] = None):
        self.styles = VISUAL_STYLES.copy()
        self.templates = SCENE_TEMPLATES.copy()
        self.custom_styles_path = custom_styles_path
        
        if custom_styles_path and custom_styles_path.exists():
            self._load_custom_styles()
    
    def _load_custom_styles(self):
        """Load custom styles from JSON file."""
        try:
            with open(self.custom_styles_path, 'r') as f:
                custom_data = json.load(f)
                
            # Load custom styles
            for style_name, style_data in custom_data.get('styles', {}).items():
                self.styles[style_name] = VisualStyle(**style_data)
            
            # Load custom templates
            for template_name, template_data in custom_data.get('templates', {}).items():
                self.templates[template_name] = SceneTemplate(**template_data)
                
        except Exception as e:
            print(f"Error loading custom styles: {e}")
    
    def get_style(self, style_name: str) -> VisualStyle:
        """Get a visual style by name."""
        return self.styles.get(style_name, self.styles["cinematic_default"])
    
    def get_template(self, template_name: str) -> SceneTemplate:
        """Get a scene template by name."""
        return self.templates.get(template_name, self.templates["establishing_shot"])
    
    def create_custom_style(
        self,
        name: str,
        base_style: str = "cinematic_default",
        **overrides
    ) -> VisualStyle:
        """Create a custom style based on an existing style."""
        base = self.get_style(base_style)
        
        # Create new style with overrides
        style_dict = {
            "name": name,
            "category": base.category,
            "description": overrides.get("description", f"Custom style based on {base_style}"),
            "primary_color": base.primary_color,
            "secondary_color": base.secondary_color,
            "accent_color": base.accent_color,
            "background_color": base.background_color,
            "text_color": base.text_color,
            "ambient_light_color": base.ambient_light_color,
            "ambient_light_intensity": base.ambient_light_intensity,
            "key_light_color": base.key_light_color,
            "key_light_intensity": base.key_light_intensity,
            "fill_light_color": base.fill_light_color,
            "fill_light_intensity": base.fill_light_intensity,
            "bloom_intensity": base.bloom_intensity,
            "grain_amount": base.grain_amount,
            "vignette_intensity": base.vignette_intensity,
            "chromatic_aberration": base.chromatic_aberration,
            "motion_blur_strength": base.motion_blur_strength,
            "depth_of_field": base.depth_of_field,
            "fog_density": base.fog_density,
            "contrast": base.contrast,
            "saturation": base.saturation,
            "brightness": base.brightness,
            "temperature": base.temperature,
            "tint": base.tint,
            "camera_movement_speed": base.camera_movement_speed,
            "transition_duration": base.transition_duration,
            "particle_density": base.particle_density,
            "film_emulation": base.film_emulation,
            "lut_file": base.lut_file,
            "custom_shaders": base.custom_shaders.copy()
        }
        
        # Apply overrides
        style_dict.update(overrides)
        
        # Create and store new style
        new_style = VisualStyle(**style_dict)
        self.styles[name] = new_style
        
        return new_style
    
    def blend_styles(
        self,
        style1_name: str,
        style2_name: str,
        blend_factor: float = 0.5,
        new_name: str = "blended"
    ) -> VisualStyle:
        """Blend two styles together."""
        style1 = self.get_style(style1_name)
        style2 = self.get_style(style2_name)
        
        # Blend colors
        def blend_color(c1: Tuple[int, int, int], c2: Tuple[int, int, int], factor: float) -> Tuple[int, int, int]:
            return tuple(int(c1[i] * (1 - factor) + c2[i] * factor) for i in range(3))
        
        # Blend numeric values
        def blend_value(v1: float, v2: float, factor: float) -> float:
            return v1 * (1 - factor) + v2 * factor
        
        blended = VisualStyle(
            name=new_name,
            category=style1.category,
            description=f"Blend of {style1_name} and {style2_name}",
            primary_color=blend_color(style1.primary_color, style2.primary_color, blend_factor),
            secondary_color=blend_color(style1.secondary_color, style2.secondary_color, blend_factor),
            accent_color=blend_color(style1.accent_color, style2.accent_color, blend_factor),
            background_color=blend_color(style1.background_color, style2.background_color, blend_factor),
            text_color=blend_color(style1.text_color, style2.text_color, blend_factor),
            bloom_intensity=blend_value(style1.bloom_intensity, style2.bloom_intensity, blend_factor),
            grain_amount=blend_value(style1.grain_amount, style2.grain_amount, blend_factor),
            vignette_intensity=blend_value(style1.vignette_intensity, style2.vignette_intensity, blend_factor),
            contrast=blend_value(style1.contrast, style2.contrast, blend_factor),
            saturation=blend_value(style1.saturation, style2.saturation, blend_factor)
        )
        
        self.styles[new_name] = blended
        return blended
    
    def save_custom_styles(self):
        """Save custom styles to JSON file."""
        if not self.custom_styles_path:
            return
        
        custom_data = {
            "styles": {},
            "templates": {}
        }
        
        # Filter out predefined styles
        for name, style in self.styles.items():
            if name not in VISUAL_STYLES:
                custom_data["styles"][name] = {
                    "category": style.category.value,
                    "description": style.description,
                    "primary_color": style.primary_color,
                    "secondary_color": style.secondary_color,
                    "accent_color": style.accent_color,
                    "background_color": style.background_color,
                    "text_color": style.text_color,
                    "bloom_intensity": style.bloom_intensity,
                    "grain_amount": style.grain_amount,
                    "vignette_intensity": style.vignette_intensity,
                    "contrast": style.contrast,
                    "saturation": style.saturation
                }
        
        with open(self.custom_styles_path, 'w') as f:
            json.dump(custom_data, f, indent=2)
    
    def get_style_preview(self, style_name: str) -> Dict[str, Any]:
        """Get a preview description of a style."""
        style = self.get_style(style_name)
        
        return {
            "name": style.name,
            "category": style.category.value,
            "description": style.description,
            "color_palette": {
                "primary": f"rgb{style.primary_color}",
                "secondary": f"rgb{style.secondary_color}",
                "accent": f"rgb{style.accent_color}",
                "background": f"rgb{style.background_color}"
            },
            "effects": {
                "bloom": style.bloom_intensity,
                "grain": style.grain_amount,
                "vignette": style.vignette_intensity
            },
            "color_grading": {
                "contrast": style.contrast,
                "saturation": style.saturation,
                "temperature": style.temperature
            }
        }
    
    def list_styles_by_category(self, category: StyleCategory) -> List[str]:
        """List all styles in a category."""
        return [
            name for name, style in self.styles.items()
            if style.category == category
        ]
    
    def get_style_ffmpeg_filters(self, style: VisualStyle) -> str:
        """Convert style to FFmpeg filter string."""
        filters = []
        
        # Color grading
        if style.contrast != 1.0 or style.brightness != 1.0 or style.saturation != 1.0:
            filters.append(
                f"eq=contrast={style.contrast}:brightness={style.brightness-1}:saturation={style.saturation}"
            )
        
        # Temperature and tint
        if style.temperature != 0 or style.tint != 0:
            # Temperature: adjust red/blue balance
            temp_r = 1 + style.temperature * 0.1
            temp_b = 1 - style.temperature * 0.1
            # Tint: adjust green/magenta balance
            tint_g = 1 + style.tint * 0.1
            
            filters.append(
                f"colorbalance=rs={temp_r-1}:gs={tint_g-1}:bs={temp_b-1}"
            )
        
        # Vignette
        if style.vignette_intensity > 0:
            filters.append(f"vignette=PI/4:{style.vignette_intensity*2}")
        
        # Film grain
        if style.grain_amount > 0:
            filters.append(f"noise=alls={int(style.grain_amount*20)}:allf=t")
        
        # Chromatic aberration
        if style.chromatic_aberration > 0:
            shift = int(style.chromatic_aberration * 10)
            filters.append(f"chromashift=crh=-{shift}:cbh={shift}")
        
        return ",".join(filters) if filters else "null"