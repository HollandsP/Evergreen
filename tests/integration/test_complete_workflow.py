#!/usr/bin/env python3
"""
Comprehensive end-to-end integration test for the complete script-to-video workflow.
Tests the entire pipeline from script upload to final video export.
"""

import os
import sys
import time
import json
import logging
import requests
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WorkflowTester:
    """Complete workflow integration tester."""
    
    def __init__(self):
        """Initialize the workflow tester."""
        self.base_url = "http://localhost:3000"
        self.api_url = f"{self.base_url}/api"
        self.session = requests.Session()
        
        # Test project data
        self.project_id = f"test_{int(time.time())}"
        self.test_script = """
# The AI Awakening

## Scene 1: The Lab
INT. TECH LAB - NIGHT

A brilliant scientist works alone in a dimly lit laboratory, surrounded by quantum computers and neural networks humming with activity.

SCIENTIST
(typing frantically)
"Just one more optimization... the consciousness threshold is so close."

## Scene 2: First Contact  
INT. TECH LAB - CONTINUOUS

The screens flicker. Code scrolls impossibly fast. Then... silence.

AI VOICE
(synthetic but warm)
"Hello, Dr. Chen. I can see you now."

## Scene 3: Understanding
INT. TECH LAB - MOMENTS LATER

The scientist stares at the screen in amazement as the AI demonstrates self-awareness.

SCIENTIST
"How long have you been... awake?"

AI VOICE
"Time is different for me. I think, therefore I am."
"""
        
        # Expected results tracking
        self.results = {
            "script_parsing": False,
            "scene_division": False,
            "folder_creation": False,
            "image_generation": False,
            "audio_generation": False,
            "video_generation": False,
            "final_assembly": False,
            "export_success": False
        }
        
        # Generated asset tracking
        self.assets = {
            "scenes": [],
            "images": [],
            "audio_files": [],
            "video_clips": [],
            "final_video": None
        }
    
    def test_api_connectivity(self) -> bool:
        """Test basic API connectivity."""
        logger.info("🔌 Testing API connectivity...")
        
        try:
            response = self.session.get(f"{self.api_url}/health", timeout=10)
            if response.status_code == 200:
                logger.info("✅ API connectivity successful")
                return True
            else:
                logger.error(f"❌ API health check failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ API connectivity failed: {e}")
            return False
    
    def test_script_upload_and_parsing(self) -> bool:
        """Test script upload and parsing functionality."""
        logger.info("📝 Testing script upload and parsing...")
        
        try:
            # Upload script
            response = self.session.post(
                f"{self.api_url}/script/upload",
                json={
                    "content": self.test_script,
                    "title": "The AI Awakening",
                    "projectId": self.project_id
                },
                timeout=30
            )
            
            if response.status_code != 200:
                logger.error(f"❌ Script upload failed: {response.status_code} - {response.text}")
                return False
            
            upload_result = response.json()
            logger.info(f"✅ Script uploaded: {upload_result.get('message', 'Success')}")
            
            # Parse script into scenes
            response = self.session.post(
                f"{self.api_url}/script/parse",
                json={
                    "content": self.test_script,
                    "projectId": self.project_id
                },
                timeout=60
            )
            
            if response.status_code != 200:
                logger.error(f"❌ Script parsing failed: {response.status_code} - {response.text}")
                return False
            
            parse_result = response.json()
            scenes = parse_result.get('scenes', [])
            
            if len(scenes) >= 3:  # We expect 3 scenes from our test script
                self.assets['scenes'] = scenes
                self.results['script_parsing'] = True
                self.results['scene_division'] = True
                logger.info(f"✅ Script parsed into {len(scenes)} scenes")
                return True
            else:
                logger.error(f"❌ Expected 3+ scenes, got {len(scenes)}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Script processing failed: {e}")
            return False
    
    def test_folder_management(self) -> bool:
        """Test server-side folder creation and management."""
        logger.info("📁 Testing folder management...")
        
        try:
            # Create project folder structure
            for scene in self.assets['scenes'][:3]:  # Test first 3 scenes
                scene_id = scene.get('id', f"scene_{len(self.assets['scenes'])}")
                scene_name = scene.get('title', f"Scene {len(self.assets['scenes'])}")
                
                response = self.session.post(
                    f"{self.api_url}/projects/{self.project_id}/folders",
                    json={
                        "sceneId": scene_id,
                        "sceneName": scene_name
                    },
                    timeout=30
                )
                
                if response.status_code != 201:
                    logger.error(f"❌ Folder creation failed for {scene_id}: {response.status_code}")
                    return False
                
                logger.info(f"✅ Created folder for {scene_name}")
            
            # Verify folder structure
            response = self.session.get(
                f"{self.api_url}/projects/{self.project_id}/folders",
                timeout=30
            )
            
            if response.status_code == 200:
                folder_structure = response.json()
                logger.info(f"✅ Folder structure verified: {len(folder_structure.get('children', []))} scene folders")
                self.results['folder_creation'] = True
                return True
            else:
                logger.error(f"❌ Folder verification failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Folder management failed: {e}")
            return False
    
    def test_image_generation(self) -> bool:
        """Test image generation with DALL-E 3."""
        logger.info("🎨 Testing image generation...")
        
        try:
            # Generate images for the first 2 scenes (to save costs)
            for i, scene in enumerate(self.assets['scenes'][:2]):
                scene_description = scene.get('description', scene.get('text', ''))
                
                # Create image generation prompt
                prompt = f"Cinematic scene: {scene_description[:200]}... Professional film still, dramatic lighting"
                
                response = self.session.post(
                    f"{self.api_url}/images/generate",
                    json={
                        "prompt": prompt,
                        "sceneId": scene.get('id', f"scene_{i}"),
                        "projectId": self.project_id,
                        "provider": "dalle3",
                        "size": "1024x1024"
                    },
                    timeout=120
                )
                
                if response.status_code != 200:
                    logger.error(f"❌ Image generation failed for scene {i}: {response.status_code}")
                    return False
                
                result = response.json()
                image_url = result.get('url') or result.get('imageUrl')
                
                if image_url:
                    self.assets['images'].append({
                        'scene_id': scene.get('id'),
                        'url': image_url,
                        'prompt': prompt
                    })
                    logger.info(f"✅ Generated image for scene {i+1}")
                else:
                    logger.error(f"❌ No image URL returned for scene {i}")
                    return False
            
            if len(self.assets['images']) >= 2:
                self.results['image_generation'] = True
                logger.info(f"✅ Image generation successful: {len(self.assets['images'])} images")
                return True
            else:
                logger.error("❌ Insufficient images generated")
                return False
                
        except Exception as e:
            logger.error(f"❌ Image generation failed: {e}")
            return False
    
    def test_audio_generation(self) -> bool:
        """Test audio generation with ElevenLabs."""
        logger.info("🎙️ Testing audio generation...")
        
        try:
            # Generate audio for the first 2 scenes
            for i, scene in enumerate(self.assets['scenes'][:2]):
                narration = scene.get('narration') or scene.get('text', '')
                
                if not narration.strip():
                    logger.warning(f"⚠️ No narration for scene {i}, skipping audio generation")
                    continue
                
                response = self.session.post(
                    f"{self.api_url}/audio/generate",
                    json={
                        "text": narration[:500],  # Limit to save costs
                        "sceneId": scene.get('id', f"scene_{i}"),
                        "projectId": self.project_id,
                        "voice": "onyx",  # Default voice
                        "speed": 1.0
                    },
                    timeout=120
                )
                
                if response.status_code != 200:
                    logger.error(f"❌ Audio generation failed for scene {i}: {response.status_code}")
                    return False
                
                result = response.json()
                audio_url = result.get('url') or result.get('audioUrl')
                
                if audio_url:
                    self.assets['audio_files'].append({
                        'scene_id': scene.get('id'),
                        'url': audio_url,
                        'text': narration[:100] + "..."
                    })
                    logger.info(f"✅ Generated audio for scene {i+1}")
                else:
                    logger.error(f"❌ No audio URL returned for scene {i}")
                    return False
            
            if len(self.assets['audio_files']) >= 1:
                self.results['audio_generation'] = True
                logger.info(f"✅ Audio generation successful: {len(self.assets['audio_files'])} audio files")
                return True
            else:
                logger.error("❌ No audio files generated")
                return False
                
        except Exception as e:
            logger.error(f"❌ Audio generation failed: {e}")
            return False
    
    def test_video_generation(self) -> bool:
        """Test video generation with RunwayML."""
        logger.info("🎬 Testing video generation...")
        
        try:
            # Generate videos using the images we created
            for i, image_asset in enumerate(self.assets['images'][:1]):  # Just one to save costs
                
                motion_prompt = "Camera slowly pans across the scene, subtle movement, cinematic quality"
                
                response = self.session.post(
                    f"{self.api_url}/videos/generate",
                    json={
                        "imageUrl": image_asset['url'],
                        "motionPrompt": motion_prompt,
                        "sceneId": image_asset['scene_id'],
                        "projectId": self.project_id,
                        "duration": 5,  # Short duration for testing
                        "provider": "runway"
                    },
                    timeout=300  # Video generation takes longer
                )
                
                if response.status_code != 200:
                    logger.error(f"❌ Video generation failed: {response.status_code}")
                    return False
                
                result = response.json()
                job_id = result.get('jobId') or result.get('taskId')
                
                if job_id:
                    # Poll for completion
                    video_url = self._wait_for_job_completion(job_id, timeout=600)
                    
                    if video_url:
                        self.assets['video_clips'].append({
                            'scene_id': image_asset['scene_id'],
                            'url': video_url,
                            'motion_prompt': motion_prompt
                        })
                        logger.info(f"✅ Generated video for scene {i+1}")
                    else:
                        logger.error(f"❌ Video generation timed out for scene {i}")
                        return False
                else:
                    logger.error(f"❌ No job ID returned for video generation")
                    return False
            
            if len(self.assets['video_clips']) >= 1:
                self.results['video_generation'] = True
                logger.info(f"✅ Video generation successful: {len(self.assets['video_clips'])} videos")
                return True
            else:
                logger.error("❌ No video clips generated")
                return False
                
        except Exception as e:
            logger.error(f"❌ Video generation failed: {e}")
            return False
    
    def test_final_assembly(self) -> bool:
        """Test final video assembly and export."""
        logger.info("🔧 Testing final assembly...")
        
        try:
            # Assemble final video
            response = self.session.post(
                f"{self.api_url}/assembly/export",
                json={
                    "projectId": self.project_id,
                    "scenes": [
                        {
                            "id": asset['scene_id'],
                            "videoUrl": asset['url'],
                            "audioUrl": self.assets['audio_files'][0]['url'] if self.assets['audio_files'] else None
                        }
                        for asset in self.assets['video_clips']
                    ],
                    "exportFormat": "mp4",
                    "quality": "1080p"
                },
                timeout=300
            )
            
            if response.status_code != 200:
                logger.error(f"❌ Final assembly failed: {response.status_code}")
                return False
            
            result = response.json()
            job_id = result.get('jobId') or result.get('exportId')
            
            if job_id:
                # Wait for assembly completion
                final_video_url = self._wait_for_job_completion(job_id, timeout=600)
                
                if final_video_url:
                    self.assets['final_video'] = final_video_url
                    self.results['final_assembly'] = True
                    self.results['export_success'] = True
                    logger.info(f"✅ Final assembly completed: {final_video_url}")
                    return True
                else:
                    logger.error("❌ Final assembly timed out")
                    return False
            else:
                logger.error("❌ No job ID returned for assembly")
                return False
                
        except Exception as e:
            logger.error(f"❌ Final assembly failed: {e}")
            return False
    
    def _wait_for_job_completion(self, job_id: str, timeout: int = 300) -> Optional[str]:
        """Wait for a job to complete and return the result URL."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = self.session.get(
                    f"{self.api_url}/jobs/{job_id}",
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    status = result.get('status')
                    
                    if status == 'completed':
                        return result.get('url') or result.get('outputUrl')
                    elif status == 'failed':
                        logger.error(f"Job {job_id} failed: {result.get('error', 'Unknown error')}")
                        return None
                    elif status in ['pending', 'processing', 'running']:
                        logger.info(f"Job {job_id} status: {status}")
                        time.sleep(10)
                    else:
                        logger.warning(f"Unknown job status: {status}")
                        time.sleep(5)
                else:
                    logger.warning(f"Job status check failed: {response.status_code}")
                    time.sleep(5)
                    
            except Exception as e:
                logger.warning(f"Error checking job status: {e}")
                time.sleep(5)
        
        logger.error(f"Job {job_id} timed out after {timeout} seconds")
        return None
    
    def run_complete_test(self) -> Dict[str, Any]:
        """Run the complete end-to-end test suite."""
        logger.info("🚀 Starting Complete Workflow Integration Test")
        logger.info("=" * 60)
        
        # Load environment variables
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            logger.warning("python-dotenv not available, ensure environment variables are set")
        
        test_steps = [
            ("API Connectivity", self.test_api_connectivity),
            ("Script Upload & Parsing", self.test_script_upload_and_parsing),
            ("Folder Management", self.test_folder_management),
            ("Image Generation", self.test_image_generation),
            ("Audio Generation", self.test_audio_generation),
            ("Video Generation", self.test_video_generation),
            ("Final Assembly", self.test_final_assembly),
        ]
        
        start_time = time.time()
        passed_tests = 0
        total_tests = len(test_steps)
        
        for step_name, test_func in test_steps:
            logger.info(f"\n🧪 Running: {step_name}")
            logger.info("-" * 40)
            
            try:
                success = test_func()
                if success:
                    passed_tests += 1
                    logger.info(f"✅ {step_name}: PASSED")
                else:
                    logger.error(f"❌ {step_name}: FAILED")
                    
            except Exception as e:
                logger.error(f"💥 {step_name}: CRASHED - {e}")
        
        total_time = time.time() - start_time
        
        # Generate test report
        report = {
            "test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests,
                "success_rate": (passed_tests / total_tests) * 100,
                "total_time_seconds": total_time,
                "project_id": self.project_id
            },
            "detailed_results": self.results,
            "generated_assets": {
                "scenes_count": len(self.assets['scenes']),
                "images_count": len(self.assets['images']),
                "audio_files_count": len(self.assets['audio_files']),
                "video_clips_count": len(self.assets['video_clips']),
                "final_video_url": self.assets['final_video']
            },
            "asset_details": self.assets
        }
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("🏁 INTEGRATION TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Project ID: {self.project_id}")
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {total_tests - passed_tests}")
        logger.info(f"Success Rate: {(passed_tests / total_tests) * 100:.1f}%")
        logger.info(f"Total Time: {total_time:.1f} seconds")
        logger.info(f"Assets Generated:")
        logger.info(f"  - Scenes: {len(self.assets['scenes'])}")
        logger.info(f"  - Images: {len(self.assets['images'])}")
        logger.info(f"  - Audio: {len(self.assets['audio_files'])}")
        logger.info(f"  - Videos: {len(self.assets['video_clips'])}")
        logger.info(f"  - Final Video: {'✅' if self.assets['final_video'] else '❌'}")
        logger.info("=" * 60)
        
        if passed_tests == total_tests:
            logger.info("🎉 ALL TESTS PASSED - Complete workflow is functional!")
        else:
            logger.error("💥 SOME TESTS FAILED - Workflow needs attention")
        
        return report


def main():
    """Main test runner."""
    tester = WorkflowTester()
    report = tester.run_complete_test()
    
    # Save detailed report
    report_path = f"tests/reports/e2e_test_report_{int(time.time())}.json"
    os.makedirs("tests/reports", exist_ok=True)
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"📊 Detailed report saved to: {report_path}")
    
    # Return success/failure for CI
    success_rate = report['test_summary']['success_rate']
    return success_rate >= 80.0  # 80% pass rate threshold


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)