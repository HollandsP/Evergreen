"""
DALL-E 3 integration service for AI image generation.
Provides async image generation with smart resizing and prompt enhancement for video generation.
"""

import os
import time
import json
import logging
import asyncio
import aiohttp
import tempfile
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
from PIL import Image
import io
import base64
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


class OpenAIImageGenerator:
    """
    DALL-E 3 image generation client with video pipeline optimization.
    """
    
    # DALL-E 3 pricing per image (as of 2024)
    PRICING = {
        "1024x1024": 0.040,  # Standard quality
        "1024x1792": 0.080,  # HD quality portrait
        "1792x1024": 0.080,  # HD quality landscape
    }
    
    # Target resolution for RunwayML
    TARGET_RESOLUTION = (1280, 720)
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenAI DALL-E 3 client.
        
        Args:
            api_key: OpenAI API key (can also be set via OPENAI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.base_url = "https://api.openai.com/v1"
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        # Track costs
        self.total_cost = 0.0
        self.generation_count = 0
        
        logger.info("Initialized DALL-E 3 image generator")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(aiohttp.ClientError)
    )
    async def generate_image(
        self,
        prompt: str,
        size: str = "1792x1024",  # HD landscape for better video quality
        quality: str = "hd",
        style: str = "vivid",
        enhance_for_video: bool = True,
        n: int = 1
    ) -> Dict[str, Any]:
        """
        Generate image using DALL-E 3 with video optimization.
        
        Args:
            prompt: Text description of the image
            size: Image size (1024x1024, 1024x1792, or 1792x1024)
            quality: Quality setting (standard or hd)
            style: Style setting (vivid or natural)
            enhance_for_video: Whether to enhance prompt for video generation
            n: Number of images to generate (always 1 for DALL-E 3)
        
        Returns:
            Dictionary with generation results and metadata
        """
        start_time = time.time()
        
        # Validate inputs
        valid_sizes = ["1024x1024", "1024x1792", "1792x1024"]
        if size not in valid_sizes:
            size = "1792x1024"  # Default to landscape HD
        
        # Enhance prompt for video generation if requested
        if enhance_for_video:
            prompt = self._enhance_prompt_for_video(prompt)
        
        # Ensure prompt doesn't exceed limits (4000 chars for DALL-E 3)
        if len(prompt) > 4000:
            prompt = prompt[:3997] + "..."
        
        # Build request payload
        payload = {
            "model": "dall-e-3",
            "prompt": prompt,
            "size": size,
            "quality": quality,
            "style": style,
            "n": 1  # DALL-E 3 only supports n=1
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/images/generations",
                    headers=self.headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        
                        # Process the response
                        image_data = result['data'][0]
                        generation_time = time.time() - start_time
                        
                        # Track costs
                        cost = self.PRICING.get(size, 0.040)
                        if quality == "standard" and size == "1024x1024":
                            cost = 0.040  # Standard quality pricing
                        
                        self.total_cost += cost
                        self.generation_count += 1
                        
                        # Download and resize image for video pipeline
                        image_url = image_data['url']
                        resized_path = await self._download_and_resize_image(image_url)
                        
                        return {
                            "success": True,
                            "original_url": image_url,
                            "resized_path": resized_path,
                            "revised_prompt": image_data.get('revised_prompt', prompt),
                            "generation_time": generation_time,
                            "cost": cost,
                            "size": size,
                            "quality": quality,
                            "style": style,
                            "timestamp": datetime.now().isoformat()
                        }
                    
                    else:
                        error_data = await response.text()
                        logger.error(f"DALL-E 3 API error {response.status}: {error_data}")
                        
                        return {
                            "success": False,
                            "error": f"API error: {response.status}",
                            "details": error_data,
                            "timestamp": datetime.now().isoformat()
                        }
                        
        except asyncio.TimeoutError:
            logger.error("DALL-E 3 request timed out")
            return {
                "success": False,
                "error": "Request timed out",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"DALL-E 3 generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _download_and_resize_image(self, image_url: str) -> str:
        """
        Download image from URL and resize to target resolution for video.
        
        Args:
            image_url: URL of the generated image
        
        Returns:
            Path to resized image file
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        
                        # Open image with PIL
                        image = Image.open(io.BytesIO(image_data))
                        
                        # Convert to RGB if necessary
                        if image.mode not in ('RGB', 'RGBA'):
                            image = image.convert('RGB')
                        
                        # Resize to target resolution (1280x720)
                        # Use high-quality resampling
                        resized = image.resize(
                            self.TARGET_RESOLUTION,
                            Image.Resampling.LANCZOS
                        )
                        
                        # Save to temporary file
                        temp_file = tempfile.NamedTemporaryFile(
                            suffix='.jpg',
                            delete=False
                        )
                        resized.save(temp_file.name, 'JPEG', quality=95)
                        
                        logger.info(f"Resized image saved to {temp_file.name}")
                        return temp_file.name
                    
                    else:
                        raise Exception(f"Failed to download image: {response.status}")
                        
        except Exception as e:
            logger.error(f"Image download/resize failed: {e}")
            raise
    
    def _enhance_prompt_for_video(self, base_prompt: str) -> str:
        """
        Enhance prompt for better video generation results.
        
        Args:
            base_prompt: Original prompt
        
        Returns:
            Enhanced prompt optimized for video keyframes
        """
        # Add cinematic and motion-friendly elements
        enhancements = [
            "cinematic composition",
            "professional photography",
            "high detail",
            "sharp focus",
            "dramatic lighting",
            "wide angle shot"
        ]
        
        # Check if prompt already has style elements
        has_style = any(word in base_prompt.lower() for word in [
            'cinematic', 'style', 'shot', 'angle', 'lighting', 'composition'
        ])
        
        if not has_style:
            # Add random subset of enhancements
            import random
            selected = random.sample(enhancements, k=3)
            enhanced = f"{base_prompt}, {', '.join(selected)}"
        else:
            enhanced = base_prompt
        
        # Ensure good framing for video
        if 'shot' not in enhanced.lower():
            enhanced += ", wide establishing shot"
        
        return enhanced
    
    async def generate_batch(
        self,
        prompts: List[str],
        size: str = "1792x1024",
        quality: str = "hd",
        style: str = "vivid",
        enhance_for_video: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple images in parallel (with rate limiting).
        
        Args:
            prompts: List of prompts to generate
            size: Image size for all generations
            quality: Quality setting for all generations
            style: Style setting for all generations
            enhance_for_video: Whether to enhance prompts for video
        
        Returns:
            List of generation results
        """
        # DALL-E 3 has rate limits, so we'll process with some concurrency control
        max_concurrent = 3  # Adjust based on your tier
        results = []
        
        for i in range(0, len(prompts), max_concurrent):
            batch = prompts[i:i + max_concurrent]
            
            # Generate batch concurrently
            tasks = [
                self.generate_image(
                    prompt=prompt,
                    size=size,
                    quality=quality,
                    style=style,
                    enhance_for_video=enhance_for_video
                )
                for prompt in batch
            ]
            
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
            
            # Add delay between batches to respect rate limits
            if i + max_concurrent < len(prompts):
                await asyncio.sleep(1)  # Adjust based on your rate limits
        
        return results
    
    def create_data_uri_from_path(self, image_path: str) -> str:
        """
        Convert image file to data URI for use with other services.
        
        Args:
            image_path: Path to image file
        
        Returns:
            Data URI string
        """
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        # Encode to base64
        base64_data = base64.b64encode(image_data).decode('utf-8')
        
        return f"data:image/jpeg;base64,{base64_data}"
    
    async def generate_variations(
        self,
        image_path: str,
        n: int = 1,
        size: str = "1792x1024"
    ) -> Dict[str, Any]:
        """
        Generate variations of an existing image.
        Note: DALL-E 3 doesn't support variations, this is for DALL-E 2 compatibility.
        
        Args:
            image_path: Path to source image
            n: Number of variations
            size: Output size
        
        Returns:
            Generation results or error
        """
        logger.warning("DALL-E 3 doesn't support variations. Use DALL-E 2 for this feature.")
        return {
            "success": False,
            "error": "Variations not supported in DALL-E 3",
            "suggestion": "Generate new images with modified prompts instead"
        }
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """
        Get summary of generation costs.
        
        Returns:
            Cost summary dictionary
        """
        return {
            "total_cost": round(self.total_cost, 3),
            "generation_count": self.generation_count,
            "average_cost": round(self.total_cost / max(1, self.generation_count), 3),
            "timestamp": datetime.now().isoformat()
        }
    
    async def test_connection(self) -> bool:
        """
        Test API connection and credentials.
        
        Returns:
            True if connection successful
        """
        try:
            # Try a simple API call
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/models",
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    if response.status == 200:
                        logger.info("OpenAI API connection successful")
                        return True
                    else:
                        logger.error(f"OpenAI API connection failed: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"OpenAI API connection test failed: {e}")
            return False


# Convenience function for creating the client
def create_dalle3_client(api_key: Optional[str] = None) -> OpenAIImageGenerator:
    """
    Create and return a configured DALL-E 3 client.
    
    Args:
        api_key: Optional API key (uses env var if not provided)
    
    Returns:
        Configured OpenAIImageGenerator instance
    """
    return OpenAIImageGenerator(api_key)