"""
Video Streaming Utility - Optimized Video Delivery with Range Support

Provides efficient video streaming with HTTP range requests, chunk-based delivery,
and adaptive quality for smooth playback of large video files.

Performance Targets:
- 4K video streaming without buffering
- Range request support for seeking
- Adaptive bitrate based on connection
- Memory usage: < 50MB during streaming
- Response time: < 100ms for range requests
"""

import os
import mimetypes
import logging
from typing import Optional, Tuple, Dict, Any, AsyncGenerator, BinaryIO
from pathlib import Path
from dataclasses import dataclass
import asyncio
import aiofiles
from io import BytesIO

from fastapi import Request, Response, HTTPException
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)

@dataclass
class VideoMetadata:
    """Video file metadata for streaming optimization."""
    file_path: str
    file_size: int
    duration: Optional[float] = None
    bitrate: Optional[int] = None
    resolution: Optional[Tuple[int, int]] = None
    format: Optional[str] = None
    last_modified: float = 0
    
    @classmethod
    async def from_file(cls, file_path: str) -> 'VideoMetadata':
        """Create metadata from video file."""
        try:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"Video file not found: {file_path}")
            
            stat = path.stat()
            
            # Basic metadata
            metadata = cls(
                file_path=file_path,
                file_size=stat.st_size,
                last_modified=stat.st_mtime,
                format=path.suffix.lower()
            )
            
            # Try to get video-specific metadata (requires ffprobe)
            try:
                await metadata._extract_video_metadata()
            except Exception as e:
                logger.debug(f"Could not extract video metadata for {file_path}: {e}")
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error creating video metadata for {file_path}: {e}")
            raise

    async def _extract_video_metadata(self):
        """Extract video metadata using ffprobe if available."""
        try:
            import subprocess
            import json
            
            # Use ffprobe to get video information
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', self.file_path
            ]
            
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            stdout, _ = await result.communicate()
            
            if result.returncode == 0:
                data = json.loads(stdout.decode())
                
                # Extract format information
                format_info = data.get('format', {})
                self.duration = float(format_info.get('duration', 0))
                self.bitrate = int(format_info.get('bit_rate', 0))
                
                # Extract video stream information
                for stream in data.get('streams', []):
                    if stream.get('codec_type') == 'video':
                        width = stream.get('width')
                        height = stream.get('height')
                        if width and height:
                            self.resolution = (width, height)
                        break
                        
        except Exception as e:
            logger.debug(f"ffprobe not available or failed: {e}")

@dataclass
class StreamingConfig:
    """Configuration for video streaming."""
    chunk_size: int = 1024 * 1024  # 1MB chunks
    max_chunk_size: int = 8 * 1024 * 1024  # 8MB max
    min_chunk_size: int = 64 * 1024  # 64KB min
    enable_range_requests: bool = True
    enable_compression: bool = False
    cache_control_max_age: int = 3600  # 1 hour
    adaptive_chunk_size: bool = True
    
    def get_adaptive_chunk_size(self, file_size: int, connection_speed: Optional[str] = None) -> int:
        """Calculate optimal chunk size based on file size and connection."""
        if not self.adaptive_chunk_size:
            return self.chunk_size
        
        # Base chunk size on file size
        if file_size < 10 * 1024 * 1024:  # < 10MB
            chunk_size = 256 * 1024  # 256KB
        elif file_size < 100 * 1024 * 1024:  # < 100MB
            chunk_size = 512 * 1024  # 512KB
        elif file_size < 1024 * 1024 * 1024:  # < 1GB
            chunk_size = 1024 * 1024  # 1MB
        else:  # >= 1GB
            chunk_size = 2 * 1024 * 1024  # 2MB
        
        # Adjust for connection speed if available
        if connection_speed:
            speed_multipliers = {
                'slow': 0.5,
                'fast': 1.5,
                'very_fast': 2.0
            }
            multiplier = speed_multipliers.get(connection_speed, 1.0)
            chunk_size = int(chunk_size * multiplier)
        
        # Ensure within bounds
        return max(self.min_chunk_size, min(self.max_chunk_size, chunk_size))

