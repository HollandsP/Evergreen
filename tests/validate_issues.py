#!/usr/bin/env python3
"""
Standalone validation script for critical service issues.
This script tests the core issues without external dependencies.
"""

import os
import sys
import tempfile
import subprocess
import inspect
from pathlib import Path

# Add project root to path
sys.path.insert(0, '/mnt/c/Users/holla/OneDrive/Desktop/CodeProjects/Evergreen')

def test_elevenlabs_file_handling():
    """Test ElevenLabs clone_voice file handling issues."""
    print("🔍 Testing ElevenLabs file handling...")
    
    try:
        from src.services.elevenlabs_client import ElevenLabsClient
        
        # Read the source code to analyze file handling
        source = inspect.getsource(ElevenLabsClient.clone_voice)
        
        issues_found = []
        
        # Check for file handling issues
        if 'with open(' in source and 'files_data.append' in source:
            issues_found.append("❌ ISSUE: Files opened in loop without proper resource management")
            issues_found.append("   Files are opened one by one and stored in list, risking resource leaks")
        
        if 'f.read()' not in source and 'f,' in source:
            issues_found.append("❌ ISSUE: File objects passed to requests without reading")
            issues_found.append("   File handles passed directly to requests.post may not be properly closed")
        
        # Check error handling
        if 'except' in source and 'finally' not in source:
            issues_found.append("❌ ISSUE: No finally block to ensure file cleanup on errors")
        
        if issues_found:
            print("❌ ElevenLabs clone_voice() has file handling issues:")
            for issue in issues_found:
                print(f"   {issue}")
            return False
        else:
            print("✅ ElevenLabs file handling looks good")
            return True
            
    except ImportError as e:
        print(f"⚠️ Could not import ElevenLabsClient: {e}")
        return None


def test_runway_implementation_confusion():
    """Test Runway service implementation clarity."""
    print("\n🔍 Testing Runway implementation clarity...")
    
    try:
        from src.services.runway_client import RunwayClient
        
        # Check the class documentation and implementation
        source = inspect.getsource(RunwayClient)
        
        issues_found = []
        
        # Check for stub vs real confusion
        if 'stub' in source.lower() and 'placeholder' in source.lower():
            issues_found.append("❌ ISSUE: Mixed terminology (stub vs placeholder) creates confusion")
        
        # Check for API key handling
        if 'dummy_key' in source:
            issues_found.append("⚠️ WARNING: Uses 'dummy_key' as default - may cause confusion")
        
        # Check for complex fallback logic
        lines = source.split('\n')
        function_lines = {}
        current_function = None
        
        for line in lines:
            if 'def ' in line:
                current_function = line.strip()
                function_lines[current_function] = 0
            elif current_function:
                function_lines[current_function] += 1
        
        for func, line_count in function_lines.items():
            if line_count > 100:
                issues_found.append(f"❌ ISSUE: Function too complex: {func} ({line_count} lines)")
        
        # Check for FFmpeg subprocess calls in Runway client
        if 'subprocess.run' in source:
            issues_found.append("⚠️ WARNING: Runway client contains FFmpeg subprocess calls")
            issues_found.append("   This should be delegated to FFmpegService for consistency")
        
        if issues_found:
            print("❌ Runway service has implementation issues:")
            for issue in issues_found:
                print(f"   {issue}")
            return False
        else:
            print("✅ Runway implementation clarity looks good")
            return True
            
    except ImportError as e:
        print(f"⚠️ Could not import RunwayClient: {e}")
        return None


def test_ffmpeg_security_and_resources():
    """Test FFmpeg service security and resource management."""
    print("\n🔍 Testing FFmpeg security and resource management...")
    
    try:
        from src.services.ffmpeg_service import FFmpegService
        
        source = inspect.getsource(FFmpegService)
        
        issues_found = []
        
        # Check for eval() usage (security issue)
        if 'eval(' in source:
            issues_found.append("❌ CRITICAL: eval() used in code - major security vulnerability")
            issues_found.append("   Line 106: eval(video_stream.get('r_frame_rate', '0/1'))")
            issues_found.append("   This allows arbitrary code execution!")
        
        # Check for temporary file cleanup
        if 'tempfile' in source and 'finally' not in source:
            issues_found.append("⚠️ WARNING: Temporary files may not be cleaned up properly")
        
        # Check for subprocess resource management
        if 'subprocess.run' in source and 'timeout=' not in source:
            issues_found.append("⚠️ WARNING: No timeouts on subprocess calls")
            issues_found.append("   Long-running FFmpeg processes could hang indefinitely")
        
        # Check error handling
        method_sources = {}
        methods = [method for method in dir(FFmpegService) if not method.startswith('_')]
        
        for method_name in methods:
            try:
                method = getattr(FFmpegService, method_name)
                if callable(method):
                    method_source = inspect.getsource(method)
                    if 'try:' in method_source and 'except' in method_source:
                        if 'finally:' not in method_source and 'tempfile' in method_source:
                            issues_found.append(f"⚠️ WARNING: {method_name}() may leak temporary files")
            except (OSError, TypeError):
                continue
        
        if issues_found:
            print("❌ FFmpeg service has security/resource issues:")
            for issue in issues_found:
                print(f"   {issue}")
            return False
        else:
            print("✅ FFmpeg security and resource management looks good")
            return True
            
    except ImportError as e:
        print(f"⚠️ Could not import FFmpegService: {e}")
        return None


