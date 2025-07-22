"""
Comprehensive prompt library for DALL-E 3 → RunwayML workflow.

This module contains optimized prompt templates for different genres, camera movements,
and style modifiers that work well together across both DALL-E 3 image generation
and RunwayML video generation.
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import random


@dataclass
class PromptPair:
    """Paired prompts for image and video generation."""
    image_prompt: str
    video_prompt: str
    genre: str
    style: str
    camera_movement: str
    duration_range: Tuple[float, float] = (3.0, 8.0)
    moderation_safe: bool = True


# Genre-specific prompt templates optimized for "The Descent" narrative style
GENRE_PROMPTS = {
    "dystopian_cityscape": {
        "base_templates": [
            {
                "image": "Dystopian cityscape at dusk, towering concrete buildings silhouetted against a polluted orange sky, scattered neon signs casting harsh shadows, abandoned vehicles scattered on empty streets, atmospheric fog rolling between buildings, cinematic wide shot, photorealistic, dramatic lighting",
                "video": "Slow pan across dystopian cityscape, gentle camera drift revealing the scope of urban decay, subtle fog movement, flickering neon signs, abandoned atmosphere",
                "tags": ["urban", "decay", "atmospheric", "wide_shot"]
            },
            {
                "image": "Post-apocalyptic metropolitan skyline, broken glass towers reflecting dying sunlight, emergency lights blinking in the distance, smoke rising from scattered fires, desolate highways with overturned cars, cinematic composition, high detail",
                "video": "Gradual zoom out from broken skyline, revealing scale of destruction, smoke drifting slowly, emergency lights pulsing rhythmically",
                "tags": ["apocalyptic", "destruction", "scale", "zoom_out"]
            },
            {
                "image": "Abandoned corporate district, empty glass office buildings with darkened windows, debris scattered across wide plazas, overturned food carts and newspaper stands, security barriers abandoned, moody lighting, professional photography",
                "video": "Dolly shot through empty plaza, camera moving between abandoned objects, shadows shifting with clouds overhead",
                "tags": ["corporate", "abandonment", "dolly", "shadows"]
            }
        ],
        "variations": [
            "rain-soaked streets reflecting neon lights",
            "thick industrial smog obscuring distant buildings", 
            "scattered protest banners clinging to lamp posts",
            "emergency broadcast screens flickering on building facades",
            "makeshift barriers blocking major intersections"
        ]
    },
    
    "underground_facility": {
        "base_templates": [
            {
                "image": "Underground facility corridor with reinforced concrete walls, harsh fluorescent lighting casting stark shadows, industrial pipes running along the ceiling, heavy security doors with biometric scanners, sterile environment, cinematic perspective",
                "video": "Steady forward tracking shot down the corridor, fluorescent lights humming overhead, subtle camera shake suggesting underground vibrations",
                "tags": ["underground", "industrial", "tracking", "sterile"]
            },
            {
                "image": "Vast underground data center, rows of server racks stretching into darkness, blinking status lights creating patterns of red and green, thick cables snaking across the floor, emergency lighting casting an eerie glow, wide establishing shot",
                "video": "Slow glide between server racks, status lights pulsing in sequence, gentle camera movement revealing the scale of the facility",
                "tags": ["data_center", "technology", "glide", "scale"]
            },
            {
                "image": "Control room with multiple monitor walls displaying data streams, ergonomic workstations with abandoned coffee cups and personal items, emergency alert indicators blinking red, backup power providing dim illumination, professional photography",
                "video": "Pan across monitor walls showing scrolling data, alert lights blinking in rhythm, slight camera shake suggesting system instability",
                "tags": ["control_room", "monitoring", "pan", "alerts"]
            }
        ],
        "variations": [
            "condensation dripping from ventilation systems",
            "security cameras tracking with red recording lights",
            "containment warnings posted on reinforced doors",
            "emergency shutdown protocols displayed on screens",
            "biometric access panels showing denied status"
        ]
    },
    
    "corporate_interior": {
        "base_templates": [
            {
                "image": "Modern corporate office floor with open-plan workstations, floor-to-ceiling windows showing city views, ergonomic furniture arranged in precise patterns, digital displays showing company metrics, professional lighting, clean composition",
                "video": "Smooth tracking shot through the office space, natural lighting shifting as clouds pass by windows, subtle movement of papers from air conditioning",
                "tags": ["corporate", "modern", "tracking", "natural_light"]
            },
            {
                "image": "Executive boardroom with polished conference table, leather chairs arranged symmetrically, wall-mounted displays showing financial data, panoramic city view through glass walls, minimalist design, high-end photography",
                "video": "Circular dolly around the conference table, financial data updating on displays, city lights twinkling in the background",
                "tags": ["executive", "boardroom", "circular", "data"]
            },
            {
                "image": "Corporate lobby with marble floors, modern art installations, security checkpoint with metal detectors, digital welcome screens, reception desk with company logo, professional architectural photography",
                "video": "Ascending shot from lobby floor revealing the full height of the space, people moving in fast motion, security systems scanning",
                "tags": ["lobby", "marble", "ascending", "security"]
            }
        ],
        "variations": [
            "employee ID badges scattered on desks",
            "motivational posters with corporate slogans",
            "security footage playing on monitoring screens",
            "visitor management systems with access logs",
            "emergency evacuation route maps on walls"
        ]
    },
    
    "residential_area": {
        "base_templates": [
            {
                "image": "Suburban neighborhood with identical houses lined along tree-lined streets, well-maintained lawns and gardens, modern streetlights providing even illumination, children's toys scattered on front yards, peaceful atmosphere, golden hour lighting",
                "video": "Slow drive-by shot down the residential street, gentle camera movement following the curve of the road, shadows shifting as day transitions to evening",
                "tags": ["suburban", "residential", "drive_by", "golden_hour"]
            },
            {
                "image": "High-rise apartment complex with balconies showing signs of daily life, laundry hanging from lines, potted plants on railings, warm lights glowing from windows, urban residential setting, natural photography",
                "video": "Vertical tilt up the apartment building, windows lighting up as evening approaches, subtle movement of hanging laundry",
                "tags": ["apartment", "urban", "vertical", "evening"]
            },
            {
                "image": "Gated community entrance with security booth, manicured landscaping, luxury vehicles in driveways, architectural consistency across homes, premium materials and finishes, professional real estate photography",
                "video": "Smooth entry shot through the community gates, camera following the main boulevard, revealing the scale and uniformity of the development",
                "tags": ["gated", "luxury", "entry", "uniformity"]
            }
        ],
        "variations": [
            "neighborhood watch signs posted on street corners",
            "children's bicycles left on sidewalks",
            "mail trucks making evening deliveries",
            "porch lights automatically turning on at dusk",
            "security cameras mounted on house corners"
        ]
    },
    
    "natural_environment": {
        "base_templates": [
            {
                "image": "Dense forest with ancient trees towering overhead, dappled sunlight filtering through thick canopy, moss-covered ground with fallen logs, mysterious shadows between tree trunks, pristine wilderness, cinematic nature photography",
                "video": "Slow walk through the forest path, sunlight patterns shifting on the ground, gentle breeze moving branches overhead",
                "tags": ["forest", "ancient", "walk", "sunlight"]
            },
            {
                "image": "Mountain valley with snow-capped peaks in the distance, crystal clear lake reflecting the landscape, wildflowers dotting the meadow, dramatic cloud formations overhead, untouched natural beauty, wide landscape shot",
                "video": "Sweeping drone shot over the valley, clouds casting moving shadows across the landscape, water gently lapping at the shore",
                "tags": ["mountain", "valley", "drone", "clouds"]
            },
            {
                "image": "Coastal cliff overlooking turbulent ocean waters, sea spray creating misty atmosphere, rugged rock formations shaped by erosion, seabirds circling overhead, dramatic natural lighting, environmental photography",
                "video": "Waves crashing against the cliffs below, camera slowly pulling back to reveal the scale of the coastline, seabirds moving in formation",
                "tags": ["coastal", "cliff", "waves", "pull_back"]
            }
        ],
        "variations": [
            "wildlife trails winding through underbrush",
            "natural springs creating small waterfalls",
            "rock formations weathered by centuries",
            "seasonal changes affecting vegetation",
            "conservation markers protecting sensitive areas"
        ]
    },
    
    "industrial_complex": {
        "base_templates": [
            {
                "image": "Massive industrial facility with cooling towers releasing steam, complex network of pipes and machinery, warning signs posted throughout, harsh industrial lighting, workers in safety gear, gritty photojournalism style",
                "video": "Tracking shot along the industrial complex, steam billowing from towers, machinery operating with rhythmic mechanical sounds",
                "tags": ["industrial", "massive", "tracking", "steam"]
            },
            {
                "image": "Factory floor with automated assembly lines, robotic arms performing precise movements, quality control stations with digital displays, safety protocols clearly marked, modern manufacturing environment, technical photography",
                "video": "Time-lapse of assembly line operations, robotic arms moving in choreographed sequences, products moving along conveyor systems",
                "tags": ["factory", "automated", "time_lapse", "robotic"]
            },
            {
                "image": "Chemical processing plant with containment vessels, complex piping systems, hazard warning symbols, emergency response equipment, industrial safety protocols, environmental compliance features, documentary style",
                "video": "Aerial view of the processing plant, revealing the complexity of the facility layout, safety systems monitoring operations",
                "tags": ["chemical", "processing", "aerial", "safety"]
            }
        ],
        "variations": [
            "shift workers changing at designated times",
            "environmental monitoring stations collecting data",
            "transportation systems moving raw materials",
            "waste management protocols in operation",
            "emergency response teams on standby"
        ]
    }
}


# Camera movements optimized for RunwayML
CAMERA_MOVEMENTS = {
    "static_shots": {
        "locked_off": "Camera remains completely stationary, subjects move within frame",
        "subtle_breathing": "Almost imperceptible camera movement, like handheld breathing",
        "micro_adjustments": "Tiny reframing movements, professional tripod work"
    },
    
    "panning_movements": {
        "slow_pan_left": "Gentle horizontal movement from right to left, revealing new elements",
        "slow_pan_right": "Smooth horizontal movement from left to right, following action",
        "reveal_pan": "Pan that uncovers hidden elements or expands the visible area",
        "follow_pan": "Camera pans to track a moving subject across the frame",
        "environmental_pan": "Wide pan showing the full scope of a location"
    },
    
    "tilting_movements": {
        "slow_tilt_up": "Gradual vertical movement from low to high, revealing scale",
        "slow_tilt_down": "Smooth downward tilt, intimate to expansive view",
        "reveal_tilt": "Tilt that uncovers important story elements",
        "architectural_tilt": "Following the lines of buildings or structures"
    },
    
    "tracking_movements": {
        "forward_track": "Camera moves steadily forward, creating depth and immersion",
        "backward_track": "Smooth retreat revealing more of the environment",
        "lateral_track": "Side-to-side movement maintaining distance from subject",
        "arc_track": "Curved movement around a central point or subject",
        "following_track": "Camera tracks behind or alongside moving subjects"
    },
    
    "zoom_movements": {
        "slow_zoom_in": "Gradual magnification, focusing attention on details",
        "slow_zoom_out": "Smooth pullback revealing context and scale",
        "rack_focus": "Shifting focus between foreground and background elements",
        "dolly_zoom": "Counter-zoom creating vertigo or tension effect"
    },
    
    "complex_movements": {
        "orbital_movement": "Circular movement around a central subject or object",
        "rising_crane": "Upward movement combined with forward motion",
        "descending_approach": "Downward movement while moving toward subject",
        "spiral_ascent": "Combination of circular and upward movement",
        "floating_drift": "Gentle, dreamlike movement with multiple axis changes"
    },
    
    "atmospheric_movements": {
        "wind_drift": "Subtle movement suggesting environmental influences",
        "thermal_rise": "Gentle upward floating motion like heat distortion",
        "gravitational_pull": "Slow draw toward a significant story element",
        "magnetic_attraction": "Inevitable movement toward points of interest",
        "tidal_flow": "Back-and-forth movement with natural rhythm"
    }
}


# Style modifiers for consistent visual aesthetics
STYLE_MODIFIERS = {
    "photorealistic": {
        "technical": [
            "shot on RED camera with 85mm lens",
            "professional cinematography with shallow depth of field",
            "natural lighting with practical light sources",
            "high dynamic range color grading",
            "film grain texture for organic feel"
        ],
        "lighting": [
            "golden hour natural lighting",
            "dramatic chiaroscuro lighting",
            "soft diffused window light",
            "harsh industrial fluorescent lighting",
            "moody tungsten color temperature"
        ],
        "composition": [
            "rule of thirds composition",
            "leading lines drawing the eye",
            "symmetrical architectural framing",
            "asymmetrical dynamic balance",
            "foreground, midground, background layers"
        ]
    },
    
    "cinematic": {
        "mood": [
            "dystopian science fiction atmosphere",
            "psychological thriller tension",
            "corporate espionage aesthetic",
            "technological anxiety mood",
            "existential dread undertones"
        ],
        "color_grading": [
            "desaturated color palette with teal and orange accents",
            "high contrast with crushed blacks",
            "cool color temperature suggesting technology",
            "warm practical lights in cold environments",
            "monochromatic blue-green color scheme"
        ],
        "visual_style": [
            "blade runner inspired visuals",
            "minority report clean futurism",
            "ex machina minimalist tech aesthetic",
            "black mirror contemporary dystopia",
            "westworld corporate luxury design"
        ]
    },
    
    "artistic": {
        "painterly": [
            "digital painting aesthetic with soft edges",
            "impressionistic lighting with visible brushstrokes",
            "watercolor transparency effects",
            "oil painting texture and depth",
            "gouache matte finish appearance"
        ],
        "stylized": [
            "geometric art deco influences",
            "minimalist design with bold shapes",
            "vintage propaganda poster aesthetic",
            "modern graphic design elements",
            "abstract expressionist color use"
        ],
        "surreal": [
            "dreamlike distortion of familiar spaces",
            "impossible architectural geometries",
            "scale shifts creating unease",
            "temporal displacement effects",
            "psychological landscape representation"
        ]
    },
    
    "documentary": {
        "realistic": [
            "handheld camera natural movement",
            "available light photography",
            "candid unposed human moments",
            "environmental portrait style",
            "photojournalistic truthfulness"
        ],
        "observational": [
            "fly-on-the-wall perspective",
            "long lens compression for natural behavior",
            "ambient sound design priority",
            "real-time pacing without manipulation",
            "minimal intervention approach"
        ]
    },
    
    "noir": {
        "classic": [
            "high contrast black and white aesthetics",
            "venetian blind shadow patterns",
            "dramatic silhouette compositions",
            "urban nighttime lighting",
            "smoke and fog atmospheric effects"
        ],
        "modern": [
            "neo-noir color desaturation",
            "neon lights in urban darkness",
            "rain-soaked reflective surfaces",
            "corporate modernism meets classic noir",
            "digital surveillance aesthetic"
        ]
    }
}


# Scene transition prompts for multi-clip stories
TRANSITION_PROMPTS = {
    "temporal": {
        "time_passage": [
            {
                "image": "Same location showing passage of time through lighting changes, shadows moving across surfaces, subtle environmental shifts indicating hours or days passing",
                "video": "Time-lapse effect showing natural light progression, shadows rotating, environmental changes accelerated",
                "type": "time_lapse_transition"
            },
            {
                "image": "Clock or timepiece showing different time, surrounding environment subtly changed to reflect temporal progression, consistent spatial relationship",
                "video": "Focus on timepiece with background soft, time moving forward, environment slowly shifting",
                "type": "clock_transition"
            }
        ],
        "day_night": [
            {
                "image": "Identical composition during day transitioning to night, same architectural elements with different lighting, maintaining spatial continuity",
                "video": "Gradual transition from daylight to artificial lighting, natural progression of time, shadows shifting",
                "type": "day_night_cycle"
            }
        ]
    },
    
    "spatial": {
        "location_change": [
            {
                "image": "Wide establishing shot of new location, clear spatial orientation, architectural or environmental landmarks for viewer reference",
                "video": "Slow reveal of new environment, camera movement establishing spatial relationships",
                "type": "establishing_transition"
            },
            {
                "image": "Transportation element like vehicle interior, train window, or elevator, suggesting movement between locations",
                "video": "Movement through transportation medium, journey progression, destination approaching",
                "type": "journey_transition"
            }
        ],
        "scale_change": [
            {
                "image": "Same subject at dramatically different scale, maintaining visual consistency while changing perspective",
                "video": "Zoom transition revealing scale relationship, smooth magnification or reduction",
                "type": "scale_transition"
            }
        ]
    },
    
    "narrative": {
        "cause_effect": [
            {
                "image": "Visual setup showing conditions that will lead to consequences, clear causal elements arranged in frame",
                "video": "Setup of causal elements, tension building through composition and movement",
                "type": "setup_transition"
            },
            {
                "image": "Result or consequence of previous action, visual connection to previous scene through composition or lighting",
                "video": "Revelation of consequences, camera movement revealing the result of previous setup",
                "type": "payoff_transition"
            }
        ],
        "parallel_action": [
            {
                "image": "Similar composition showing simultaneous action in different location, visual rhyming through lighting or framing",
                "video": "Parallel movement patterns, visual echoes between different spaces",
                "type": "parallel_transition"
            }
        ]
    },
    
    "thematic": {
        "visual_metaphor": [
            {
                "image": "Symbolic imagery reinforcing narrative themes, metaphorical representation of story concepts",
                "video": "Symbolic movement or transformation, metaphor becoming literal through motion",
                "type": "metaphor_transition"
            }
        ],
        "emotional_shift": [
            {
                "image": "Visual representation of emotional state change, color and lighting supporting mood transition",
                "video": "Gradual shift in visual mood, lighting and movement supporting emotional progression",
                "type": "emotional_transition"
            }
        ]
    }
}


def get_prompt_by_genre(genre: str, style: str = "photorealistic") -> Optional[PromptPair]:
    """
    Get a random prompt pair for the specified genre and style.
    
    Args:
        genre: Genre key from GENRE_PROMPTS
        style: Style modifier key from STYLE_MODIFIERS
        
    Returns:
        PromptPair object or None if genre not found
    """
    if genre not in GENRE_PROMPTS:
        return None
    
    genre_data = GENRE_PROMPTS[genre]
    template = random.choice(genre_data["base_templates"])
    variation = random.choice(genre_data.get("variations", [""]))
    
    # Apply style modifiers
    style_mods = STYLE_MODIFIERS.get(style, {})
    style_elements = []
    
    for category, modifiers in style_mods.items():
        if modifiers:
            style_elements.append(random.choice(modifiers))
    
    # Construct enhanced prompts
    enhanced_image = template["image"]
    if variation:
        enhanced_image += f", {variation}"
    if style_elements:
        enhanced_image += f", {', '.join(style_elements)}"
    
    enhanced_video = template["video"]
    if style == "cinematic":
        enhanced_video += ", cinematic camera movement with professional smoothness"
    
    return PromptPair(
        image_prompt=enhanced_image,
        video_prompt=enhanced_video,
        genre=genre,
        style=style,
        camera_movement=template.get("tags", ["unknown"])[2] if len(template.get("tags", [])) > 2 else "static"
    )


def get_camera_movement(category: str, specific: str = None) -> str:
    """
    Get camera movement description for RunwayML.
    
    Args:
        category: Movement category from CAMERA_MOVEMENTS
        specific: Specific movement type (optional)
        
    Returns:
        Camera movement description
    """
    if category not in CAMERA_MOVEMENTS:
        return "static shot with minimal camera movement"
    
    movements = CAMERA_MOVEMENTS[category]
    
    if specific and specific in movements:
        return movements[specific]
    
    # Return random movement from category
    return random.choice(list(movements.values()))


def get_style_modifier(style_type: str, category: str = None) -> str:
    """
    Get style modifier for consistent visual aesthetics.
    
    Args:
        style_type: Style type from STYLE_MODIFIERS
        category: Specific category within style type
        
    Returns:
        Style modifier description
    """
    if style_type not in STYLE_MODIFIERS:
        return ""
    
    style_data = STYLE_MODIFIERS[style_type]
    
    if category and category in style_data:
        return random.choice(style_data[category])
    
    # Return random modifier from any category
    all_modifiers = []
    for cat_modifiers in style_data.values():
        all_modifiers.extend(cat_modifiers)
    
    return random.choice(all_modifiers) if all_modifiers else ""


def get_transition_prompt(transition_type: str, subtype: str = None) -> Optional[PromptPair]:
    """
    Get transition prompt pair for scene changes.
    
    Args:
        transition_type: Type of transition (temporal, spatial, narrative, thematic)
        subtype: Specific subtype of transition
        
    Returns:
        PromptPair for transition or None if not found
    """
    if transition_type not in TRANSITION_PROMPTS:
        return None
    
    transition_data = TRANSITION_PROMPTS[transition_type]
    
    if subtype and subtype in transition_data:
        template = random.choice(transition_data[subtype])
    else:
        # Get random transition from any subtype
        all_transitions = []
        for subtype_transitions in transition_data.values():
            all_transitions.extend(subtype_transitions)
        template = random.choice(all_transitions)
    
    return PromptPair(
        image_prompt=template["image"],
        video_prompt=template["video"],
        genre="transition",
        style="cinematic",
        camera_movement=template["type"]
    )


# Genre compatibility matrix for narrative flow
GENRE_COMPATIBILITY = {
    "dystopian_cityscape": ["underground_facility", "corporate_interior", "industrial_complex"],
    "underground_facility": ["dystopian_cityscape", "corporate_interior", "industrial_complex"],
    "corporate_interior": ["dystopian_cityscape", "underground_facility", "residential_area"],
    "residential_area": ["corporate_interior", "dystopian_cityscape", "natural_environment"],
    "natural_environment": ["residential_area", "industrial_complex"],
    "industrial_complex": ["dystopian_cityscape", "underground_facility", "natural_environment"]
}


def get_compatible_genre(current_genre: str) -> str:
    """
    Get a genre that flows well narratively from the current genre.
    
    Args:
        current_genre: Current scene genre
        
    Returns:
        Compatible genre for narrative flow
    """
    compatible = GENRE_COMPATIBILITY.get(current_genre, list(GENRE_PROMPTS.keys()))
    return random.choice(compatible)


# Moderation-safe content guidelines
MODERATION_GUIDELINES = {
    "avoid_terms": [
        # Violence/weapons
        "blood", "gore", "weapon", "gun", "knife", "violence", "death", "killing",
        # Explicit content
        "nude", "naked", "sexual", "erotic", "pornographic",
        # Hate speech
        "nazi", "confederate", "supremacist", "terrorist",
        # Illegal activities
        "drug", "cocaine", "heroin", "meth", "illegal"
    ],
    "safe_alternatives": {
        "destruction": "decay, abandonment, weathering, neglect",
        "conflict": "tension, unease, uncertainty, anxiety",
        "danger": "warning signs, caution barriers, emergency protocols",
        "authority": "security checkpoints, surveillance systems, access controls"
    },
    "recommended_terms": [
        "atmospheric", "moody", "cinematic", "professional", "architectural",
        "environmental", "industrial", "technological", "corporate", "urban",
        "dramatic lighting", "composition", "perspective", "depth of field"
    ]
}


def is_moderation_safe(prompt: str) -> bool:
    """
    Check if prompt is safe for content moderation.
    
    Args:
        prompt: Prompt text to check
        
    Returns:
        True if prompt appears safe for moderation
    """
    prompt_lower = prompt.lower()
    
    for term in MODERATION_GUIDELINES["avoid_terms"]:
        if term in prompt_lower:
            return False
    
    return True


def sanitize_prompt(prompt: str) -> str:
    """
    Sanitize prompt to be moderation-safe while maintaining creative intent.
    
    Args:
        prompt: Original prompt text
        
    Returns:
        Sanitized prompt text
    """
    sanitized = prompt
    
    for unsafe_term, safe_alternative in MODERATION_GUIDELINES["safe_alternatives"].items():
        if unsafe_term in sanitized.lower():
            # Replace with first safe alternative
            replacement = safe_alternative.split(", ")[0]
            sanitized = sanitized.replace(unsafe_term, replacement)
    
    return sanitized