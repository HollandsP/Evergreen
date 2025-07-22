"""
Security middleware for API endpoints.
"""

import time
import logging
from typing import Dict, Optional, Set
from fastapi import HTTPException, Request, Response
from fastapi.security import HTTPBearer
from collections import defaultdict, deque
import hashlib
import hmac
from datetime import datetime, timedelta

from .security import SecurityConfig, security_validator

logger = logging.getLogger(__name__)


class SecurityHeaders:
    """Security headers for HTTP responses."""
    
    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """Get recommended security headers."""
        return {
            # Prevent XSS attacks
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            
            # HTTPS enforcement
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            
            # Content Security Policy
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "media-src 'self'; "
                "object-src 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            ),
            
            # Referrer policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Feature policy
            "Permissions-Policy": (
                "camera=(), "
                "microphone=(), "
                "geolocation=(), "
                "payment=(), "
                "usb=(), "
                "magnetometer=(), "
                "gyroscope=(), "
                "speaker=()"
            ),
            
            # Cross-origin policies
            "Cross-Origin-Embedder-Policy": "require-corp",
            "Cross-Origin-Opener-Policy": "same-origin",
            "Cross-Origin-Resource-Policy": "same-origin"
        }


class RateLimiter:
    """Rate limiting implementation."""
    
    def __init__(self, max_requests: int = 100, window_minutes: int = 1):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests per window
            window_minutes: Time window in minutes
        """
        self.max_requests = max_requests
        self.window_seconds = window_minutes * 60
        self.requests = defaultdict(deque)  # IP -> deque of timestamps
    
    def is_allowed(self, client_ip: str) -> bool:
        """
        Check if request is allowed for client IP.
        
        Args:
            client_ip: Client IP address
        
        Returns:
            True if request is allowed
        """
        now = time.time()
        client_requests = self.requests[client_ip]
        
        # Remove old requests outside the window
        while client_requests and client_requests[0] < now - self.window_seconds:
            client_requests.popleft()
        
        # Check if under limit
        if len(client_requests) < self.max_requests:
            client_requests.append(now)
            return True
        
        return False
    
    def get_reset_time(self, client_ip: str) -> Optional[float]:
        """Get timestamp when rate limit resets for client."""
        client_requests = self.requests[client_ip]
        if client_requests:
            return client_requests[0] + self.window_seconds
        return None


class CSRFProtection:
    """CSRF token validation."""
    
    def __init__(self, secret_key: str):
        """Initialize CSRF protection with secret key."""
        self.secret_key = secret_key.encode('utf-8')
    
    def generate_token(self, session_id: str) -> str:
        """Generate CSRF token for session."""
        timestamp = str(int(time.time()))
        message = f"{session_id}:{timestamp}"
        signature = hmac.new(
            self.secret_key,
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return f"{timestamp}:{signature}"
    
    def validate_token(self, token: str, session_id: str, max_age: int = 3600) -> bool:
        """
        Validate CSRF token.
        
        Args:
            token: CSRF token to validate
            session_id: Session ID
            max_age: Maximum token age in seconds
        
        Returns:
            True if token is valid
        """
        try:
            if ':' not in token:
                return False
            
            timestamp_str, signature = token.rsplit(':', 1)
            timestamp = int(timestamp_str)
            
            # Check if token is not expired
            if time.time() - timestamp > max_age:
                return False
            
            # Verify signature
            message = f"{session_id}:{timestamp_str}"
            expected_signature = hmac.new(
                self.secret_key,
                message.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
            
        except (ValueError, TypeError):
            return False


class SecurityMiddleware:
    """Main security middleware."""
    
    def __init__(self, secret_key: str = "default-secret-change-in-production"):
        """Initialize security middleware."""
        self.rate_limiter = RateLimiter(
            max_requests=SecurityConfig.DEFAULT_RATE_LIMIT,
            window_minutes=1
        )
        self.api_rate_limiter = RateLimiter(
            max_requests=SecurityConfig.API_RATE_LIMIT,
            window_minutes=1
        )
        self.csrf_protection = CSRFProtection(secret_key)
        self.blocked_ips: Set[str] = set()
        
    def get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check for forwarded headers (for proxy setups)
        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('x-real-ip')
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        if hasattr(request.client, 'host'):
            return request.client.host
        
        return 'unknown'
    
    def is_api_endpoint(self, path: str) -> bool:
        """Check if path is an API endpoint."""
        return path.startswith('/api/') or path.startswith('/v1/')
    
    async def __call__(self, request: Request, call_next):
        """Process request through security middleware."""
        client_ip = self.get_client_ip(request)
        
        # Check if IP is blocked
        if client_ip in self.blocked_ips:
            logger.warning(f"Blocked IP attempted access: {client_ip}")
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Rate limiting
        rate_limiter = (
            self.api_rate_limiter if self.is_api_endpoint(request.url.path)
            else self.rate_limiter
        )
        
        if not rate_limiter.is_allowed(client_ip):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            
            # Add rate limit headers
            reset_time = rate_limiter.get_reset_time(client_ip)
            headers = {
                "X-RateLimit-Limit": str(rate_limiter.max_requests),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(reset_time)) if reset_time else "0"
            }
            
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers=headers
            )
        
        # Content length check
        content_length = request.headers.get('content-length')
        if content_length and int(content_length) > SecurityConfig.MAX_FILE_SIZE:
            logger.warning(f"Request too large: {content_length} bytes from {client_ip}")
            raise HTTPException(status_code=413, detail="Request entity too large")
        
        # CSRF protection for POST/PUT/DELETE requests
        if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            csrf_token = request.headers.get('X-CSRF-Token')
            session_id = request.headers.get('X-Session-ID', client_ip)
            
            if not csrf_token or not self.csrf_protection.validate_token(csrf_token, session_id):
                logger.warning(f"CSRF token validation failed for {client_ip}")
                # For API endpoints, we might want to be more lenient
                if not self.is_api_endpoint(request.url.path):
                    raise HTTPException(status_code=403, detail="CSRF token invalid")
        
        # Log security events
        user_agent = request.headers.get('user-agent', 'unknown')
        logger.info(f"Request: {request.method} {request.url.path} from {client_ip} ({user_agent})")
        
        # Process request
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Add security headers
        for name, value in SecurityHeaders.get_security_headers().items():
            response.headers[name] = value
        
        # Add custom headers
        response.headers["X-Request-ID"] = hashlib.sha256(
            f"{client_ip}:{start_time}:{request.url.path}".encode()
        ).hexdigest()[:16]
        
        response.headers["X-Process-Time"] = str(round(process_time, 4))
        
        # Rate limit headers
        remaining = rate_limiter.max_requests - len(rate_limiter.requests[client_ip])
        response.headers["X-RateLimit-Limit"] = str(rate_limiter.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        
        reset_time = rate_limiter.get_reset_time(client_ip)
        if reset_time:
            response.headers["X-RateLimit-Reset"] = str(int(reset_time))
        
        return response
    
    def block_ip(self, ip: str, reason: str = "Security violation"):
        """Block an IP address."""
        self.blocked_ips.add(ip)
        logger.warning(f"Blocked IP {ip}: {reason}")
    
    def unblock_ip(self, ip: str):
        """Unblock an IP address."""
        self.blocked_ips.discard(ip)
        logger.info(f"Unblocked IP {ip}")
    
    def generate_csrf_token(self, session_id: str) -> str:
        """Generate CSRF token for session."""
        return self.csrf_protection.generate_token(session_id)


class InputSanitizer:
    """Request input sanitization."""
    
    @staticmethod
    async def sanitize_request(request: Request) -> Dict:
        """
        Sanitize request data.
        
        Args:
            request: FastAPI request object
        
        Returns:
            Sanitized request data
        """
        # Get JSON body if present
        data = {}
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                content_type = request.headers.get('content-type', '')
                if 'application/json' in content_type:
                    data = await request.json()
                elif 'application/x-www-form-urlencoded' in content_type:
                    form = await request.form()
                    data = dict(form)
            except Exception as e:
                logger.warning(f"Failed to parse request body: {e}")
                raise HTTPException(status_code=400, detail="Invalid request format")
        
        # Sanitize data using security validator
        if data:
            try:
                return security_validator.validate_api_request(data)
            except ValueError as e:
                logger.warning(f"Request validation failed: {e}")
                raise HTTPException(status_code=400, detail=str(e))
        
        return data


# Global security middleware instance
security_middleware = None

def get_security_middleware(secret_key: str = None) -> SecurityMiddleware:
    """Get or create security middleware instance."""
    global security_middleware
    if security_middleware is None:
        security_middleware = SecurityMiddleware(secret_key)
    return security_middleware