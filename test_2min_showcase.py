#!/usr/bin/env python3
"""
2-Minute Showcase Video Generation Test
Tests all components of the AI video generation pipeline
"""
import os
import requests
import time
import subprocess
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# 2-minute showcase script
SHOWCASE_SCRIPT = """SCRIPT: AI VIDEO GENERATION - 2 MINUTE SHOWCASE

[0:00 - Opening]
Visual: A futuristic AI laboratory with holographic displays showing code streaming across multiple screens
Narration (Male): "Welcome to the AI video generation pipeline showcase. This comprehensive demonstration highlights our cutting-edge technology that transforms scripts into professional videos."
ON-SCREEN TEXT: $ echo "AI Video Generation Pipeline v1.0" | figlet

[0:15 - Voice Synthesis Demo]
Visual: Sound wave visualizations morphing between different voice patterns, showing frequency analysis
Narration (Female): "Our ElevenLabs integration provides natural, expressive voice synthesis with multiple speaker options. Each voice is carefully crafted for maximum clarity and emotion."
ON-SCREEN TEXT: $ python -m elevenlabs --voice "female_calm" --text "Hello, world!"

[0:30 - Terminal UI Showcase]
Visual: Multiple terminal windows cascading across the screen, each showing different themes and animations
Narration (Male): "Watch as our terminal renderer creates stunning typing animations with customizable themes. From classic dark mode to the iconic Matrix theme."
ON-SCREEN TEXT: for theme in dark light matrix hacker vscode; do clear; echo "Theme: $theme"; sleep 2; done

[0:45 - Visual Generation]
Visual: AI-generated cityscapes transitioning smoothly from day to night with dynamic lighting
Narration (Female): "Runway's powerful AI transforms text descriptions into cinematic visuals. Each scene is generated based on detailed prompts for maximum visual impact."
ON-SCREEN TEXT: $ curl -X POST https://api.runway.ml/v1/generate -d "prompt=futuristic city"

[1:00 - Component Integration]
Visual: Split screen showing all components working together - voice waveforms, terminal animations, and visuals
Narration (Male): "Our FFmpeg assembly pipeline seamlessly combines audio, visuals, and terminal overlays into a cohesive final product."
ON-SCREEN TEXT: $ ffmpeg -i visual.mp4 -i terminal.mp4 -filter_complex "overlay=W-w-50:H-h-50"

[1:15 - Performance Metrics]
Visual: Real-time dashboard showing performance metrics, GPU usage, and rendering statistics
Narration (Female): "The system processes videos efficiently, maintaining high quality while optimizing resources. Average processing time is under two minutes per minute of video."
ON-SCREEN TEXT: $ htop | grep -E "ffmpeg|python" | awk '{print $1,$9,$10}'

[1:30 - Error Recovery]
Visual: System console showing error messages being caught and handled gracefully
Narration (Male): "Built-in error recovery ensures reliable operation even when external services fail. The system automatically falls back to alternative methods."
ON-SCREEN TEXT: $ ./pipeline.sh --retry-on-failure --fallback-mode --max-retries=3

[1:45 - Final Results]
Visual: Montage of generated videos showcasing different styles - educational, entertainment, corporate
Narration (Female): "From script to screen, our AI pipeline delivers professional videos ready for any platform. YouTube, social media, or corporate presentations - we've got you covered."
ON-SCREEN TEXT: $ echo "Video generation complete!" && ls -la output/*.mp4

END SHOWCASE
"""