class RangeRequest:
    """HTTP Range request parser and handler."""
    
    def __init__(self, range_header: str, file_size: int):
        """
        Initialize range request.
        
        Args:
            range_header: HTTP Range header value
            file_size: Total file size in bytes
        """
        self.range_header = range_header
        self.file_size = file_size
        self.start = 0
        self.end = file_size - 1
        self.length = file_size
        self.is_partial = False
        
        self._parse_range()
    
    def _parse_range(self):
        """Parse HTTP Range header."""
        try:
            if not self.range_header or not self.range_header.startswith('bytes='):
                return
            
            range_spec = self.range_header[6:]  # Remove 'bytes='
            
            # Handle multiple ranges (take first one)
            range_parts = range_spec.split(',')[0].strip()
            
            if '-' not in range_parts:
                return
            
            start_str, end_str = range_parts.split('-', 1)
            
            # Parse start
            if start_str:
                self.start = int(start_str)
                self.is_partial = True
            
            # Parse end
            if end_str:
                self.end = int(end_str)
                self.is_partial = True
            else:
                self.end = self.file_size - 1
            
            # Validate and adjust bounds
            self.start = max(0, min(self.start, self.file_size - 1))
            self.end = max(self.start, min(self.end, self.file_size - 1))
            self.length = self.end - self.start + 1
            
            logger.debug(f"Parsed range: {self.start}-{self.end}/{self.file_size}")
            
        except (ValueError, IndexError) as e:
            logger.warning(f"Invalid range header '{self.range_header}': {e}")
            # Reset to full file on invalid range
            self.start = 0
            self.end = self.file_size - 1
            self.length = self.file_size
            self.is_partial = False
    
    def get_content_range_header(self) -> str:
        """Get Content-Range header value."""
        return f"bytes {self.start}-{self.end}/{self.file_size}"
    
    def is_satisfiable(self) -> bool:
        """Check if range request is satisfiable."""
        return self.start < self.file_size and self.end < self.file_size and self.start <= self.end

