"""
Unified pipeline manager for DALL-E 3 and RunwayML integration.
Manages the complete flow from text to image to video generation.
"""

import os
import asyncio
import logging
import tempfile
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
from pathlib import Path
import json
from enum import Enum

from .dalle3_client import OpenAIImageGenerator, create_dalle3_client
from .runway_ml_proper import RunwayMLProperClient, AsyncRunwayMLClient

logger = logging.getLogger(__name__)


class GenerationProvider(Enum):
    """Available generation providers."""
    DALLE3 = "dalle3"
    RUNWAY_IMAGE = "runway_image"
    AUTO = "auto"


class VideoGenerationMode(Enum):
    """Video generation modes."""
    IMAGE_TO_VIDEO = "image_to_video"
    TEXT_TO_VIDEO = "text_to_video"  # Future support
    AUTO = "auto"


class UnifiedPipelineManager:
    """
    Manages the complete pipeline from text to video generation.
    Integrates DALL-E 3 for image generation and RunwayML for video generation.
    """
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        runway_api_key: Optional[str] = None,
        default_provider: GenerationProvider = GenerationProvider.AUTO
    ):
        """
        Initialize the unified pipeline manager.
        
        Args:
            openai_api_key: OpenAI API key for DALL-E 3
            runway_api_key: RunwayML API key
            default_provider: Default image generation provider
        """
        # Initialize clients
        self.dalle3_client = None
        self.runway_client = None
        self.async_runway_client = None
        
        # Try to initialize DALL-E 3
        try:
            self.dalle3_client = create_dalle3_client(openai_api_key)
            logger.info("DALL-E 3 client initialized")
        except Exception as e:
            logger.warning(f"DALL-E 3 initialization failed: {e}")
        
        # Try to initialize RunwayML
        try:
            self.runway_client = RunwayMLProperClient(runway_api_key)
            self.async_runway_client = AsyncRunwayMLClient(runway_api_key)
            logger.info("RunwayML client initialized")
        except Exception as e:
            logger.warning(f"RunwayML initialization failed: {e}")
        
        self.default_provider = default_provider
        
        # Track pipeline metrics
        self.pipeline_runs = 0
        self.total_cost = 0.0
        self.success_count = 0
        self.failure_count = 0
        
        # Cache for generated assets
        self.asset_cache = {}
    
    async def generate_video_clip(
        self,
        prompt: str,
        duration: int = 10,
        image_provider: Optional[GenerationProvider] = None,
        video_model: str = "gen4_turbo",
        video_ratio: str = "1280:720",
        image_size: str = "1792x1024",
        image_quality: str = "hd",
        image_style: str = "vivid",
        enhance_prompt: bool = True,
        camera_movement: Optional[str] = None,
        lighting: Optional[str] = None,
        mood: Optional[str] = None,
        style: str = "cinematic",
        seed: Optional[int] = None,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a complete video clip from text prompt.
        
        Args:
            prompt: Text description of the desired video
            duration: Video duration in seconds (5 or 10)
            image_provider: Provider for initial image generation
            video_model: RunwayML model to use
            video_ratio: Video aspect ratio
            image_size: DALL-E 3 image size
            image_quality: DALL-E 3 quality setting
            image_style: DALL-E 3 style setting
            enhance_prompt: Whether to enhance prompts for better results
            camera_movement: Camera movement description
            lighting: Lighting setup
            mood: Emotional tone
            style: Visual style
            seed: Random seed for reproducibility
            output_path: Optional path to save the final video
        
        Returns:
            Dictionary with generation results, URLs, and metadata
        """
        start_time = datetime.now()
        pipeline_result = {
            "success": False,
            "prompt": prompt,
            "start_time": start_time.isoformat(),
            "steps": [],
            "cost": 0.0
        }
        
        try:
            # Step 1: Generate initial image
            logger.info("Step 1: Generating initial image")
            image_result = await self._generate_initial_image(
                prompt=prompt,
                provider=image_provider or self.default_provider,
                size=image_size,
                quality=image_quality,
                style=image_style,
                enhance_for_video=enhance_prompt,
                video_style=style,
                camera_movement=camera_movement,
                lighting=lighting,
                mood=mood
            )
            
            pipeline_result["steps"].append({
                "name": "image_generation",
                "status": "success" if image_result["success"] else "failed",
                "duration": image_result.get("generation_time", 0),
                "result": image_result
            })
            
            if not image_result["success"]:
                raise Exception(f"Image generation failed: {image_result.get('error')}")
            
            # Update cost
            pipeline_result["cost"] += image_result.get("cost", 0)
            
            # Step 2: Generate video from image
            logger.info("Step 2: Generating video from image")
            
            # Prepare video prompt
            video_prompt = self._prepare_video_prompt(
                base_prompt=prompt,
                style=style,
                camera_movement=camera_movement,
                lighting=lighting,
                mood=mood
            )
            
            # Create data URI from resized image
            image_path = image_result.get("resized_path")
            if not image_path:
                raise Exception("No resized image path available")
            
            image_data_uri = self.runway_client.create_data_uri_from_image(image_path)
            
            # Generate video
            video_task = await self.async_runway_client.generate_video_from_image(
                image_url=image_data_uri,
                prompt=video_prompt,
                duration=duration,
                model=video_model,
                ratio=video_ratio,
                seed=seed
            )
            
            if not video_task or not video_task.get("id"):
                raise Exception(f"Video generation failed to start: {video_task}")
            
            logger.info(f"Video generation task created: {video_task['id']}")
            
            # Step 3: Wait for video completion
            logger.info("Step 3: Waiting for video generation")
            video_url = await self.async_runway_client.wait_for_completion(
                video_task["id"],
                max_wait_time=600,
                poll_interval=5
            )
            
            if not video_url:
                raise Exception("Video generation failed or timed out")
            
            pipeline_result["steps"].append({
                "name": "video_generation",
                "status": "success",
                "task_id": video_task["id"],
                "video_url": video_url
            })
            
            # Step 4: Download video if output path specified
            final_path = None
            if output_path:
                logger.info("Step 4: Downloading video")
                final_path = await self.async_runway_client.download_video(
                    video_url,
                    output_path
                )
                
                pipeline_result["steps"].append({
                    "name": "video_download",
                    "status": "success" if final_path else "failed",
                    "output_path": final_path
                })
            
            # Calculate total time
            end_time = datetime.now()
            total_duration = (end_time - start_time).total_seconds()
            
            # Update pipeline result
            pipeline_result.update({
                "success": True,
                "end_time": end_time.isoformat(),
                "total_duration": total_duration,
                "image_url": image_result.get("original_url"),
                "image_path": image_result.get("resized_path"),
                "video_url": video_url,
                "video_path": final_path,
                "revised_prompt": image_result.get("revised_prompt", prompt),
                "video_prompt": video_prompt
            })
            
            # Update metrics
            self.pipeline_runs += 1
            self.success_count += 1
            self.total_cost += pipeline_result["cost"]
            
            # Clean up temporary image file
            try:
                if image_path and os.path.exists(image_path):
                    os.unlink(image_path)
            except Exception as e:
                logger.warning(f"Failed to clean up temp image: {e}")
            
            return pipeline_result
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            
            # Update failure metrics
            self.pipeline_runs += 1
            self.failure_count += 1
            
            pipeline_result.update({
                "success": False,
                "error": str(e),
                "end_time": datetime.now().isoformat()
            })
            
            return pipeline_result
    
    async def _generate_initial_image(
        self,
        prompt: str,
        provider: GenerationProvider,
        size: str,
        quality: str,
        style: str,
        enhance_for_video: bool,
        video_style: str,
        camera_movement: Optional[str],
        lighting: Optional[str],
        mood: Optional[str]
    ) -> Dict[str, Any]:
        """
        Generate initial image using selected provider.
        
        Args:
            prompt: Base prompt
            provider: Image generation provider
            size: Image size
            quality: Quality setting
            style: Style setting
            enhance_for_video: Whether to enhance prompt
            video_style: Video style for prompt enhancement
            camera_movement: Camera movement
            lighting: Lighting description
            mood: Mood description
        
        Returns:
            Image generation result
        """
        # Determine which provider to use
        if provider == GenerationProvider.AUTO:
            # Use DALL-E 3 if available, otherwise RunwayML
            if self.dalle3_client:
                provider = GenerationProvider.DALLE3
            elif self.runway_client:
                provider = GenerationProvider.RUNWAY_IMAGE
            else:
                raise Exception("No image generation provider available")
        
        # Generate with selected provider
        if provider == GenerationProvider.DALLE3:
            if not self.dalle3_client:
                raise Exception("DALL-E 3 client not initialized")
            
            # Enhance prompt with video-specific elements
            if enhance_for_video:
                enhanced_prompt = self._enhance_prompt_for_dalle3(
                    prompt, video_style, camera_movement, lighting, mood
                )
            else:
                enhanced_prompt = prompt
            
            return await self.dalle3_client.generate_image(
                prompt=enhanced_prompt,
                size=size,
                quality=quality,
                style=style,
                enhance_for_video=enhance_for_video
            )
        
        elif provider == GenerationProvider.RUNWAY_IMAGE:
            if not self.runway_client:
                raise Exception("RunwayML client not initialized")
            
            # Use RunwayML's image generation
            # Note: This is a placeholder - RunwayML primarily does video
            raise NotImplementedError("RunwayML image generation not yet implemented")
        
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    def _enhance_prompt_for_dalle3(
        self,
        base_prompt: str,
        style: str,
        camera_movement: Optional[str],
        lighting: Optional[str],
        mood: Optional[str]
    ) -> str:
        """
        Enhance prompt specifically for DALL-E 3 to create video-ready images.
        
        Args:
            base_prompt: Original prompt
            style: Visual style
            camera_movement: Camera movement hint
            lighting: Lighting setup
            mood: Emotional tone
        
        Returns:
            Enhanced prompt
        """
        parts = [base_prompt]
        
        # Add style elements
        style_mappings = {
            "cinematic": "cinematic composition, film still, professional cinematography",
            "noir": "film noir style, dramatic shadows, high contrast black and white",
            "cyberpunk": "cyberpunk aesthetic, neon lights, futuristic cityscape",
            "horror": "horror atmosphere, dark and ominous, unsettling",
            "documentary": "documentary photography, realistic, natural lighting",
            "anime": "anime art style, vibrant colors, dynamic composition",
            "retro": "retro 1980s aesthetic, synthwave colors, nostalgic"
        }
        
        if style in style_mappings:
            parts.append(style_mappings[style])
        
        # Add camera hints (for composition)
        if camera_movement:
            if "zoom" in camera_movement.lower():
                parts.append("centered composition suitable for zoom")
            elif "pan" in camera_movement.lower():
                parts.append("wide panoramic composition")
            elif "tilt" in camera_movement.lower():
                parts.append("vertical composition with headroom")
        
        # Add lighting
        if lighting:
            parts.append(f"{lighting} lighting")
        
        # Add mood
        if mood:
            parts.append(f"{mood} atmosphere")
        
        # Always add video-friendly elements
        parts.extend([
            "high detail",
            "sharp focus",
            "professional quality",
            "16:9 aspect ratio composition"
        ])
        
        return ", ".join(parts)
    
    def _prepare_video_prompt(
        self,
        base_prompt: str,
        style: str,
        camera_movement: Optional[str],
        lighting: Optional[str],
        mood: Optional[str]
    ) -> str:
        """
        Prepare prompt specifically for RunwayML video generation.
        
        Args:
            base_prompt: Original prompt
            style: Visual style
            camera_movement: Camera movement
            lighting: Lighting setup
            mood: Emotional tone
        
        Returns:
            Video-optimized prompt
        """
        if self.runway_client:
            return self.runway_client.generate_cinematic_prompt(
                base_description=base_prompt,
                style=style,
                camera_movement=camera_movement,
                lighting=lighting,
                mood=mood
            )
        else:
            # Fallback prompt preparation
            parts = [base_prompt]
            
            if camera_movement:
                parts.append(f"{camera_movement} camera movement")
            
            if style != "cinematic":
                parts.append(f"{style} style")
            
            if lighting:
                parts.append(f"{lighting} lighting")
            
            if mood:
                parts.append(f"{mood} mood")
            
            full_prompt = ", ".join(parts)
            
            # Truncate to RunwayML's limit
            if len(full_prompt) > 1000:
                full_prompt = full_prompt[:997] + "..."
            
            return full_prompt
    
    async def generate_batch_clips(
        self,
        prompts: List[str],
        duration: int = 10,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple video clips in an optimized batch process.
        
        Args:
            prompts: List of prompts to generate
            duration: Duration for all videos
            **kwargs: Additional arguments passed to generate_video_clip
        
        Returns:
            List of generation results
        """
        results = []
        
        # First, generate all images in parallel (with rate limiting)
        logger.info(f"Generating {len(prompts)} images in batch")
        
        if self.dalle3_client:
            image_results = await self.dalle3_client.generate_batch(
                prompts=prompts,
                size=kwargs.get("image_size", "1792x1024"),
                quality=kwargs.get("image_quality", "hd"),
                style=kwargs.get("image_style", "vivid"),
                enhance_for_video=kwargs.get("enhance_prompt", True)
            )
        else:
            # Fallback to sequential generation
            image_results = []
            for prompt in prompts:
                result = await self._generate_initial_image(
                    prompt=prompt,
                    provider=kwargs.get("image_provider", self.default_provider),
                    size=kwargs.get("image_size", "1792x1024"),
                    quality=kwargs.get("image_quality", "hd"),
                    style=kwargs.get("image_style", "vivid"),
                    enhance_for_video=kwargs.get("enhance_prompt", True),
                    video_style=kwargs.get("style", "cinematic"),
                    camera_movement=kwargs.get("camera_movement"),
                    lighting=kwargs.get("lighting"),
                    mood=kwargs.get("mood")
                )
                image_results.append(result)
        
        # Then generate videos from successful images
        for i, (prompt, image_result) in enumerate(zip(prompts, image_results)):
            if image_result.get("success"):
                logger.info(f"Generating video {i+1}/{len(prompts)}")
                
                # Create a modified kwargs with the image result
                clip_kwargs = kwargs.copy()
                clip_kwargs["_pregenerated_image"] = image_result
                
                clip_result = await self._generate_video_from_image_result(
                    prompt=prompt,
                    image_result=image_result,
                    duration=duration,
                    **clip_kwargs
                )
                
                results.append(clip_result)
            else:
                # Add failed result
                results.append({
                    "success": False,
                    "prompt": prompt,
                    "error": f"Image generation failed: {image_result.get('error')}",
                    "image_result": image_result
                })
        
        return results
    
    async def _generate_video_from_image_result(
        self,
        prompt: str,
        image_result: Dict[str, Any],
        duration: int,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate video from pre-generated image result.
        
        Args:
            prompt: Original prompt
            image_result: Image generation result
            duration: Video duration
            **kwargs: Additional video generation parameters
        
        Returns:
            Video generation result
        """
        # This is a simplified version of generate_video_clip that skips image generation
        # Implementation would follow similar pattern but start from step 2
        # For brevity, using the main method with the pre-generated image
        
        # Note: This is a placeholder for optimization
        # In a real implementation, we'd extract the video generation logic
        # to avoid code duplication
        
        return await self.generate_video_clip(
            prompt=prompt,
            duration=duration,
            **kwargs
        )
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """
        Get pipeline execution statistics.
        
        Returns:
            Statistics dictionary
        """
        success_rate = (
            self.success_count / self.pipeline_runs * 100
            if self.pipeline_runs > 0
            else 0
        )
        
        stats = {
            "total_runs": self.pipeline_runs,
            "successful_runs": self.success_count,
            "failed_runs": self.failure_count,
            "success_rate": round(success_rate, 2),
            "total_cost": round(self.total_cost, 3),
            "average_cost_per_run": round(
                self.total_cost / max(1, self.pipeline_runs), 3
            )
        }
        
        # Add provider-specific stats
        if self.dalle3_client:
            stats["dalle3_stats"] = self.dalle3_client.get_cost_summary()
        
        if self.runway_client:
            stats["runway_stats"] = {
                "org_info": self.runway_client.get_organization_info()
            }
        
        return stats
    
    async def test_pipeline(self) -> Dict[str, Any]:
        """
        Test the pipeline with a simple example.
        
        Returns:
            Test results
        """
        test_prompt = "A serene mountain landscape at sunset with dramatic clouds"
        
        logger.info("Testing pipeline components...")
        
        results = {
            "dalle3_available": False,
            "runway_available": False,
            "pipeline_test": None
        }
        
        # Test DALL-E 3
        if self.dalle3_client:
            try:
                dalle3_ok = await self.dalle3_client.test_connection()
                results["dalle3_available"] = dalle3_ok
            except Exception as e:
                logger.error(f"DALL-E 3 test failed: {e}")
        
        # Test RunwayML
        if self.runway_client:
            try:
                org_info = self.runway_client.get_organization_info()
                results["runway_available"] = bool(org_info)
                results["runway_org_info"] = org_info
            except Exception as e:
                logger.error(f"RunwayML test failed: {e}")
        
        # Test full pipeline if both are available
        if results["dalle3_available"] and results["runway_available"]:
            logger.info("Running full pipeline test...")
            
            try:
                pipeline_result = await self.generate_video_clip(
                    prompt=test_prompt,
                    duration=5,  # Short duration for testing
                    image_size="1024x1024",  # Smaller size for testing
                    image_quality="standard",  # Lower quality for testing
                    enhance_prompt=True
                )
                
                results["pipeline_test"] = {
                    "success": pipeline_result["success"],
                    "duration": pipeline_result.get("total_duration"),
                    "cost": pipeline_result.get("cost"),
                    "error": pipeline_result.get("error")
                }
                
            except Exception as e:
                results["pipeline_test"] = {
                    "success": False,
                    "error": str(e)
                }
        
        return results


# Convenience function for creating the unified pipeline
def create_unified_pipeline(
    openai_api_key: Optional[str] = None,
    runway_api_key: Optional[str] = None,
    default_provider: GenerationProvider = GenerationProvider.AUTO
) -> UnifiedPipelineManager:
    """
    Create and return a configured unified pipeline manager.
    
    Args:
        openai_api_key: OpenAI API key
        runway_api_key: RunwayML API key
        default_provider: Default image provider
    
    Returns:
        Configured UnifiedPipelineManager instance
    """
    return UnifiedPipelineManager(
        openai_api_key=openai_api_key,
        runway_api_key=runway_api_key,
        default_provider=default_provider
    )