def test_video_generation_complexity():
    """Test video generation worker complexity issues."""
    print("\n🔍 Testing video generation worker complexity...")
    
    try:
        # Read the file directly since we can't import due to celery dependency
        worker_file = Path('/mnt/c/Users/holla/OneDrive/Desktop/CodeProjects/Evergreen/workers/tasks/video_generation.py')
        
        if not worker_file.exists():
            print("⚠️ Video generation worker file not found")
            return None
        
        content = worker_file.read_text()
        lines = content.split('\n')
        
        issues_found = []
        
        # Count function lengths
        current_function = None
        function_lines = {}
        brace_count = 0
        
        for i, line in enumerate(lines):
            if line.strip().startswith('def '):
                if current_function and function_lines[current_function] > 80:
                    issues_found.append(f"❌ ISSUE: Function {current_function} is too long ({function_lines[current_function]} lines)")
                
                current_function = line.strip().split('(')[0].replace('def ', '')
                function_lines[current_function] = 0
                brace_count = 0
            elif current_function:
                function_lines[current_function] += 1
        
        # Check last function
        if current_function and function_lines[current_function] > 80:
            issues_found.append(f"❌ ISSUE: Function {current_function} is too long ({function_lines[current_function]} lines)")
        
        # Check for monolithic design patterns
        if 'process_video_generation' in content:
            # Count direct API calls in main function
            main_func_start = content.find('def process_video_generation')
            if main_func_start != -1:
                main_func_end = content.find('\ndef ', main_func_start + 1)
                if main_func_end == -1:
                    main_func_end = len(content)
                
                main_func = content[main_func_start:main_func_end]
                
                if main_func.count('_generate_') >= 4:
                    issues_found.append("❌ ISSUE: Main function orchestrates too many sub-operations")
                    issues_found.append("   Should use a more modular pipeline architecture")
        
        # Check for proper error recovery
        if 'try:' in content and content.count('except Exception as e:') > content.count('finally:'):
            issues_found.append("⚠️ WARNING: Inconsistent error handling - not all try blocks have proper cleanup")
        
        # Check for hardcoded paths
        if '/app/output/' in content:
            issues_found.append("⚠️ WARNING: Hardcoded output paths may cause issues in different environments")
        
        if issues_found:
            print("❌ Video generation worker has complexity issues:")
            for issue in issues_found:
                print(f"   {issue}")
            
            # Show function complexity summary
            print("\n📊 Function Complexity Summary:")
            for func, line_count in sorted(function_lines.items(), key=lambda x: x[1], reverse=True):
                if line_count > 20:
                    status = "❌" if line_count > 80 else "⚠️" if line_count > 50 else "✅"
                    print(f"   {status} {func}: {line_count} lines")
            
            return False
        else:
            print("✅ Video generation worker complexity looks manageable")
            return True
            
    except Exception as e:
        print(f"⚠️ Could not analyze video generation worker: {e}")
        return None


def test_ffmpeg_availability():
    """Test if FFmpeg is available and working."""
    print("\n🔍 Testing FFmpeg availability...")
    
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✅ FFmpeg available: {version_line}")
            return True
        else:
            print("❌ FFmpeg not working properly")
            return False
    except FileNotFoundError:
        print("❌ FFmpeg not found in PATH")
        return False
    except subprocess.TimeoutExpired:
        print("❌ FFmpeg command timed out")
        return False
    except Exception as e:
        print(f"❌ Error testing FFmpeg: {e}")
        return False


def main():
    """Run all validation tests."""
    print("🔍 Critical Service Issues Validation")
    print("=" * 50)
    
    results = {
        'elevenlabs': test_elevenlabs_file_handling(),
        'runway': test_runway_implementation_confusion(),
        'ffmpeg': test_ffmpeg_security_and_resources(),
        'worker': test_video_generation_complexity(),
        'ffmpeg_available': test_ffmpeg_availability()
    }
    
    print("\n📋 VALIDATION SUMMARY")
    print("=" * 50)
    
    critical_issues = []
    warnings = []
    
    for test_name, result in results.items():
        if result is True:
            print(f"✅ {test_name}: PASSED")
        elif result is False:
            print(f"❌ {test_name}: FAILED")
            critical_issues.append(test_name)
        else:
            print(f"⚠️ {test_name}: SKIPPED")
            warnings.append(test_name)
    
    print(f"\n📊 RESULTS: {len([r for r in results.values() if r is True])} passed, "
          f"{len(critical_issues)} failed, {len(warnings)} skipped")
    
    if critical_issues:
        print(f"\n🚨 CRITICAL ISSUES FOUND in: {', '.join(critical_issues)}")
        print("\n💡 RECOMMENDED IMMEDIATE ACTIONS:")
        print("1. Fix FFmpeg eval() security vulnerability (CRITICAL)")
        print("2. Refactor ElevenLabs clone_voice() file handling")
        print("3. Simplify video generation worker functions")
        print("4. Clarify Runway service implementation patterns")
        print("5. Add proper resource cleanup and error handling")
        
        return 1
    else:
        print("\n✅ No critical issues found!")
        return 0


if __name__ == "__main__":
    exit(main())