class VideoStreamer:
    """
    High-performance video streaming service with range support.
    
    Features:
    - HTTP range request support for seeking
    - Adaptive chunk sizing based on file size and connection
    - Memory-efficient streaming for large files
    - Caching headers for performance
    - Error handling and recovery
    """
    
    def __init__(self, config: Optional[StreamingConfig] = None):
        """Initialize video streamer with configuration."""
        self.config = config or StreamingConfig()
        self._file_cache: Dict[str, VideoMetadata] = {}
        self._cache_ttl = 300  # 5 minutes
        
        logger.info("Initialized VideoStreamer with range request support")
    
    async def stream_video(self, 
                          file_path: str, 
                          request: Request) -> StreamingResponse:
        """
        Stream video file with range support.
        
        Args:
            file_path: Path to video file
            request: FastAPI request object
            
        Returns:
            StreamingResponse with video content
        """
        try:
            # Get video metadata
            metadata = await self._get_video_metadata(file_path)
            
            # Parse range request
            range_header = request.headers.get('range')
            range_request = RangeRequest(range_header or '', metadata.file_size)
            
            # Validate range
            if range_request.is_partial and not range_request.is_satisfiable():
                raise HTTPException(
                    status_code=416,
                    detail="Range Not Satisfiable",
                    headers={
                        'Content-Range': f"bytes */{metadata.file_size}",
                        'Accept-Ranges': 'bytes'
                    }
                )
            
            # Determine content type
            content_type = self._get_content_type(file_path)
            
            # Get adaptive chunk size
            connection_speed = self._detect_connection_speed(request)
            chunk_size = self.config.get_adaptive_chunk_size(
                metadata.file_size, 
                connection_speed
            )
            
            # Create streaming response
            headers = self._build_response_headers(metadata, range_request)
            status_code = 206 if range_request.is_partial else 200
            
            # Create async generator for file chunks
            generator = self._create_file_generator(
                file_path, 
                range_request, 
                chunk_size
            )
            
            logger.info(f"Streaming video {file_path}: "
                       f"{range_request.start}-{range_request.end}/{metadata.file_size}, "
                       f"chunk_size={chunk_size}")
            
            return StreamingResponse(
                generator,
                status_code=status_code,
                headers=headers,
                media_type=content_type
            )
            
        except HTTPException:
            raise
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Video file not found")
        except Exception as e:
            logger.error(f"Error streaming video {file_path}: {e}")
            raise HTTPException(status_code=500, detail=f"Streaming error: {str(e)}")
    
    async def get_video_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get video file information for client.
        
        Args:
            file_path: Path to video file
            
        Returns:
            Dictionary with video metadata
        """
        try:
            metadata = await self._get_video_metadata(file_path)
            
            return {
                'file_path': file_path,
                'file_size': metadata.file_size,
                'duration': metadata.duration,
                'bitrate': metadata.bitrate,
                'resolution': metadata.resolution,
                'format': metadata.format,
                'supports_range_requests': self.config.enable_range_requests,
                'recommended_chunk_size': self.config.get_adaptive_chunk_size(metadata.file_size)
            }
            
        except Exception as e:
            logger.error(f"Error getting video info for {file_path}: {e}")
            raise HTTPException(status_code=500, detail=f"Video info error: {str(e)}")
    
    async def _get_video_metadata(self, file_path: str) -> VideoMetadata:
        """Get cached or fresh video metadata."""
        # Check cache first
        if file_path in self._file_cache:
            cached = self._file_cache[file_path]
            
            # Verify file hasn't changed
            try:
                current_mtime = Path(file_path).stat().st_mtime
                if current_mtime == cached.last_modified:
                    return cached
            except Exception:
                pass  # File might not exist, remove from cache below
        
        # Get fresh metadata
        metadata = await VideoMetadata.from_file(file_path)
        
        # Cache with TTL cleanup
        self._file_cache[file_path] = metadata
        
        # Simple cache cleanup (remove old entries periodically)
        if len(self._file_cache) > 100:
            # Remove oldest 20% of entries
            items = list(self._file_cache.items())
            items.sort(key=lambda x: x[1].last_modified)
            for path, _ in items[:20]:
                self._file_cache.pop(path, None)
        
        return metadata
    
    def _get_content_type(self, file_path: str) -> str:
        """Determine MIME type for video file."""
        content_type, _ = mimetypes.guess_type(file_path)
        
        if not content_type:
            # Default based on extension
            ext = Path(file_path).suffix.lower()
            content_type = {
                '.mp4': 'video/mp4',
                '.avi': 'video/x-msvideo',
                '.mov': 'video/quicktime',
                '.mkv': 'video/x-matroska',
                '.webm': 'video/webm'
            }.get(ext, 'application/octet-stream')
        
        return content_type
    
    def _detect_connection_speed(self, request: Request) -> Optional[str]:
        """Detect client connection speed from headers."""
        # Check for connection speed hints in headers
        user_agent = request.headers.get('user-agent', '').lower()
        
        # Simple heuristics based on user agent
        if 'mobile' in user_agent or 'android' in user_agent:
            return 'slow'
        elif 'chrome' in user_agent or 'firefox' in user_agent:
            return 'fast'
        
        # Check for network information API headers (if available)
        connection_type = request.headers.get('save-data')
        if connection_type:
            return 'slow'
        
        return None
    
    def _build_response_headers(self, 
                               metadata: VideoMetadata, 
                               range_request: RangeRequest) -> Dict[str, str]:
        """Build HTTP response headers for video streaming."""
        headers = {
            'Accept-Ranges': 'bytes',
            'Cache-Control': f'public, max-age={self.config.cache_control_max_age}',
            'Content-Length': str(range_request.length)
        }
        
        # Add range headers for partial content
        if range_request.is_partial:
            headers['Content-Range'] = range_request.get_content_range_header()
        
        # Add last modified for caching
        if metadata.last_modified:
            from email.utils import formatdate
            headers['Last-Modified'] = formatdate(metadata.last_modified, usegmt=True)
        
        # Add video-specific headers
        if metadata.duration:
            headers['X-Content-Duration'] = str(metadata.duration)
        
        return headers
    
    async def _create_file_generator(self, 
                                   file_path: str, 
                                   range_request: RangeRequest, 
                                   chunk_size: int) -> AsyncGenerator[bytes, None]:
        """Create async generator for file chunks."""
        try:
            async with aiofiles.open(file_path, 'rb') as file:
                # Seek to start position
                await file.seek(range_request.start)
                
                bytes_remaining = range_request.length
                
                while bytes_remaining > 0:
                    # Read chunk (don't exceed remaining bytes)
                    read_size = min(chunk_size, bytes_remaining)
                    chunk = await file.read(read_size)
                    
                    if not chunk:
                        break
                    
                    yield chunk
                    bytes_remaining -= len(chunk)
                    
                    # Small delay to prevent overwhelming the client
                    if bytes_remaining > 0:
                        await asyncio.sleep(0.001)  # 1ms delay
                        
        except Exception as e:
            logger.error(f"Error in file generator for {file_path}: {e}")
            raise

class VideoStreamingManager:
    """
    Manager class for video streaming operations.
    
    Provides high-level interface for video streaming with caching,
    performance monitoring, and error handling.
    """
    
    def __init__(self):
        """Initialize video streaming manager."""
        self.streamer = VideoStreamer()
        self._stream_stats = {
            'total_streams': 0,
            'total_bytes_served': 0,
            'range_requests': 0,
            'errors': 0
        }
        
        logger.info("Initialized VideoStreamingManager")
    
    async def stream_scene_video(self, 
                                scene_id: str, 
                                project_id: str, 
                                request: Request) -> StreamingResponse:
        """
        Stream a scene video file with automatic path resolution.
        
        Args:
            scene_id: Scene identifier
            project_id: Project identifier  
            request: FastAPI request
            
        Returns:
            StreamingResponse for video
        """
        try:
            # Import here to avoid circular imports
            from src.services.scene_index_manager import get_scene_index_manager
            
            # Get scene video path using index manager
            scene_manager = await get_scene_index_manager()
            video_path = await scene_manager.find_scene_video(scene_id, project_id)
            
            if not video_path:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Video not found for scene {scene_id} in project {project_id}"
                )
            
            # Update stats
            self._stream_stats['total_streams'] += 1
            if request.headers.get('range'):
                self._stream_stats['range_requests'] += 1
            
            # Stream the video
            response = await self.streamer.stream_video(video_path, request)
            
            # Track bytes served (estimate)
            content_length = response.headers.get('content-length')
            if content_length:
                self._stream_stats['total_bytes_served'] += int(content_length)
            
            return response
            
        except HTTPException:
            self._stream_stats['errors'] += 1
            raise
        except Exception as e:
            self._stream_stats['errors'] += 1
            logger.error(f"Error streaming scene video {scene_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Streaming failed: {str(e)}")
    
    async def get_streaming_stats(self) -> Dict[str, Any]:
        """Get video streaming statistics."""
        return {
            'statistics': self._stream_stats.copy(),
            'configuration': {
                'chunk_size': self.streamer.config.chunk_size,
                'range_requests_enabled': self.streamer.config.enable_range_requests,
                'adaptive_chunk_size': self.streamer.config.adaptive_chunk_size,
                'cache_max_age': self.streamer.config.cache_control_max_age
            },
            'performance': {
                'cache_size': len(self.streamer._file_cache),
                'average_chunk_size': self.streamer.config.chunk_size
            }
        }

# Global instance
_video_streaming_manager: Optional[VideoStreamingManager] = None

def get_video_streaming_manager() -> VideoStreamingManager:
    """Get global video streaming manager instance."""
    global _video_streaming_manager
    
    if _video_streaming_manager is None:
        _video_streaming_manager = VideoStreamingManager()
    
    return _video_streaming_manager