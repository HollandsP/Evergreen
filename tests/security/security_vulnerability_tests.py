#!/usr/bin/env python3
"""
CRITICAL SECURITY TEST: eval() Vulnerability Demonstration
This test demonstrates the critical security vulnerability in FFmpeg service.

⚠️  WARNING: This test demonstrates real security vulnerabilities.
    Run only in isolated test environments.
"""

import json
import tempfile
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def create_malicious_video_metadata():
    """Create mock video metadata with malicious eval() payload."""
    
    # Simulate malicious video metadata that would be returned by ffprobe
    malicious_metadata = {
        'streams': [
            {
                'codec_type': 'video',
                'width': 1920,
                'height': 1080,
                # CRITICAL: This will execute arbitrary code when eval() is called
                'r_frame_rate': '__import__("os").system("echo SECURITY_BREACH_DETECTED > /tmp/security_test_output.txt")',
                'codec_name': 'h264',
                'bit_rate': '5000000'
            }
        ],
        'format': {
            'duration': '10.0',
            'size': '12345678',
            'bit_rate': '6000000',
            'format_name': 'mp4'
        }
    }
    
    return malicious_metadata

def test_eval_vulnerability_ffmpeg_service():
    """Test the eval() vulnerability in ffmpeg_service.py"""
    
    print("🚨 TESTING CRITICAL eval() VULNERABILITY in FFmpegService")
    print("=" * 60)
    
    try:
        from services.ffmpeg_service import FFmpegService
        
        # Create a mock video stream data that would trigger the vulnerability
        mock_video_stream = {
            'width': '1920',
            'height': '1080',
            # This is the malicious payload that gets eval()'d
            'r_frame_rate': '__import__("os").system("echo CRITICAL_VULNERABILITY_EXPLOITED")',
            'codec_name': 'h264',
            'bit_rate': '5000000'
        }
        
        print(f"Malicious payload: {mock_video_stream['r_frame_rate']}")
        print("\n⚠️  About to execute vulnerable code path...")
        
        # This simulates the vulnerable line 106 in ffmpeg_service.py
        # 'fps': eval(video_stream.get('r_frame_rate', '0/1')),
        vulnerable_result = eval(mock_video_stream.get('r_frame_rate', '0/1'))
        
        print(f"❌ VULNERABILITY CONFIRMED: Code executed successfully")
        print(f"Returned: {vulnerable_result}")
        
    except Exception as e:
        print(f"Error during test: {e}")
        print("This error might mask the vulnerability execution")

def test_eval_vulnerability_video_optimizer():
    """Test the eval() vulnerability in video_quality_optimizer.py"""
    
    print("\n🚨 TESTING CRITICAL eval() VULNERABILITY in VideoQualityOptimizer")
    print("=" * 60)
    
    # Simulate the vulnerable code from video_quality_optimizer.py line 156
    mock_video_stream = {
        'r_frame_rate': '__import__("subprocess").run(["echo", "OPTIMIZER_VULNERABILITY_EXPLOITED"])'
    }
    
    print(f"Malicious payload: {mock_video_stream['r_frame_rate']}")
    print("\n⚠️  About to execute vulnerable code path...")
    
    try:
        # This simulates the vulnerable line 156 in video_quality_optimizer.py
        # 'fps': eval(video_stream['r_frame_rate']),
        vulnerable_result = eval(mock_video_stream['r_frame_rate'])
        
        print(f"❌ VULNERABILITY CONFIRMED: Code executed successfully")
        print(f"Returned: {vulnerable_result}")
        
    except Exception as e:
        print(f"Error during test: {e}")

def test_safe_alternative():
    """Demonstrate safe alternative to eval() for frame rate parsing."""
    
    print("\n✅ TESTING SAFE ALTERNATIVE")
    print("=" * 60)
    
    def safe_parse_frame_rate(frame_rate_str):
        """Safe alternative to eval() for parsing frame rates."""
        try:
            # Validate input is in expected format
            if '/' not in frame_rate_str:
                return float(frame_rate_str)
            
            parts = frame_rate_str.split('/')
            if len(parts) != 2:
                raise ValueError("Invalid frame rate format")
            
            numerator = float(parts[0])
            denominator = float(parts[1])
            
            if denominator == 0:
                return 0.0
            
            return numerator / denominator
            
        except (ValueError, TypeError):
            return 0.0
    
    # Test with legitimate frame rates
    test_cases = ['30/1', '60/1', '23.976', '0/1']
    
    for test_case in test_cases:
        result = safe_parse_frame_rate(test_case)
        print(f"Safe parsing '{test_case}' -> {result}")
    
    # Test with malicious input
    malicious_input = '__import__("os").system("echo ATTACK")'
    safe_result = safe_parse_frame_rate(malicious_input)
    print(f"Safe parsing malicious input -> {safe_result} (attack prevented)")

def create_security_report():
    """Generate detailed security report."""
    
    report = """
SECURITY VULNERABILITY REPORT
=============================

VULNERABILITY: Arbitrary Code Execution via eval()
SEVERITY: CRITICAL (9.8/10)
FILES AFFECTED:
- src/services/ffmpeg_service.py:106
- src/services/video_quality_optimizer.py:156

ATTACK VECTOR:
Malicious video files with crafted metadata can execute arbitrary Python code
when processed by the application.

EXPLOITATION:
1. Attacker creates video file with malicious r_frame_rate metadata
2. Application processes video using FFmpegService or VideoQualityOptimizer
3. eval() function executes the malicious code with application privileges
4. Attacker gains code execution on the server

IMPACT:
- Complete system compromise
- Data exfiltration
- Backdoor installation
- Service disruption
- Lateral movement in network

IMMEDIATE ACTIONS REQUIRED:
1. Replace eval() with safe parsing functions
2. Implement input validation for all external data
3. Add security scanning to CI/CD pipeline
4. Audit all uses of eval(), exec(), subprocess, os.system
5. Implement principle of least privilege

TIMELINE: Patch within 24 hours
"""
    
    with open('/tmp/security_vulnerability_report.txt', 'w') as f:
        f.write(report)
    
    print(report)

if __name__ == "__main__":
    print("🚨 CRITICAL SECURITY VULNERABILITY TESTING")
    print("=" * 60)
    print("⚠️  WARNING: These tests demonstrate real vulnerabilities")
    print("    Run only in isolated environments")
    print("=" * 60)
    
    # Test the vulnerabilities
    test_eval_vulnerability_ffmpeg_service()
    test_eval_vulnerability_video_optimizer()
    
    # Show safe alternative
    test_safe_alternative()
    
    # Generate report
    create_security_report()
    
    print("\n🚨 SECURITY TESTING COMPLETE")
    print("See /tmp/security_vulnerability_report.txt for full report")