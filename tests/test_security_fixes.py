"""
Test security vulnerability fixes.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, mock_open

from src.services.ffmpeg_service import safe_parse_frame_rate, validate_file_path, FFmpegService
from src.services.video_quality_optimizer import safe_parse_frame_rate as vqo_safe_parse_frame_rate
from src.services.elevenlabs_client import validate_audio_file, ElevenLabsClient
from src.core.security import (
    sanitize_filename, validate_file_path as sec_validate_file_path,
    validate_text_input, validate_voice_id, SecurityValidator
)


class TestSecurityFixes:
    """Test security vulnerability fixes."""
    
    def test_ffmpeg_safe_frame_rate_parsing(self):
        """Test that eval() vulnerability is fixed in FFmpeg service."""
        # Test normal cases
        assert safe_parse_frame_rate("30/1") == 30.0
        assert safe_parse_frame_rate("25/1") == 25.0
        assert safe_parse_frame_rate("60/1") == 60.0
        assert safe_parse_frame_rate("24000/1001") == pytest.approx(23.976, rel=1e-3)
        
        # Test edge cases
        assert safe_parse_frame_rate("0/1") == 0.0
        assert safe_parse_frame_rate("0/0") == 0.0
        assert safe_parse_frame_rate("") == 0.0
        assert safe_parse_frame_rate(None) == 0.0
        
        # Test malicious inputs (should not execute code)
        assert safe_parse_frame_rate("__import__('os').system('rm -rf /')") == 0.0
        assert safe_parse_frame_rate("eval('malicious_code')") == 0.0
        assert safe_parse_frame_rate("1+1") == 0.0  # Invalid format
        assert safe_parse_frame_rate("30*1") == 0.0  # Invalid format
        
        # Test division by zero
        assert safe_parse_frame_rate("30/0") == 0.0
    
    def test_video_quality_optimizer_safe_frame_rate_parsing(self):
        """Test that eval() vulnerability is fixed in VideoQualityOptimizer."""
        # Test normal cases
        assert vqo_safe_parse_frame_rate("30/1") == 30.0
        assert vqo_safe_parse_frame_rate("25/1") == 25.0
        
        # Test malicious inputs
        assert vqo_safe_parse_frame_rate("__import__('os').system('rm -rf /')") == 0.0
        assert vqo_safe_parse_frame_rate("eval('malicious_code')") == 0.0
    
    def test_file_path_validation(self):
        """Test file path validation prevents path traversal."""
        # Create temporary test file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"test content")
            valid_path = temp_file.name
        
        try:
            # Test valid path
            validated = validate_file_path(valid_path)
            assert str(validated) == str(Path(valid_path).resolve())
            
            # Test empty path
            with pytest.raises(ValueError, match="File path cannot be empty"):
                validate_file_path("")
            
            # Test non-existent file
            with pytest.raises(ValueError, match="File does not exist"):
                validate_file_path("/nonexistent/file.txt")
            
        finally:
            os.unlink(valid_path)
    
    def test_elevenlabs_file_leak_fix(self):
        """Test that file handles are properly closed in ElevenLabs client."""
        client = ElevenLabsClient(api_key="test_key")
        
        # Create temporary audio files
        temp_files = []
        for i in range(3):
            temp_file = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
            temp_file.write(b"fake audio data")
            temp_file.close()
            temp_files.append(temp_file.name)
        
        try:
            # Mock the requests.post to simulate API failure
            with patch('requests.post') as mock_post:
                mock_post.side_effect = Exception("API Error")
                
                # This should raise an exception but still close file handles
                with pytest.raises(Exception):
                    client.clone_voice("test_voice", temp_files)
                
                # Verify files can be deleted (not locked by open handles)
                for file_path in temp_files:
                    os.unlink(file_path)  # Should not raise PermissionError
        
        finally:
            # Clean up any remaining files
            for file_path in temp_files:
                if os.path.exists(file_path):
                    os.unlink(file_path)
    
    def test_audio_file_validation(self):
        """Test audio file validation."""
        # Create temporary audio file
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_file.write(b"fake audio data")
            valid_audio = temp_file.name
        
        try:
            # Test valid audio file
            validated = validate_audio_file(valid_audio)
            assert validated == str(Path(valid_audio).resolve())
            
            # Test empty path
            with pytest.raises(ValueError, match="File path cannot be empty"):
                validate_audio_file("")
            
            # Test non-existent file
            with pytest.raises(ValueError, match="Audio file does not exist"):
                validate_audio_file("/nonexistent/audio.mp3")
            
        finally:
            os.unlink(valid_audio)
        
        # Test invalid file extension
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            temp_file.write(b"not audio")
            invalid_audio = temp_file.name
        
        try:
            with pytest.raises(ValueError, match="Unsupported audio file type"):
                validate_audio_file(invalid_audio)
        finally:
            os.unlink(invalid_audio)
    
    def test_text_input_validation(self):
        """Test text input validation."""
        # Test normal text
        assert validate_text_input("Hello world!") == "Hello world!"
        assert validate_text_input("  Text with spaces  ") == "Text with spaces"
        
        # Test empty text
        with pytest.raises(ValueError, match="Text cannot be None"):
            validate_text_input(None)
        
        # Test non-string input
        with pytest.raises(ValueError, match="Text must be a string"):
            validate_text_input(123)
        
        # Test maximum length
        long_text = "a" * 6000
        with pytest.raises(ValueError, match="Text too long"):
            validate_text_input(long_text)
        
        # Test dangerous patterns
        dangerous_inputs = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "data:text/html;base64,PHNjcmlwdD5hbGVydCgneHNzJyk8L3NjcmlwdD4=",
            "eval('malicious_code')",
            "exec('malicious_code')",
            "import os",
            "__import__",
        ]
        
        for dangerous_input in dangerous_inputs:
            with pytest.raises(ValueError, match="potentially dangerous content"):
                validate_text_input(dangerous_input)
    
    def test_voice_id_validation(self):
        """Test voice ID validation."""
        # Test valid voice IDs
        assert validate_voice_id("valid_voice_123") == "valid_voice_123"
        assert validate_voice_id("voice-id-with-hyphens") == "voice-id-with-hyphens"
        
        # Test empty voice ID
        with pytest.raises(ValueError, match="Voice ID cannot be empty"):
            validate_voice_id("")
        
        with pytest.raises(ValueError, match="Voice ID cannot be empty"):
            validate_voice_id("   ")
        
        # Test invalid characters
        with pytest.raises(ValueError, match="Invalid voice ID format"):
            validate_voice_id("voice$id")
        
        with pytest.raises(ValueError, match="Invalid voice ID format"):
            validate_voice_id("voice id")  # spaces
        
        # Test length limit
        long_id = "a" * 101
        with pytest.raises(ValueError, match="Voice ID too long"):
            validate_voice_id(long_id)
    
    def test_filename_sanitization(self):
        """Test filename sanitization."""
        # Test normal filename
        assert sanitize_filename("document.pdf") == "document.pdf"
        
        # Test filename with dangerous characters
        assert sanitize_filename("file<>name.txt") == "file__name.txt"
        assert sanitize_filename('file"name.txt') == "file_name.txt"
        assert sanitize_filename("file/name.txt") == "file_name.txt"
        
        # Test path traversal attempts
        assert sanitize_filename("../../../etc/passwd") == "passwd"
        assert sanitize_filename("..\\..\\windows\\system32") == "system32"
        
        # Test hidden file
        assert sanitize_filename(".hidden") == "file_.hidden"
        
        # Test empty filename after sanitization
        assert sanitize_filename("///") == "sanitized_file"
        assert sanitize_filename("") == ValueError
    
    def test_security_validator_api_request(self):
        """Test API request validation."""
        validator = SecurityValidator()
        
        # Test valid request
        valid_data = {
            "text": "Hello world",
            "voice_id": "valid_voice_123",
            "stability": 0.5,
            "similarity_boost": 0.7
        }
        
        result = validator.validate_api_request(valid_data)
        assert result["text"] == "Hello world"
        assert result["voice_id"] == "valid_voice_123"
        assert result["stability"] == 0.5
        
        # Test invalid stability value
        invalid_data = {
            "text": "Hello world",
            "stability": 1.5  # Invalid: > 1.0
        }
        
        with pytest.raises(ValueError, match="stability must be between 0 and 1"):
            validator.validate_api_request(invalid_data)
    
    def test_elevenlabs_input_validation(self):
        """Test ElevenLabs client input validation."""
        client = ElevenLabsClient(api_key="test_key")
        
        # Test empty text
        with pytest.raises(ValueError, match="Text cannot be empty"):
            client.text_to_speech("", "voice_id")
        
        with pytest.raises(ValueError, match="Text cannot be empty"):
            client.text_to_speech("   ", "voice_id")
        
        # Test long text
        long_text = "a" * 5001
        with pytest.raises(ValueError, match="Text too long"):
            client.text_to_speech(long_text, "voice_id")
        
        # Test empty voice ID
        with pytest.raises(ValueError, match="Voice ID cannot be empty"):
            client.text_to_speech("Hello", "")
        
        with pytest.raises(ValueError, match="Voice ID cannot be empty"):
            client.text_to_speech("Hello", "   ")
        
        # Test streaming with invalid chunk size
        with pytest.raises(ValueError, match="Chunk size must be between"):
            list(client.text_to_speech_stream("Hello", "voice_id", chunk_size=0))
        
        with pytest.raises(ValueError, match="Chunk size must be between"):
            list(client.text_to_speech_stream("Hello", "voice_id", chunk_size=20000))


if __name__ == "__main__":
    pytest.main([__file__])