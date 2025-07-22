"""
Security utilities and validation functions.
"""

import os
import re
import logging
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import hashlib
import hmac
import secrets
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class SecurityConfig:
    """Security configuration and constants."""
    
    # File upload limits
    MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB
    MAX_TEXT_LENGTH = 5000  # Characters
    MAX_FILENAME_LENGTH = 255
    
    # Allowed file extensions
    ALLOWED_AUDIO_EXTENSIONS = {'.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac'}
    ALLOWED_VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv'}
    ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    
    # Rate limiting
    DEFAULT_RATE_LIMIT = 100  # requests per minute
    API_RATE_LIMIT = 60  # API calls per minute
    
    # Content validation patterns
    SAFE_FILENAME_PATTERN = re.compile(r'^[a-zA-Z0-9._-]+$')
    SAFE_TEXT_PATTERN = re.compile(r'^[a-zA-Z0-9\s.,!?\'";:()\-_@#$%&*+=\[\]{}|\\~`]+$')


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent security issues.
    
    Args:
        filename: Input filename
    
    Returns:
        Sanitized filename
    
    Raises:
        ValueError: If filename is invalid
    """
    if not filename:
        raise ValueError("Filename cannot be empty")
    
    if len(filename) > SecurityConfig.MAX_FILENAME_LENGTH:
        raise ValueError(f"Filename too long: {len(filename)} (max: {SecurityConfig.MAX_FILENAME_LENGTH})")
    
    # Remove directory traversal attempts
    filename = os.path.basename(filename)
    
    # Remove or replace unsafe characters
    safe_chars = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Ensure it doesn't start with a dot (hidden file)
    if safe_chars.startswith('.'):
        safe_chars = 'file_' + safe_chars
    
    # Ensure it's not empty after sanitization
    if not safe_chars or safe_chars == '_':
        safe_chars = 'sanitized_file'
    
    return safe_chars


def validate_file_path(file_path: str, allowed_extensions: Optional[set] = None) -> Path:
    """
    Validate and sanitize file path.
    
    Args:
        file_path: Input file path
        allowed_extensions: Set of allowed file extensions
    
    Returns:
        Validated Path object
    
    Raises:
        ValueError: If path is invalid or potentially malicious
    """
    if not file_path:
        raise ValueError("File path cannot be empty")
    
    try:
        path = Path(file_path).resolve()
    except (OSError, ValueError) as e:
        raise ValueError(f"Invalid file path: {e}")
    
    # Check if file exists
    if not path.exists():
        raise ValueError(f"File does not exist: {path}")
    
    if not path.is_file():
        raise ValueError(f"Path is not a file: {path}")
    
    # Check file extension if specified
    if allowed_extensions and path.suffix.lower() not in allowed_extensions:
        raise ValueError(f"File type not allowed: {path.suffix}")
    
    # Check file size
    try:
        file_size = path.stat().st_size
        if file_size > SecurityConfig.MAX_FILE_SIZE:
            raise ValueError(f"File too large: {file_size} bytes (max: {SecurityConfig.MAX_FILE_SIZE})")
    except OSError as e:
        raise ValueError(f"Cannot read file: {e}")
    
    return path


def validate_text_input(text: str, max_length: Optional[int] = None) -> str:
    """
    Validate and sanitize text input.
    
    Args:
        text: Input text
        max_length: Maximum allowed length
    
    Returns:
        Validated text
    
    Raises:
        ValueError: If text is invalid
    """
    if text is None:
        raise ValueError("Text cannot be None")
    
    if not isinstance(text, str):
        raise ValueError("Text must be a string")
    
    # Check length
    max_len = max_length or SecurityConfig.MAX_TEXT_LENGTH
    if len(text) > max_len:
        raise ValueError(f"Text too long: {len(text)} characters (max: {max_len})")
    
    # Check for potential injection attempts
    dangerous_patterns = [
        r'<script.*?>.*?</script>',  # Script tags
        r'javascript:',              # JavaScript URLs
        r'data:.*base64',           # Base64 data URLs
        r'eval\s*\(',               # eval() calls
        r'exec\s*\(',               # exec() calls
        r'import\s+',               # import statements
        r'__.*__',                  # Python dunder methods
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            logger.warning(f"Potentially dangerous pattern detected in text: {pattern}")
            raise ValueError("Text contains potentially dangerous content")
    
    return text.strip()


def validate_voice_id(voice_id: str) -> str:
    """
    Validate voice ID format.
    
    Args:
        voice_id: Voice ID to validate
    
    Returns:
        Validated voice ID
    
    Raises:
        ValueError: If voice ID is invalid
    """
    if not voice_id or not voice_id.strip():
        raise ValueError("Voice ID cannot be empty")
    
    voice_id = voice_id.strip()
    
    # ElevenLabs voice IDs are typically alphanumeric with limited special chars
    if not re.match(r'^[a-zA-Z0-9_-]+$', voice_id):
        raise ValueError("Invalid voice ID format")
    
    if len(voice_id) > 100:  # Reasonable limit
        raise ValueError(f"Voice ID too long: {len(voice_id)}")
    
    return voice_id


def validate_url(url: str, allowed_schemes: Optional[List[str]] = None) -> str:
    """
    Validate URL format and scheme.
    
    Args:
        url: URL to validate
        allowed_schemes: List of allowed URL schemes
    
    Returns:
        Validated URL
    
    Raises:
        ValueError: If URL is invalid
    """
    if not url or not url.strip():
        raise ValueError("URL cannot be empty")
    
    url = url.strip()
    
    try:
        parsed = urlparse(url)
    except Exception as e:
        raise ValueError(f"Invalid URL format: {e}")
    
    if not parsed.scheme or not parsed.netloc:
        raise ValueError("URL must have scheme and netloc")
    
    allowed = allowed_schemes or ['http', 'https']
    if parsed.scheme.lower() not in allowed:
        raise ValueError(f"URL scheme not allowed: {parsed.scheme}")
    
    return url


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token.
    
    Args:
        length: Token length in bytes
    
    Returns:
        Hex-encoded secure token
    """
    return secrets.token_hex(length)


