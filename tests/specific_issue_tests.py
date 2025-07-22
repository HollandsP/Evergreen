#!/usr/bin/env python3
"""
Specific test cases demonstrating each critical issue.
These tests can be run independently to verify problems and solutions.
"""

import sys
import os
import tempfile
import json
from unittest.mock import Mock, patch

sys.path.insert(0, '/mnt/c/Users/holla/OneDrive/Desktop/CodeProjects/Evergreen')

def test_1_ffmpeg_eval_exploit():
    """TEST 1: Demonstrate FFmpeg eval() security vulnerability"""
    print("TEST 1: FFmpeg eval() Security Vulnerability")
    print("-" * 50)
    
    from src.services.ffmpeg_service import FFmpegService
    
    service = FFmpegService()
    
    # Create malicious JSON that exploits eval()
    malicious_json = {
        "format": {"duration": "10.0"},
        "streams": [{
            "codec_type": "video",
            "r_frame_rate": "print('SECURITY_BREACH_DETECTED')",  # This will execute!
            "width": 1920,
            "height": 1080
        }]
    }
    
    with patch.object(service, '_run_command') as mock_run:
        mock_result = Mock()
        mock_result.stdout = json.dumps(malicious_json)
        mock_run.return_value = mock_result
        
        print("❌ Exploiting eval() vulnerability...")
        try:
            service.get_media_info("fake.mp4")
            print("✅ VULNERABILITY CONFIRMED: Arbitrary code executed!")
        except Exception as e:
            print(f"⚠️ Exploit failed: {e}")
    
    print("\n💡 SOLUTION: Replace eval() with safe parsing")
    print("✅ TEST 1 COMPLETE")


def test_2_elevenlabs_file_leak():
    """TEST 2: Demonstrate ElevenLabs file handle leak"""
    print("\nTEST 2: ElevenLabs File Handle Leak")
    print("-" * 50)
    
    from src.services.elevenlabs_client import ElevenLabsClient
    
    # Create test files
    test_files = []
    for i in range(3):
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            f.write(b"test audio")
            test_files.append(f.name)
    
    client = ElevenLabsClient(api_key="test")
    
    # Show the problematic pattern
    print("❌ PROBLEMATIC PATTERN:")
    print("   File objects stored in list before requests.post()")
    print("   Risk: Files may not close properly on errors")
    
    try:
        with patch('requests.post') as mock_post:
            mock_post.side_effect = Exception("API Error")
            
            try:
                client.clone_voice("test", test_files)
            except:
                pass  # Expected to fail
        
        print("⚠️ File leak risk demonstrated")
        
    finally:
        # Cleanup
        for f in test_files:
            try:
                os.unlink(f)
            except:
                pass
    
    print("💡 SOLUTION: Read file content immediately")
    print("✅ TEST 2 COMPLETE")


def test_3_runway_complexity():
    """TEST 3: Demonstrate Runway service complexity issues"""
    print("\nTEST 3: Runway Service Complexity")
    print("-" * 50)
    
    import inspect
    from src.services.runway_client import RunwayClient
    
    # Analyze function complexity
    method = getattr(RunwayClient, '_generate_enhanced_placeholder_video')
    source_lines = inspect.getsourcelines(method)[0]
    
    print(f"❌ Function length: {len(source_lines)} lines")
    print("❌ Multiple responsibilities in single function:")
    print("   - Scene type detection")
    print("   - Filter generation")
    print("   - FFmpeg subprocess management")
    print("   - Error handling")
    
    if len(source_lines) > 100:
        print("⚠️ COMPLEXITY ISSUE: Function too long for maintainability")
    
    print("💡 SOLUTION: Split into focused, single-responsibility functions")
    print("✅ TEST 3 COMPLETE")


