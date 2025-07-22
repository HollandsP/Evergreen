"""
PromptOptimizer class for enhancing prompts for DALL-E 3 image generation
and creating matching video prompts for RunwayML.

This module ensures consistency between image and video generation while
optimizing for quality and avoiding moderation triggers.
"""

import re
import random
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from .dalle3_runway_prompts import (
    PromptPair, STYLE_MODIFIERS, CAMERA_MOVEMENTS, 
    MODERATION_GUIDELINES, is_moderation_safe, sanitize_prompt
)


@dataclass
class OptimizationConfig:
    """Configuration for prompt optimization."""
    enhance_for_video: bool = True
    target_style: str = "photorealistic"
    camera_movement_preference: str = "smooth"
    duration_range: Tuple[float, float] = (3.0, 8.0)
    resolution: str = "1792x1024"  # HD landscape for DALL-E 3
    ensure_moderation_safe: bool = True
    add_technical_specs: bool = True
    enhance_lighting: bool = True
    add_composition_guides: bool = True
    consistency_mode: bool = True  # Ensure image/video consistency


@dataclass
class OptimizationResult:
    """Result of prompt optimization."""
    original_prompt: str
    optimized_image_prompt: str
    optimized_video_prompt: str
    style_applied: str
    camera_movement: str
    estimated_duration: float
    moderation_safe: bool
    optimization_notes: List[str] = field(default_factory=list)
    technical_specs: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class PromptOptimizer:
    """
    Optimizes prompts for DALL-E 3 and creates matching RunwayML video prompts.
    
    Features:
    - Prompt enhancement for better image quality
    - Consistent image/video prompt pairs
    - Moderation safety checks
    - Style and technical optimization
    - Camera movement integration
    """
    
    def __init__(self, config: OptimizationConfig = None):
        """
        Initialize PromptOptimizer.
        
        Args:
            config: Configuration for optimization behavior
        """
        self.config = config or OptimizationConfig()
        self.optimization_history: List[OptimizationResult] = []
        
        # Precompiled regex patterns for efficiency
        self._technical_pattern = re.compile(r'\b(shot|camera|lens|lighting|composition)\b', re.IGNORECASE)
        self._style_pattern = re.compile(r'\b(cinematic|photorealistic|artistic|dramatic)\b', re.IGNORECASE)
        self._movement_pattern = re.compile(r'\b(pan|tilt|zoom|track|dolly|crane)\b', re.IGNORECASE)
    
    def optimize_prompt(self, base_prompt: str, target_style: str = None) -> OptimizationResult:
        """
        Optimize a base prompt for both DALL-E 3 and RunwayML.
        
        Args:
            base_prompt: Original prompt text
            target_style: Override default style from config
            
        Returns:
            OptimizationResult with enhanced prompts and metadata
        """
        style = target_style or self.config.target_style
        notes = []
        
        # Step 1: Moderation safety check
        if self.config.ensure_moderation_safe:
            if not is_moderation_safe(base_prompt):
                base_prompt = sanitize_prompt(base_prompt)
                notes.append("Applied moderation safety sanitization")
        
        # Step 2: Enhance image prompt for DALL-E 3
        image_prompt = self._enhance_image_prompt(base_prompt, style, notes)
        
        # Step 3: Create matching video prompt for RunwayML
        video_prompt = self._create_video_prompt(base_prompt, image_prompt, style, notes)
        
        # Step 4: Select appropriate camera movement
        camera_movement = self._select_camera_movement(base_prompt, style)
        
        # Step 5: Estimate duration
        duration = self._estimate_duration(base_prompt, camera_movement)
        
        # Create result
        result = OptimizationResult(
            original_prompt=base_prompt,
            optimized_image_prompt=image_prompt,
            optimized_video_prompt=video_prompt,
            style_applied=style,
            camera_movement=camera_movement,
            estimated_duration=duration,
            moderation_safe=is_moderation_safe(image_prompt) and is_moderation_safe(video_prompt),
            optimization_notes=notes,
            technical_specs={
                "resolution": self.config.resolution,
                "target_style": style,
                "camera_preference": self.config.camera_movement_preference,
                "duration_range": self.config.duration_range
            }
        )
        
        # Store in history
        self.optimization_history.append(result)
        
        return result
    
    def _enhance_image_prompt(self, base_prompt: str, style: str, notes: List[str]) -> str:
        """
        Enhance prompt specifically for DALL-E 3 image generation.
        
        Args:
            base_prompt: Original prompt
            style: Target visual style
            notes: List to append optimization notes
            
        Returns:
            Enhanced image prompt
        """
        enhanced = base_prompt.strip()
        
        # Add style-specific enhancements
        if style in STYLE_MODIFIERS:
            style_data = STYLE_MODIFIERS[style]
            
            # Add technical specifications if requested
            if self.config.add_technical_specs and "technical" in style_data:
                if not self._technical_pattern.search(enhanced):
                    tech_spec = random.choice(style_data["technical"])
                    enhanced += f", {tech_spec}"
                    notes.append(f"Added technical specification: {tech_spec}")
            
            # Add lighting enhancements
            if self.config.enhance_lighting and "lighting" in style_data:
                if "lighting" not in enhanced.lower():
                    lighting = random.choice(style_data["lighting"])
                    enhanced += f", {lighting}"
                    notes.append(f"Added lighting enhancement: {lighting}")
            
            # Add composition guides
            if self.config.add_composition_guides and "composition" in style_data:
                if not re.search(r'\b(composition|framing|shot)\b', enhanced, re.IGNORECASE):
                    composition = random.choice(style_data["composition"])
                    enhanced += f", {composition}"
                    notes.append(f"Added composition guide: {composition}")
        
        # Ensure video-optimized elements if enabled
        if self.config.enhance_for_video:
            video_elements = [
                "wide establishing shot",
                "cinematic composition", 
                "professional photography",
                "high detail",
                "sharp focus"
            ]
            
            # Add elements that aren't already present
            for element in video_elements:
                if not any(word in enhanced.lower() for word in element.split()):
                    enhanced += f", {element}"
                    notes.append(f"Added video optimization: {element}")
                    break  # Only add one to avoid over-enhancement
        
        # Ensure prompt length is within DALL-E 3 limits (4000 chars)
        if len(enhanced) > 3900:
            enhanced = enhanced[:3897] + "..."
            notes.append("Truncated prompt to stay within DALL-E 3 character limit")
        
        return enhanced
    
    def _create_video_prompt(self, base_prompt: str, image_prompt: str, style: str, notes: List[str]) -> str:
        """
        Create video prompt for RunwayML based on image prompt.
        
        Args:
            base_prompt: Original prompt
            image_prompt: Enhanced image prompt
            style: Target visual style
            notes: List to append optimization notes
            
        Returns:
            Video motion prompt for RunwayML
        """
        # Extract key visual elements from image prompt
        key_elements = self._extract_key_elements(image_prompt)
        
        # Determine appropriate motion based on scene content
        motion_type = self._analyze_motion_potential(base_prompt, key_elements)
        
        # Build video prompt focusing on movement and cinematography
        video_prompt_parts = []
        
        # Add camera movement
        camera_movement = self._get_camera_movement_description(base_prompt)
        video_prompt_parts.append(camera_movement)
        
        # Add environmental motion based on scene
        environmental_motion = self._get_environmental_motion(key_elements)
        if environmental_motion:
            video_prompt_parts.append(environmental_motion)
        
        # Add style-specific motion elements
        if style == "cinematic":
            video_prompt_parts.append("professional cinematic camera movement")
        elif style == "documentary":
            video_prompt_parts.append("natural handheld camera movement")
        elif style == "artistic":
            video_prompt_parts.append("creative camera work with artistic flair")
        
        # Ensure consistency with image
        if self.config.consistency_mode:
            consistency_elements = self._ensure_visual_consistency(image_prompt)
            video_prompt_parts.extend(consistency_elements)
        
        video_prompt = ", ".join(video_prompt_parts)
        notes.append(f"Created video prompt with motion type: {motion_type}")
        
        return video_prompt
    
    def _extract_key_elements(self, image_prompt: str) -> List[str]:
        """Extract key visual elements from image prompt."""
        elements = []
        
        # Environment types
        environments = ["cityscape", "interior", "office", "facility", "landscape", "forest", "mountain", "ocean"]
        for env in environments:
            if env in image_prompt.lower():
                elements.append(f"environment:{env}")
        
        # Lighting conditions
        lighting = ["golden hour", "dusk", "night", "fluorescent", "natural", "dramatic"]
        for light in lighting:
            if light in image_prompt.lower():
                elements.append(f"lighting:{light}")
        
        # Architectural elements
        architecture = ["building", "tower", "structure", "bridge", "corridor", "room"]
        for arch in architecture:
            if arch in image_prompt.lower():
                elements.append(f"architecture:{arch}")
        
        # Atmospheric elements
        atmosphere = ["fog", "mist", "smoke", "rain", "clouds", "steam"]
        for atmo in atmosphere:
            if atmo in image_prompt.lower():
                elements.append(f"atmosphere:{atmo}")
        
        return elements
    
    def _analyze_motion_potential(self, base_prompt: str, key_elements: List[str]) -> str:
        """Analyze what type of motion would work best for the scene."""
        prompt_lower = base_prompt.lower()
        
        # Static scenes - minimal movement
        if any(word in prompt_lower for word in ["abandoned", "empty", "still", "quiet", "frozen"]):
            return "static_with_atmosphere"
        
        # Dynamic scenes - more movement
        if any(word in prompt_lower for word in ["bustling", "active", "moving", "flowing", "dynamic"]):
            return "dynamic_movement"
        
        # Architectural scenes - structural movement
        if any(f"architecture:{arch}" in str(key_elements) for arch in ["building", "tower", "structure"]):
            return "architectural_reveal"
        
        # Environmental scenes - natural movement
        if any(f"environment:{env}" in str(key_elements) for env in ["landscape", "forest", "mountain", "ocean"]):
            return "environmental_flow"
        
        # Default to atmospheric
        return "atmospheric_movement"
    
    def _get_camera_movement_description(self, base_prompt: str) -> str:
        """Get appropriate camera movement description based on scene."""
        prompt_lower = base_prompt.lower()
        
        # Determine best camera movement category
        if "interior" in prompt_lower or "room" in prompt_lower:
            category = "tracking_movements"
        elif "cityscape" in prompt_lower or "landscape" in prompt_lower:
            category = "panning_movements"
        elif "building" in prompt_lower or "tower" in prompt_lower:
            category = "tilting_movements"
        elif "corridor" in prompt_lower or "path" in prompt_lower:
            category = "tracking_movements"
        else:
            category = "atmospheric_movements"
        
        # Get movement from category
        if category in CAMERA_MOVEMENTS:
            movements = list(CAMERA_MOVEMENTS[category].values())
            return random.choice(movements)
        
        return "smooth camera movement revealing the scene"
    
    def _get_environmental_motion(self, key_elements: List[str]) -> Optional[str]:
        """Get environmental motion based on scene elements."""
        element_str = " ".join(key_elements).lower()
        
        if "atmosphere:fog" in element_str or "atmosphere:mist" in element_str:
            return "fog drifting slowly across the scene"
        elif "atmosphere:smoke" in element_str:
            return "smoke rising and dispersing naturally"
        elif "atmosphere:clouds" in element_str:
            return "clouds moving slowly across the sky"
        elif "lighting:golden hour" in element_str:
            return "shadows shifting as light changes"
        elif "environment:ocean" in element_str:
            return "waves moving rhythmically in the background"
        elif "environment:forest" in element_str:
            return "leaves rustling gently in the breeze"
        elif "lighting:fluorescent" in element_str:
            return "fluorescent lights humming with slight flicker"
        
        return None
    
    def _ensure_visual_consistency(self, image_prompt: str) -> List[str]:
        """Ensure video maintains visual consistency with image."""
        consistency_elements = []
        
        # Preserve lighting consistency
        if "golden hour" in image_prompt.lower():
            consistency_elements.append("maintaining golden hour lighting throughout")
        elif "dramatic lighting" in image_prompt.lower():
            consistency_elements.append("preserving dramatic lighting contrasts")
        elif "fluorescent" in image_prompt.lower():
            consistency_elements.append("consistent harsh fluorescent illumination")
        
        # Preserve atmospheric consistency
        if "fog" in image_prompt.lower() or "mist" in image_prompt.lower():
            consistency_elements.append("atmospheric haze remaining consistent")
        elif "smoke" in image_prompt.lower():
            consistency_elements.append("smoke effects maintaining density")
        
        # Preserve color consistency
        if "desaturated" in image_prompt.lower():
            consistency_elements.append("maintaining desaturated color palette")
        elif "monochromatic" in image_prompt.lower():
            consistency_elements.append("preserving monochromatic color scheme")
        
        return consistency_elements
    
    def _select_camera_movement(self, base_prompt: str, style: str) -> str:
        """Select appropriate camera movement for the scene."""
        prompt_lower = base_prompt.lower()
        
        # Map content to movement preferences
        if "abandoned" in prompt_lower or "empty" in prompt_lower:
            return "slow_explore"
        elif "facility" in prompt_lower or "corridor" in prompt_lower:
            return "forward_track"
        elif "cityscape" in prompt_lower or "skyline" in prompt_lower:
            return "reveal_pan"
        elif "interior" in prompt_lower or "room" in prompt_lower:
            return "orbital_movement"
        else:
            return "atmospheric_drift"
    
    def _estimate_duration(self, base_prompt: str, camera_movement: str) -> float:
        """Estimate appropriate duration for the video."""
        base_duration = sum(self.config.duration_range) / 2  # Average of range
        
        # Adjust based on scene complexity
        prompt_lower = base_prompt.lower()
        
        if "complex" in prompt_lower or "detailed" in prompt_lower:
            return min(base_duration + 2.0, self.config.duration_range[1])
        elif "simple" in prompt_lower or "minimal" in prompt_lower:
            return max(base_duration - 1.0, self.config.duration_range[0])
        
        # Adjust based on camera movement
        if "slow" in camera_movement or "gradual" in camera_movement:
            return min(base_duration + 1.0, self.config.duration_range[1])
        elif "quick" in camera_movement or "fast" in camera_movement:
            return max(base_duration - 1.0, self.config.duration_range[0])
        
        return base_duration
    
    def create_prompt_sequence(self, base_prompts: List[str], narrative_flow: bool = True) -> List[OptimizationResult]:
        """
        Create a sequence of optimized prompts for multi-scene narratives.
        
        Args:
            base_prompts: List of base prompts for each scene
            narrative_flow: Whether to optimize for narrative consistency
            
        Returns:
            List of OptimizationResult objects for the sequence
        """
        results = []
        
        for i, prompt in enumerate(base_prompts):
            # For narrative flow, adjust style consistency
            if narrative_flow and i > 0:
                # Use same style as previous scene for consistency
                previous_style = results[-1].style_applied
                result = self.optimize_prompt(prompt, target_style=previous_style)
            else:
                result = self.optimize_prompt(prompt)
            
            results.append(result)
        
        return results
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """
        Get statistics about optimization performance.
        
        Returns:
            Dictionary with optimization statistics
        """
        if not self.optimization_history:
            return {"total_optimizations": 0}
        
        total = len(self.optimization_history)
        moderation_safe_count = sum(1 for r in self.optimization_history if r.moderation_safe)
        avg_duration = sum(r.estimated_duration for r in self.optimization_history) / total
        
        style_distribution = {}
        camera_distribution = {}
        
        for result in self.optimization_history:
            style = result.style_applied
            camera = result.camera_movement
            
            style_distribution[style] = style_distribution.get(style, 0) + 1
            camera_distribution[camera] = camera_distribution.get(camera, 0) + 1
        
        return {
            "total_optimizations": total,
            "moderation_safe_rate": moderation_safe_count / total,
            "average_duration": avg_duration,
            "style_distribution": style_distribution,
            "camera_movement_distribution": camera_distribution,
            "most_common_style": max(style_distribution, key=style_distribution.get),
            "most_common_camera": max(camera_distribution, key=camera_distribution.get)
        }
    
    def export_prompts_for_api(self, results: List[OptimizationResult]) -> Dict[str, Any]:
        """
        Export optimization results in format suitable for API calls.
        
        Args:
            results: List of OptimizationResult objects
            
        Returns:
            Dictionary formatted for API integration
        """
        exported = {
            "dalle3_prompts": [],
            "runway_prompts": [],
            "metadata": {
                "total_scenes": len(results),
                "total_estimated_duration": sum(r.estimated_duration for r in results),
                "sequence_id": f"seq_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "optimization_config": {
                    "style": self.config.target_style,
                    "resolution": self.config.resolution,
                    "camera_preference": self.config.camera_movement_preference,
                    "moderation_safe": self.config.ensure_moderation_safe
                }
            }
        }
        
        for i, result in enumerate(results):
            # DALL-E 3 format
            dalle3_item = {
                "scene_id": i,
                "prompt": result.optimized_image_prompt,
                "size": self.config.resolution,
                "quality": "hd",
                "style": "vivid" if "dramatic" in result.optimized_image_prompt else "natural"
            }
            exported["dalle3_prompts"].append(dalle3_item)
            
            # RunwayML format
            runway_item = {
                "scene_id": i,
                "text_prompt": result.optimized_video_prompt,
                "duration": result.estimated_duration,
                "camera_movement": result.camera_movement,
                "style": result.style_applied
            }
            exported["runway_prompts"].append(runway_item)
        
        return exported