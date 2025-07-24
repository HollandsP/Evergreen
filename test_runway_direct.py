#!/usr/bin/env python3
"""
Direct test of RunwayML API integration without heavy dependencies.
"""

import os
import requests
import json
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_runway_api_direct():
    """Test RunwayML API directly without importing heavy modules."""
    
    api_key = os.getenv('RUNWAY_API_KEY')
    if not api_key:
        logger.error("❌ RUNWAY_API_KEY environment variable not set")
        return False
    
    logger.info(f"🔑 Using API key: {api_key[:20]}...")
    
    # API configuration
    base_url = "https://api.dev.runwayml.com"
    api_version = "2024-11-06"
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'X-Runway-Version': api_version,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    # Test 1: Organization info (authentication test)
    logger.info("🔐 Testing authentication...")
    try:
        response = requests.get(
            f"{base_url}/v1/organization",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            org_info = response.json()
            logger.info("✅ Authentication successful!")
            logger.info(f"Organization info: {json.dumps(org_info, indent=2)}")
        else:
            logger.error(f"❌ Authentication failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Authentication request failed: {e}")
        return False
    
    # Test 2: Text-to-image generation
    logger.info("\n🎨 Testing text-to-image generation...")
    try:
        payload = {
            "promptText": "A beautiful mountain landscape at sunset, cinematic quality",
            "model": "gen4_image",
            "ratio": "1360:768"
        }
        
        response = requests.post(
            f"{base_url}/v1/text_to_image",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code in [200, 202]:
            result = response.json()
            task_id = result.get('id')
            logger.info(f"✅ Image generation task created: {task_id}")
            
            # Check status a few times
            for i in range(10):
                status_response = requests.get(
                    f"{base_url}/v1/tasks/{task_id}",
                    headers=headers,
                    timeout=10
                )
                
                if status_response.status_code == 200:
                    status = status_response.json()
                    current_status = status.get('status')
                    progress = status.get('progress', 0)
                    
                    logger.info(f"Poll {i+1}: Status = {current_status}, Progress = {progress}%")
                    
                    if current_status == 'SUCCEEDED':
                        output = status.get('output', [])
                        if output:
                            image_url = output[0]
                            logger.info(f"✅ Image generation completed: {image_url}")
                            return test_image_to_video(image_url, headers, base_url)
                        break
                    elif current_status == 'FAILED':
                        failure_reason = status.get('failure', 'Unknown error')
                        logger.error(f"❌ Image generation failed: {failure_reason}")
                        return False
                    
                    time.sleep(5)
                else:
                    logger.error(f"❌ Status check failed: {status_response.status_code}")
                    
            logger.error("❌ Image generation timed out")
            return False
        else:
            logger.error(f"❌ Image generation request failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Image generation failed: {e}")
        return False


def test_image_to_video(image_url, headers, base_url):
    """Test image-to-video generation."""
    logger.info("\n🎬 Testing image-to-video generation...")
    
    try:
        payload = {
            "promptImage": image_url,
            "promptText": "Camera slowly pans across the landscape, gentle movement",
            "model": "gen3a_turbo",
            "ratio": "1280:768",
            "duration": 5
        }
        
        response = requests.post(
            f"{base_url}/v1/image_to_video",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code in [200, 202]:
            result = response.json()
            task_id = result.get('id')
            logger.info(f"✅ Video generation task created: {task_id}")
            
            # Check status (longer wait for video)
            for i in range(30):  # Up to 15 minutes
                status_response = requests.get(
                    f"{base_url}/v1/tasks/{task_id}",
                    headers=headers,
                    timeout=10
                )
                
                if status_response.status_code == 200:
                    status = status_response.json()
                    current_status = status.get('status')
                    progress = status.get('progress', 0)
                    
                    logger.info(f"Poll {i+1}: Status = {current_status}, Progress = {progress}%")
                    
                    if current_status == 'SUCCEEDED':
                        output = status.get('output', [])
                        if output:
                            video_url = output[0]
                            logger.info(f"✅ Video generation completed: {video_url}")
                            
                            # Download the video
                            video_response = requests.get(video_url, stream=True, timeout=60)
                            if video_response.status_code == 200:
                                output_path = f"output/runway_test_video_{int(time.time())}.mp4"
                                os.makedirs("output", exist_ok=True)
                                
                                with open(output_path, 'wb') as f:
                                    for chunk in video_response.iter_content(chunk_size=8192):
                                        f.write(chunk)
                                
                                file_size = os.path.getsize(output_path)
                                logger.info(f"✅ Video downloaded: {output_path} ({file_size} bytes)")
                                return True
                            else:
                                logger.error("❌ Video download failed")
                                return False
                        break
                    elif current_status == 'FAILED':
                        failure_reason = status.get('failure', 'Unknown error')
                        logger.error(f"❌ Video generation failed: {failure_reason}")
                        return False
                    
                    time.sleep(30)  # Wait 30 seconds between polls
                else:
                    logger.error(f"❌ Status check failed: {status_response.status_code}")
                    
            logger.error("❌ Video generation timed out")
            return False
        else:
            logger.error(f"❌ Video generation request failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Video generation failed: {e}")
        return False


if __name__ == "__main__":
    logger.info("🚀 Starting RunwayML API Direct Test")
    logger.info("=" * 50)
    
    success = test_runway_api_direct()
    
    logger.info("\n" + "=" * 50)
    if success:
        logger.info("🎉 ALL TESTS PASSED - RunwayML API is working!")
    else:
        logger.error("💥 TESTS FAILED - Check API configuration")
    logger.info("=" * 50)