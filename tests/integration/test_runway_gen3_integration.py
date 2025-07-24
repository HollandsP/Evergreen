#!/usr/bin/env python3
"""
Test RunwayML Gen-3 Alpha Turbo API integration
Tests image-to-video generation with the latest Gen-3 Alpha Turbo model
"""
import os
import sys
import time
import json
import logging
import tempfile
import requests
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any, Optional

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class RunwayGen3Client:
    """Client for RunwayML Gen-3 Alpha Turbo API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Runway client with API key"""
        self.api_key = api_key or os.getenv('RUNWAY_API_KEY')
        if not self.api_key:
            raise ValueError("Runway API key is required")
        
        # API endpoints (based on documentation)
        self.base_url = os.getenv('RUNWAY_API_URL', 'https://api.dev.runwayml.com/v1')
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        logger.info("Initialized Runway Gen-3 Client")
    
    def test_connection(self) -> bool:
        """Test API connection and authentication"""
        try:
            # Try to get account info or models list
            response = requests.get(
                f'{self.base_url}/models',
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("Successfully connected to Runway API")
                return True
            elif response.status_code == 401:
                logger.error("Authentication failed - check API key")
                return False
            else:
                logger.warning(f"Connection test returned status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def image_to_video_gen3_turbo(
        self, 
        image_url: str,
        prompt: str,
        duration: int = 5,
        resolution: str = "1280x768",
        camera_movement: Optional[str] = None,
        motion_intensity: float = 0.5
    ) -> Dict[str, Any]:
        """
        Generate video from image using Gen-3 Alpha Turbo
        
        Args:
            image_url: URL or base64 data URI of the input image
            prompt: Text description of desired video
            duration: Video duration in seconds (5 or 10)
            resolution: Output resolution ("1280x768" or "768x1280" for vertical)
            camera_movement: Camera movement type (optional)
            motion_intensity: Intensity of motion (0.0 to 1.0)
        
        Returns:
            Generation job information
        """
        # Validate inputs
        if duration not in [5, 10]:
            raise ValueError("Duration must be 5 or 10 seconds")
        
        if resolution not in ["1280x768", "768x1280"]:
            raise ValueError("Resolution must be '1280x768' or '768x1280'")
        
        # Build request payload for Gen-3 Alpha Turbo
        payload = {
            "model": "gen3a_turbo",  # Gen-3 Alpha Turbo model
            "input": {
                "init_image": image_url,
                "text_prompt": prompt,
                "duration": duration,
                "resolution": resolution,
                "motion_intensity": motion_intensity
            }
        }
        
        # Add camera movement if specified
        if camera_movement:
            payload["input"]["camera_movement"] = camera_movement
        
        try:
            # Submit generation request
            response = requests.post(
                f'{self.base_url}/generations',
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code in [200, 201, 202]:
                job_data = response.json()
                logger.info(f"Generation job submitted: {job_data.get('id', 'unknown')}")
                return {
                    'success': True,
                    'job_id': job_data.get('id'),
                    'status': job_data.get('status', 'processing'),
                    'data': job_data
                }
            else:
                error_msg = f"API error {response.status_code}: {response.text}"
                logger.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg,
                    'status_code': response.status_code
                }
                
        except Exception as e:
            logger.error(f"Generation request failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_generation_status(self, job_id: str) -> Dict[str, Any]:
        """Check status of a generation job"""
        try:
            response = requests.get(
                f'{self.base_url}/generations/{job_id}',
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Status check failed: {response.status_code}")
                return {'status': 'error', 'error': response.text}
                
        except Exception as e:
            logger.error(f"Status check failed: {e}")
            return {'status': 'error', 'error': str(e)}

def test_runway_connection():
    """Test RunwayML API connection"""
    print("\n🔍 Testing RunwayML Gen-3 Connection...")
    
    # Check if API key is set
    api_key = os.getenv('RUNWAY_API_KEY')
    if not api_key:
        print("❌ RUNWAY_API_KEY not found in environment variables")
        print("   Please set your Runway API key:")
        print("   export RUNWAY_API_KEY='your-api-key-here'")
        return None
    
    print(f"✅ Runway API key found (ending in ...{api_key[-4:]})")
    
    try:
        client = RunwayGen3Client(api_key)
        
        # Test connection
        if client.test_connection():
            print("✅ Successfully connected to Runway API")
            return client
        else:
            print("❌ Failed to connect to Runway API")
            print("   Please verify your API key is valid and has access to Gen-3")
            return None
            
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return None

def test_gen3_turbo_image_to_video(client: RunwayGen3Client):
    """Test Gen-3 Alpha Turbo image-to-video generation"""
    print("\n🎬 Testing Gen-3 Alpha Turbo Image-to-Video...")
    
    try:
        # For testing, we'll use a simple test image
        # In production, this would be a DALL-E generated image
        test_image_url = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        
        # Test prompt
        prompt = "Camera slowly zooms out revealing a futuristic cityscape with flying vehicles"
        
        print(f"📝 Prompt: '{prompt}'")
        print("🖼️ Using test image (1x1 red pixel)")
        print("⏱️ Duration: 5 seconds")
        print("📐 Resolution: 1280x768")
        
        # Submit generation
        result = client.image_to_video_gen3_turbo(
            image_url=test_image_url,
            prompt=prompt,
            duration=5,
            resolution="1280x768",
            camera_movement="zoom_out",
            motion_intensity=0.7
        )
        
        if result['success']:
            job_id = result['job_id']
            print(f"✅ Generation job submitted!")
            print(f"   Job ID: {job_id}")
            
            # Poll for status
            print("\n⏳ Checking generation status...")
            max_attempts = 60  # 5 minutes max
            attempt = 0
            
            while attempt < max_attempts:
                time.sleep(5)  # Check every 5 seconds
                status = client.get_generation_status(job_id)
                
                current_status = status.get('status', 'unknown')
                progress = status.get('progress', 0)
                
                print(f"   Status: {current_status} ({progress}%)")
                
                if current_status == 'completed':
                    print("\n✅ Video generation completed!")
                    video_url = status.get('output', {}).get('video_url')
                    if video_url:
                        print(f"   Video URL: {video_url}")
                    return True
                    
                elif current_status in ['failed', 'error']:
                    print(f"\n❌ Generation failed: {status.get('error', 'Unknown error')}")
                    return False
                
                attempt += 1
            
            print("\n⏱️ Generation timed out after 5 minutes")
            return False
            
        else:
            print(f"❌ Failed to submit generation: {result['error']}")
            
            # Check if it's an authentication issue
            if result.get('status_code') == 401:
                print("   Authentication failed - please check your API key")
            elif result.get('status_code') == 403:
                print("   Access denied - your API key may not have access to Gen-3 Alpha Turbo")
            elif result.get('status_code') == 404:
                print("   Endpoint not found - API URL may be incorrect")
            
            return False
            
    except Exception as e:
        print(f"❌ Image-to-video test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gen3_features():
    """Test and document Gen-3 Alpha Turbo features"""
    print("\n📋 Gen-3 Alpha Turbo Features & Capabilities...")
    
    print("\n🚀 Key Features:")
    print("   - 7x faster than standard Gen-3 Alpha")
    print("   - 50% lower cost per generation")
    print("   - Supports 5s and 10s video durations")
    print("   - Can extend videos up to 34 seconds")
    print("   - Advanced camera controls")
    print("   - Vertical video support (768x1280)")
    
    print("\n📷 Camera Movement Options:")
    print("   - static: No camera movement")
    print("   - zoom_in: Camera zooms into the scene")
    print("   - zoom_out: Camera zooms out from the scene")
    print("   - pan_left: Camera pans to the left")
    print("   - pan_right: Camera pans to the right")
    print("   - tilt_up: Camera tilts upward")
    print("   - tilt_down: Camera tilts downward")
    print("   - orbit: Camera orbits around subject")
    
    print("\n🎨 Best Practices:")
    print("   - Use high-quality input images (1280x720 or higher)")
    print("   - Provide detailed, descriptive prompts")
    print("   - Specify camera movements for dynamic shots")
    print("   - Use motion intensity 0.3-0.7 for natural movement")
    print("   - Higher motion intensity (0.8-1.0) for action scenes")
    
    print("\n💰 Pricing (as of 2025):")
    print("   - Gen-3 Alpha Turbo: ~$0.01 per second")
    print("   - Standard Gen-3 Alpha: ~$0.02 per second")
    print("   - Bulk discounts available for high volume")
    
    print("\n⚡ API Limits:")
    print("   - Rate limit: Varies by tier")
    print("   - Concurrent generations: Based on plan")
    print("   - Max video duration per request: 10 seconds")
    print("   - Total extended duration: 34 seconds")

def test_runway_models_list(client: RunwayGen3Client):
    """List available Runway models"""
    print("\n📦 Testing Available Models...")
    
    try:
        response = requests.get(
            f'{client.base_url}/models',
            headers=client.headers,
            timeout=10
        )
        
        if response.status_code == 200:
            models = response.json()
            print(f"\n✅ Available Models:")
            
            if isinstance(models, list):
                for model in models:
                    print(f"\n   Model ID: {model.get('id', 'N/A')}")
                    print(f"   Name: {model.get('name', 'N/A')}")
                    print(f"   Type: {model.get('type', 'N/A')}")
                    
                    # Look for Gen-3 models
                    if 'gen3' in model.get('id', '').lower():
                        print("   ⚡ This is a Gen-3 model!")
            else:
                print("   Response format unexpected")
                print(f"   Data: {json.dumps(models, indent=2)}")
        else:
            print(f"⚠️ Could not retrieve models: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Models list test failed: {e}")

def test_api_fallback():
    """Test fallback behavior when API is unavailable"""
    print("\n🔄 Testing API Fallback Behavior...")
    
    # Import the existing Runway client to test fallback
    try:
        from src.services.runway_client import RunwayClient
        
        # Test with dummy API key
        client = RunwayClient(api_key="test_key")
        
        print("📹 Testing fallback video generation...")
        job = client.generate_video(
            prompt="A futuristic city with flying cars",
            duration=5.0,
            style="futuristic"
        )
        
        print(f"✅ Fallback generation created: {job['id']}")
        print(f"   Status: {job['status']}")
        print(f"   Is placeholder: {job.get('is_placeholder', False)}")
        
        # Test status check
        print("\n📊 Testing fallback status check...")
        status = client.get_generation_status(job['id'])
        print(f"   Status: {status['status']}")
        print(f"   Progress: {status.get('progress', 0)}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Fallback test failed: {e}")
        return False

def main():
    """Run all RunwayML Gen-3 tests"""
    print("🚀 RunwayML Gen-3 Alpha Turbo Integration Test Suite")
    print("=" * 50)
    
    # Test 1: Connection
    client = test_runway_connection()
    
    if not client:
        print("\n⚠️ Connection test failed.")
        print("   Will test fallback behavior instead...")
        
        # Test fallback
        test_api_fallback()
        
        # Still show features documentation
        test_gen3_features()
        
        return
    
    # Test 2: List available models
    test_runway_models_list(client)
    
    # Test 3: Gen-3 Alpha Turbo image-to-video
    gen3_ok = test_gen3_turbo_image_to_video(client)
    
    # Test 4: Document features
    test_gen3_features()
    
    # Test 5: Fallback behavior
    print("\n💡 Testing fallback behavior...")
    test_api_fallback()
    
    print("\n✅ RunwayML Integration Tests Complete!")
    print("=" * 50)

if __name__ == "__main__":
    main()