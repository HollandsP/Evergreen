#!/usr/bin/env python3
"""
Integration test for RunwayML real API implementation.
Tests actual API calls to validate the integration works.
"""

import os
import sys
import time
import logging
import tempfile
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.services.runway_ml_proper import RunwayMLProperClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_runway_api_authentication():
    """Test that we can authenticate with the RunwayML API."""
    try:
        client = RunwayMLProperClient()
        
        # Test organization info endpoint
        org_info = client.get_organization_info()
        
        if org_info:
            logger.info("✅ Authentication successful!")
            logger.info(f"Organization: {org_info}")
            return True
        else:
            logger.error("❌ Authentication failed - no organization info returned")
            return False
            
    except Exception as e:
        logger.error(f"❌ Authentication failed with error: {e}")
        return False


def test_text_to_image_generation():
    """Test text-to-image generation."""
    try:
        client = RunwayMLProperClient()
        
        # Generate an image from text
        prompt = "A serene mountain landscape at sunset, cinematic quality"
        
        logger.info(f"Generating image from prompt: {prompt}")
        
        # Use the private method for testing
        result = client._generate_image_from_text(
            prompt=prompt,
            ratio="1360:768",
            model="gen4_image"
        )
        
        if result and 'id' in result:
            task_id = result['id']
            logger.info(f"✅ Image generation task created: {task_id}")
            
            # Wait for completion
            image_url = client._wait_for_task_completion(task_id, timeout=180)
            
            if image_url:
                logger.info(f"✅ Image generation completed: {image_url}")
                return True, image_url
            else:
                logger.error("❌ Image generation timed out or failed")
                return False, None
        else:
            logger.error("❌ Failed to create image generation task")
            return False, None
            
    except Exception as e:
        logger.error(f"❌ Image generation failed with error: {e}")
        return False, None


def test_image_to_video_generation():
    """Test image-to-video generation using a test image."""
    try:
        client = RunwayMLProperClient()
        
        # First generate a test image
        success, image_url = test_text_to_image_generation()
        
        if not success or not image_url:
            logger.error("❌ Cannot test video generation without image")
            return False
        
        # Generate video from the image
        prompt = "Camera slowly pans across the landscape, gentle movement"
        
        logger.info(f"Generating video from image with prompt: {prompt}")
        
        result = client.generate_video_from_image(
            image_url=image_url,
            prompt=prompt,
            duration=5,  # Short duration for testing
            model="gen3a_turbo",  # Use the more reliable model
            ratio="1280:768"
        )
        
        if result and 'id' in result:
            task_id = result['id']
            logger.info(f"✅ Video generation task created: {task_id}")
            
            # Wait for completion (longer timeout for video)
            video_url = client.wait_for_completion(task_id, max_wait_time=300)
            
            if video_url:
                logger.info(f"✅ Video generation completed: {video_url}")
                
                # Download the video for verification
                with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
                    output_path = f.name
                
                downloaded_path = client.download_video(video_url, output_path)
                
                if downloaded_path and os.path.exists(downloaded_path):
                    file_size = os.path.getsize(downloaded_path)
                    logger.info(f"✅ Video downloaded successfully: {downloaded_path} ({file_size} bytes)")
                    
                    # Move to output directory for inspection
                    output_dir = project_root / "output" / "runway_api_test"
                    output_dir.mkdir(exist_ok=True)
                    
                    final_path = output_dir / f"test_video_{int(time.time())}.mp4"
                    os.rename(downloaded_path, str(final_path))
                    
                    logger.info(f"✅ Test video saved to: {final_path}")
                    return True
                else:
                    logger.error("❌ Video download failed")
                    return False
            else:
                logger.error("❌ Video generation timed out or failed")
                return False
        else:
            logger.error("❌ Failed to create video generation task")
            return False
            
    except Exception as e:
        logger.error(f"❌ Video generation failed with error: {e}")
        return False


def test_task_status_polling():
    """Test task status polling functionality."""
    try:
        client = RunwayMLProperClient()
        
        # Create a dummy task to test status polling
        prompt = "A simple test image for status polling"
        
        result = client._generate_image_from_text(
            prompt=prompt,
            ratio="1360:768",
            model="gen4_image"
        )
        
        if result and 'id' in result:
            task_id = result['id']
            logger.info(f"Testing status polling for task: {task_id}")
            
            # Poll status a few times
            for i in range(5):
                status = client.get_task_status(task_id)
                logger.info(f"Poll {i+1}: Status = {status.get('status', 'UNKNOWN')}")
                
                if status.get('status') in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
                    break
                    
                time.sleep(3)
            
            logger.info("✅ Status polling test completed")
            return True
        else:
            logger.error("❌ Failed to create task for status testing")
            return False
            
    except Exception as e:
        logger.error(f"❌ Status polling test failed: {e}")
        return False


def main():
    """Run all RunwayML API integration tests."""
    logger.info("🚀 Starting RunwayML API Integration Tests")
    logger.info("=" * 50)
    
    # Check API key
    api_key = os.getenv('RUNWAY_API_KEY')
    if not api_key:
        logger.error("❌ RUNWAY_API_KEY environment variable not set")
        return False
    
    logger.info(f"Using API key: {api_key[:20]}...")
    
    test_results = []
    
    # Test 1: Authentication
    logger.info("\n🔐 Testing API Authentication...")
    auth_success = test_runway_api_authentication()
    test_results.append(("Authentication", auth_success))
    
    if not auth_success:
        logger.error("❌ Authentication failed, skipping other tests")
        return False
    
    # Test 2: Task Status Polling
    logger.info("\n📊 Testing Task Status Polling...")
    status_success = test_task_status_polling()
    test_results.append(("Status Polling", status_success))
    
    # Test 3: Image-to-Video Generation (Full workflow)
    logger.info("\n🎬 Testing Complete Image-to-Video Workflow...")
    video_success = test_image_to_video_generation()
    test_results.append(("Image-to-Video Generation", video_success))
    
    # Print summary
    logger.info("\n" + "=" * 50)
    logger.info("🏁 TEST SUMMARY")
    logger.info("=" * 50)
    
    all_passed = True
    for test_name, success in test_results:
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
        if not success:
            all_passed = False
    
    logger.info("=" * 50)
    
    if all_passed:
        logger.info("🎉 ALL TESTS PASSED - RunwayML API integration working!")
        return True
    else:
        logger.error("💥 SOME TESTS FAILED - Check API configuration and credentials")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)