class TwoMinuteShowcaseTest:
    def __init__(self):
        self.base_url = "http://localhost:8000/api/v1"
        self.script = SHOWCASE_SCRIPT
        self.job_id = None
        self.project_id = None
        self.token = None
        self.start_time = None
        self.test_results = {
            "components": {},
            "timing": {},
            "errors": [],
            "output": None
        }
        
    def run_test(self):
        """Run the complete 2-minute showcase test"""
        print("🎬 Starting 2-Minute Showcase Video Generation Test")
        print("=" * 60)
        
        self.start_time = datetime.now()
        
        try:
            # Step 1: Authenticate
            if not self._authenticate():
                return False
                
            # Step 2: Create project
            if not self._create_project():
                return False
                
            # Step 3: Start video generation
            if not self._start_generation():
                return False
                
            # Step 4: Monitor generation
            if not self._monitor_generation():
                return False
                
            # Step 5: Validate output
            if not self._validate_output():
                return False
                
            # Step 6: Generate report
            self._generate_report()
            
            return True
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            self.test_results["errors"].append(str(e))
            return False
    
    def _authenticate(self):
        """Authenticate with the API"""
        print("\n📝 Step 1: Authentication")
        
        # Register user
        register_data = {
            "email": "showcase.test@example.com",
            "password": "showcase123",
            "full_name": "Showcase Test User"
        }
        
        requests.post(f"{self.base_url}/auth/register", json=register_data)
        
        # Login
        login_data = {
            "username": "showcase.test@example.com",
            "password": "showcase123"
        }
        
        response = requests.post(f"{self.base_url}/auth/token", data=login_data)
        
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            print("✅ Authentication successful")
            return True
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            return False
    
    def _create_project(self):
        """Create a new project with the showcase script"""
        print("\n📝 Step 2: Creating Project")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        project_data = {
            "name": "2-Minute AI Showcase",
            "description": "Comprehensive demonstration of all pipeline components",
            "script_content": self.script,
            "style": "techwear",  # Futuristic style
            "voice_type": "male_calm"  # Default voice
        }
        
        response = requests.post(
            f"{self.base_url}/projects/",
            json=project_data,
            headers=headers
        )
        
        if response.status_code in [200, 201]:
            project = response.json()
            self.project_id = project["id"]
            print(f"✅ Project created: {project['name']} (ID: {self.project_id})")
            return True
        else:
            print(f"❌ Project creation failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    
    def _start_generation(self):
        """Start the video generation process"""
        print("\n🎬 Step 3: Starting Video Generation")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        generation_data = {
            "project_id": self.project_id,
            "quality": "high",
            "priority": 10  # Highest priority
        }
        
        response = requests.post(
            f"{self.base_url}/generation/",
            json=generation_data,
            headers=headers
        )
        
        if response.status_code == 202:
            result = response.json()
            self.job_id = result["job_id"]
            print(f"✅ Generation started: Job ID {self.job_id}")
            return True
        else:
            print(f"❌ Generation start failed: {response.status_code}")
            return False
    
    def _monitor_generation(self):
        """Monitor the generation progress with detailed logging"""
        print("\n📊 Step 4: Monitoring Generation Progress")
        print("-" * 60)
        
        headers = {"Authorization": f"Bearer {self.token}"}
        max_wait = 300  # 5 minutes max
        start_time = time.time()
        
        # Also monitor worker logs
        print("\n📋 Starting log monitor...")
        log_monitor = subprocess.Popen(
            ["docker-compose", "logs", "-f", "worker"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        last_progress = -1
        components_seen = set()
        
        try:
            while time.time() - start_time < max_wait:
                # Check generation status
                response = requests.get(
                    f"{self.base_url}/generation/{self.job_id}/status",
                    headers=headers
                )
                
                if response.status_code == 200:
                    status = response.json()
                    progress = status.get("progress", 0)
                    
                    # Only print if progress changed
                    if progress != last_progress:
                        print(f"\n⏳ Progress: {progress:.1f}% - {status.get('current_step', 'Processing')}")
                        last_progress = progress
                    
                    # Track components
                    current_step = status.get("current_step", "")
                    if "voice" in current_step.lower() and "voice" not in components_seen:
                        components_seen.add("voice")
                        self.test_results["components"]["voice"] = True
                        print("  ✓ Voice synthesis started")
                    elif "terminal" in current_step.lower() and "terminal" not in components_seen:
                        components_seen.add("terminal")
                        self.test_results["components"]["terminal"] = True
                        print("  ✓ Terminal UI generation started")
                    elif "visual" in current_step.lower() and "visual" not in components_seen:
                        components_seen.add("visual")
                        self.test_results["components"]["visual"] = True
                        print("  ✓ Visual scene generation started")
                    elif "assembl" in current_step.lower() and "assembly" not in components_seen:
                        components_seen.add("assembly")
                        self.test_results["components"]["assembly"] = True
                        print("  ✓ FFmpeg assembly started")
                    
                    # Check if complete
                    if status["status"] == "completed":
                        print("\n✅ Generation completed successfully!")
                        self.test_results["output"] = status.get("output_file")
                        self.test_results["timing"]["total"] = time.time() - start_time
                        return True
                    elif status["status"] == "failed":
                        print(f"\n❌ Generation failed: {status.get('error', 'Unknown error')}")
                        self.test_results["errors"].append(status.get("error", "Unknown error"))
                        return False
                
                time.sleep(2)
                
                # Check worker logs for important messages
                if log_monitor.poll() is None:
                    line = log_monitor.stdout.readline()
                    if line:
                        # Look for key messages
                        if "Starting video assembly" in line:
                            print("\n🎯 NEW FFmpeg assembly code detected!")
                            self.test_results["components"]["new_assembly"] = True
                        elif "Video assembly planned" in line:
                            print("\n⚠️ OLD placeholder code still in use")
                            self.test_results["components"]["new_assembly"] = False
                        elif "VideoComposer" in line:
                            print("\n✓ VideoComposer class instantiated")
                        elif "FFmpeg command:" in line:
                            print(f"\n🔧 {line.strip()}")
                
            print("\n⏰ Generation timed out")
            return False
            
        finally:
            # Stop log monitor
            log_monitor.terminate()
    
    def _validate_output(self):
        """Validate the generated video output"""
        print("\n🔍 Step 5: Validating Output")
        
        if not self.test_results.get("output"):
            print("❌ No output file generated")
            return False
        
        # Check if file exists in container
        output_file = self.test_results["output"]
        check_cmd = ["docker", "exec", "evergreen-worker-1", "ls", "-la", output_file]
        
        result = subprocess.run(check_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Output file not found: {output_file}")
            return False
        
        # Get file info
        file_info = result.stdout.strip()
        print(f"✅ Output file exists: {file_info}")
        
        # Use ffprobe to validate video properties
        probe_cmd = [
            "docker", "exec", "evergreen-worker-1",
            "ffprobe", "-v", "error", "-show_format", "-show_streams",
            "-print_format", "json", output_file
        ]
        
        result = subprocess.run(probe_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            try:
                probe_data = json.loads(result.stdout)
                
                # Extract key properties
                format_info = probe_data.get("format", {})
                duration = float(format_info.get("duration", 0))
                size = int(format_info.get("size", 0)) / (1024 * 1024)  # MB
                
                print(f"\n📊 Video Properties:")
                print(f"  Duration: {duration:.1f} seconds (expected: ~120s)")
                print(f"  Size: {size:.1f} MB")
                print(f"  Format: {format_info.get('format_name', 'unknown')}")
                
                # Check streams
                streams = probe_data.get("streams", [])
                video_stream = next((s for s in streams if s["codec_type"] == "video"), None)
                audio_stream = next((s for s in streams if s["codec_type"] == "audio"), None)
                
                if video_stream:
                    print(f"  Video: {video_stream['codec_name']} {video_stream['width']}x{video_stream['height']} @ {video_stream.get('r_frame_rate', 'unknown')} fps")
                
                if audio_stream:
                    print(f"  Audio: {audio_stream['codec_name']} {audio_stream.get('sample_rate', 'unknown')} Hz")
                
                # Validation checks
                valid = True
                if duration < 110 or duration > 130:  # Allow 10s variance
                    print("  ⚠️ Duration outside expected range")
                    valid = False
                
                if size < 1:  # Less than 1MB suggests placeholder
                    print("  ⚠️ File size too small - likely placeholder")
                    valid = False
                
                if not video_stream or not audio_stream:
                    print("  ⚠️ Missing video or audio stream")
                    valid = False
                
                return valid
                
            except json.JSONDecodeError:
                print("❌ Failed to parse ffprobe output")
                return False
        else:
            print(f"❌ ffprobe failed: {result.stderr}")
            return False
    
    def _generate_report(self):
        """Generate a comprehensive test report"""
        print("\n" + "=" * 60)
        print("📑 TEST REPORT - 2-Minute Showcase Video")
        print("=" * 60)
        
        # Timing
        total_time = self.test_results["timing"].get("total", 0)
        print(f"\n⏱️ Total Generation Time: {total_time:.1f} seconds")
        
        # Components
        print("\n🧩 Component Status:")
        components = self.test_results["components"]
        print(f"  Voice Synthesis: {'✅' if components.get('voice') else '❌'}")
        print(f"  Terminal UI: {'✅' if components.get('terminal') else '❌'}")
        print(f"  Visual Scenes: {'✅' if components.get('visual') else '❌'}")
        print(f"  FFmpeg Assembly: {'✅' if components.get('assembly') else '❌'}")
        print(f"  New Assembly Code: {'✅' if components.get('new_assembly') else '❌ (using old placeholder)'}")
        
        # Output
        print(f"\n📹 Output File: {self.test_results.get('output', 'None')}")
        
        # Errors
        if self.test_results["errors"]:
            print("\n❌ Errors Encountered:")
            for error in self.test_results["errors"]:
                print(f"  - {error}")
        
        # Overall Status
        all_components = all([
            components.get("voice"),
            components.get("terminal"),
            components.get("visual"),
            components.get("assembly")
        ])
        
        print("\n" + "=" * 60)
        if all_components and components.get("new_assembly"):
            print("✅ TEST PASSED - All components working with new FFmpeg assembly!")
        elif all_components:
            print("⚠️ TEST PARTIAL - Components working but using old assembly code")
        else:
            print("❌ TEST FAILED - Not all components functional")
        print("=" * 60)

def main():
    """Run the showcase test"""
    test = TwoMinuteShowcaseTest()
    success = test.run_test()
    
    if success:
        print("\n🎉 Showcase video generation successful!")
        print("Check the output file in the worker container")
    else:
        print("\n💔 Showcase video generation failed")
        print("Review the errors and logs for details")

if __name__ == "__main__":
    main()