def verify_hmac_signature(message: bytes, signature: str, secret: str) -> bool:
    """
    Verify HMAC signature.
    
    Args:
        message: Original message
        signature: HMAC signature to verify
        secret: Secret key
    
    Returns:
        True if signature is valid
    """
    try:
        expected = hmac.new(
            secret.encode('utf-8'),
            message,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected)
    except Exception:
        return False


def hash_content(content: Union[str, bytes]) -> str:
    """
    Generate SHA-256 hash of content.
    
    Args:
        content: Content to hash
    
    Returns:
        Hex-encoded hash
    """
    if isinstance(content, str):
        content = content.encode('utf-8')
    
    return hashlib.sha256(content).hexdigest()


class SecurityValidator:
    """Security validation utility class."""
    
    def __init__(self):
        self.config = SecurityConfig()
    
    def validate_api_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate API request data.
        
        Args:
            data: Request data dictionary
        
        Returns:
            Validated and sanitized data
        
        Raises:
            ValueError: If validation fails
        """
        validated = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                # Validate string fields
                if key in ['text', 'description', 'name']:
                    validated[key] = validate_text_input(value)
                elif key == 'voice_id':
                    validated[key] = validate_voice_id(value)
                elif key in ['url', 'callback_url']:
                    validated[key] = validate_url(value)
                else:
                    validated[key] = validate_text_input(value, max_length=1000)
            elif isinstance(value, (int, float)):
                # Validate numeric fields
                if key in ['stability', 'similarity_boost', 'style']:
                    if not 0 <= value <= 1:
                        raise ValueError(f"{key} must be between 0 and 1")
                validated[key] = value
            elif isinstance(value, list):
                # Validate list fields
                if len(value) > 100:  # Reasonable limit
                    raise ValueError(f"List {key} too long: {len(value)}")
                validated[key] = value
            else:
                validated[key] = value
        
        return validated
    
    def validate_file_upload(self, file_path: str, file_type: str) -> Path:
        """
        Validate file upload.
        
        Args:
            file_path: Path to uploaded file
            file_type: Expected file type ('audio', 'video', 'image')
        
        Returns:
            Validated Path object
        
        Raises:
            ValueError: If validation fails
        """
        type_extensions = {
            'audio': self.config.ALLOWED_AUDIO_EXTENSIONS,
            'video': self.config.ALLOWED_VIDEO_EXTENSIONS,
            'image': self.config.ALLOWED_IMAGE_EXTENSIONS,
        }
        
        allowed_extensions = type_extensions.get(file_type)
        if not allowed_extensions:
            raise ValueError(f"Unknown file type: {file_type}")
        
        return validate_file_path(file_path, allowed_extensions)


# Global validator instance
security_validator = SecurityValidator()