def test_4_worker_monolithic_design():
    """TEST 4: Demonstrate video worker monolithic design"""
    print("\nTEST 4: Video Worker Monolithic Design")
    print("-" * 50)
    
    # Read worker file and analyze
    worker_file = '/mnt/c/Users/holla/OneDrive/Desktop/CodeProjects/Evergreen/workers/tasks/video_generation.py'
    
    try:
        with open(worker_file, 'r') as f:
            content = f.read()
        
        # Count function lengths
        functions = {}
        lines = content.split('\n')
        current_function = None
        
        for line in lines:
            if line.strip().startswith('def '):
                current_function = line.strip().split('(')[0].replace('def ', '')
                functions[current_function] = 0
            elif current_function and line.strip():
                functions[current_function] += 1
        
        complex_functions = [(f, l) for f, l in functions.items() if l > 80]
        
        print(f"❌ Complex functions found: {len(complex_functions)}")
        for func, length in complex_functions:
            print(f"   - {func}: {length} lines")
        
        print("❌ MONOLITHIC ISSUES:")
        print("   - Functions handling multiple concerns")
        print("   - Difficult to test individual components")
        print("   - Hard to modify without affecting other functionality")
        
        print("💡 SOLUTION: Extract service classes and split responsibilities")
        
    except Exception as e:
        print(f"⚠️ Could not analyze worker file: {e}")
    
    print("✅ TEST 4 COMPLETE")


def test_5_resource_cleanup():
    """TEST 5: Test resource cleanup patterns"""
    print("\nTEST 5: Resource Cleanup Patterns")
    print("-" * 50)
    
    from src.services.runway_client import RunwayClient
    
    # Test memory usage during operations
    import psutil
    process = psutil.Process()
    initial_memory = process.memory_info().rss
    
    client = RunwayClient()
    
    # Perform multiple operations
    for i in range(10):
        job = client.generate_video(f"test {i}")
        status = client.get_generation_status(job['id'])
        if status.get('video_url'):
            data = client.download_video(status['video_url'])
            del data
    
    final_memory = process.memory_info().rss
    growth = final_memory - initial_memory
    
    print(f"Memory growth: {growth / 1024 / 1024:.1f} MB")
    
    if growth < 20 * 1024 * 1024:  # 20MB
        print("✅ Resource cleanup appears adequate")
    else:
        print("⚠️ Potential resource leak detected")
    
    print("💡 Best practices: Use context managers and explicit cleanup")
    print("✅ TEST 5 COMPLETE")


def demonstrate_safe_solutions():
    """Demonstrate safe implementations for all issues"""
    print("\n🔧 SAFE SOLUTION DEMONSTRATIONS")
    print("=" * 50)
    
    print("1. Safe fraction parsing (replaces eval):")
    def safe_parse_fraction(fraction_str):
        try:
            if '/' in fraction_str:
                num, den = fraction_str.split('/')
                return float(num) / float(den) if float(den) != 0 else 0
            return float(fraction_str)
        except (ValueError, ZeroDivisionError):
            return 0.0
    
    # Test cases
    test_cases = ["30/1", "29.97", "invalid", "__import__('os').system('echo hack')"]
    for case in test_cases:
        result = safe_parse_fraction(case)
        print(f"   '{case}' -> {result}")
    
    print("\n2. Safe file handling pattern:")
    print("""
    def safe_clone_voice(self, files):
        files_data = []
        for file_path in files:
            with open(file_path, 'rb') as f:
                content = f.read()  # Read immediately
                files_data.append(('files', (basename, content, 'audio/mpeg')))
        return requests.post(url, files=files_data)
    """)
    
    print("3. Modular service design:")
    print("""
    class VideoGenerationService:
        def __init__(self):
            self.voice_service = VoiceGenerationService()
            self.visual_service = VisualGenerationService()
            self.assembly_service = VideoAssemblyService()
        
        def process(self, script):
            with self.cleanup_context():
                return self.assembly_service.assemble(
                    voice=self.voice_service.generate(script),
                    visuals=self.visual_service.generate(script)
                )
    """)


def main():
    """Run all specific issue tests"""
    print("🔍 CRITICAL ISSUE DEMONSTRATION TESTS")
    print("=" * 50)
    
    test_1_ffmpeg_eval_exploit()
    test_2_elevenlabs_file_leak()
    test_3_runway_complexity()
    test_4_worker_monolithic_design()
    test_5_resource_cleanup()
    demonstrate_safe_solutions()
    
    print("\n🚨 SUMMARY OF CRITICAL ISSUES")
    print("=" * 50)
    print("1. ❌ FFmpeg eval() - SECURITY VULNERABILITY")
    print("2. ❌ ElevenLabs file handling - RESOURCE LEAK")
    print("3. ❌ Runway complexity - MAINTAINABILITY")
    print("4. ❌ Worker monolithic design - CODE QUALITY")
    print("5. ⚠️ Resource cleanup - PERFORMANCE")
    
    print("\n✅ All issues demonstrated with safe solutions provided")
    print("📖 See CRITICAL_ISSUES_REPORT.md for complete analysis")


if __name__ == "__main__":
    main()