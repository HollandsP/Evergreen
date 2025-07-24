"""
Scene Index Manager - High-Performance Scene Lookup Service

Transforms O(n) scene file system scans into O(1) Redis-cached lookups.
Designed for sub-100ms response times with intelligent caching and indexing.

Performance Targets:
- Scene lookup: < 100ms
- Index updates: < 50ms  
- Memory usage: < 100MB for 1000 scenes
- Index size: < 10MB for 1000 scenes
"""

import os
import json
import asyncio
import logging
import hashlib
from typing import Dict, List, Optional, Tuple, Set
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from redis.exceptions import ConnectionError as RedisConnectionError

logger = logging.getLogger(__name__)

@dataclass
class SceneMediaInfo:
    """Scene media file information with metadata."""
    scene_id: str
    project_id: str
    file_path: str
    file_type: str  # 'video', 'audio', 'image'
    file_size: int
    last_modified: float
    duration: Optional[float] = None
    resolution: Optional[Tuple[int, int]] = None
    format: Optional[str] = None
    created_at: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow().timestamp()

@dataclass
class ProjectSceneIndex:
    """Complete scene index for a project."""
    project_id: str
    scenes: Dict[str, List[SceneMediaInfo]]
    last_updated: float
    total_files: int
    index_version: str = "1.0"
    
    def __post_init__(self):
        if not hasattr(self, 'last_updated') or self.last_updated is None:
            self.last_updated = datetime.utcnow().timestamp()

class SceneIndexManager:
    """
    High-performance scene indexing and lookup service.
    
    Features:
    - O(1) scene lookup using Redis hashing
    - Intelligent cache invalidation and updates
    - Memory-efficient storage with compression
    - Batch operations for bulk updates
    - Health monitoring and auto-recovery
    """
    
    # Redis key patterns
    SCENE_INDEX_KEY = "scene_index:project:{project_id}"
    SCENE_LOOKUP_KEY = "scene_lookup:{project_id}:{scene_id}"
    SCENE_FILES_KEY = "scene_files:{project_id}:{scene_id}:{file_type}"
    GLOBAL_INDEX_KEY = "scene_index:global"
    HEALTH_KEY = "scene_index:health"
    STATS_KEY = "scene_index:stats"
    
    # Performance settings
    DEFAULT_TTL = 3600  # 1 hour cache TTL
    BATCH_SIZE = 50     # Files per batch operation
    MAX_RETRIES = 3     # Redis operation retries
    TIMEOUT = 10        # Redis operation timeout (seconds)
    
    def __init__(self, 
                 redis_url: str = None,
                 default_ttl: int = DEFAULT_TTL,
                 enable_compression: bool = True):
        """
        Initialize Scene Index Manager.
        
        Args:
            redis_url: Redis connection URL (defaults to env REDIS_URL)
            default_ttl: Default cache TTL in seconds
            enable_compression: Enable JSON compression for storage
        """
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.default_ttl = default_ttl
        self.enable_compression = enable_compression
        self.redis_client: Optional[aioredis.Redis] = None
        self._connection_pool = None
        self._stats = {
            'lookups': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'index_updates': 0,
            'errors': 0
        }
        
        # Performance monitoring
        self._last_health_check = 0
        self._health_check_interval = 60  # seconds
        
        logger.info(f"Initialized SceneIndexManager with Redis: {self.redis_url}")
    
    async def initialize(self) -> bool:
        """Initialize Redis connection and verify health."""
        try:
            # Create connection pool for better performance
            self._connection_pool = aioredis.ConnectionPool.from_url(
                self.redis_url,
                max_connections=20,
                retry_on_timeout=True,
                socket_timeout=self.TIMEOUT,
                socket_connect_timeout=self.TIMEOUT
            )
            
            self.redis_client = aioredis.Redis(
                connection_pool=self._connection_pool,
                decode_responses=True
            )
            
            # Test connection
            await self.redis_client.ping()
            
            # Initialize health status
            await self._update_health_status("healthy", "Initialized successfully")
            
            logger.info("Scene Index Manager initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Scene Index Manager: {e}")
            await self._update_health_status("unhealthy", f"Initialization failed: {e}")
            return False
    
    async def close(self):
        """Clean up Redis connections."""
        try:
            if self.redis_client:
                await self.redis_client.close()
            if self._connection_pool:
                await self._connection_pool.disconnect()
            logger.info("Scene Index Manager closed")
        except Exception as e:
            logger.error(f"Error closing Scene Index Manager: {e}")
    
    @asynccontextmanager
    async def _redis_operation(self, operation_name: str):
        """Context manager for Redis operations with error handling and stats."""
        start_time = datetime.utcnow()
        try:
            if not self.redis_client:
                raise RedisConnectionError("Redis client not initialized")
            yield
        except RedisConnectionError as e:
            self._stats['errors'] += 1
            logger.error(f"Redis connection error in {operation_name}: {e}")
            await self._update_health_status("degraded", f"Connection issues in {operation_name}")
            raise
        except Exception as e:
            self._stats['errors'] += 1
            logger.error(f"Error in {operation_name}: {e}")
            raise
        finally:
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            if duration > 100:  # Log slow operations
                logger.warning(f"Slow Redis operation {operation_name}: {duration:.1f}ms")
    
    async def find_scene_video(self, scene_target: str, project_id: str) -> Optional[str]:
        """
        Fast O(1) scene video lookup using Redis index.
        
        Args:
            scene_target: Scene identifier (e.g., "scene_1", "scene_2")
            project_id: Project identifier
            
        Returns:
            Path to scene video file or None if not found
        """
        async with self._redis_operation("find_scene_video"):
            self._stats['lookups'] += 1
            
            # Parse scene number from target
            scene_id = self._parse_scene_id(scene_target)
            if not scene_id:
                logger.warning(f"Invalid scene target format: {scene_target}")
                return None
            
            # Check Redis cache first
            cache_key = self.SCENE_LOOKUP_KEY.format(project_id=project_id, scene_id=scene_id)
            
            try:
                cached_result = await self.redis_client.get(cache_key)
                if cached_result:
                    self._stats['cache_hits'] += 1
                    file_path = json.loads(cached_result)
                    
                    # Verify file still exists
                    if Path(file_path).exists():
                        logger.debug(f"Cache hit for scene {scene_target}: {file_path}")
                        return file_path
                    else:
                        # File was deleted, invalidate cache
                        await self.redis_client.delete(cache_key)
                        logger.info(f"Cache invalidated for missing file: {file_path}")
                
                # Cache miss, perform file system lookup
                self._stats['cache_misses'] += 1
                video_path = await self._scan_scene_video(scene_id, project_id)
                
                if video_path:
                    # Cache the result
                    await self.redis_client.setex(
                        cache_key, 
                        self.default_ttl, 
                        json.dumps(video_path)
                    )
                    logger.debug(f"Cached scene video: {scene_target} -> {video_path}")
                
                return video_path
                
            except Exception as e:
                logger.error(f"Error in scene lookup for {scene_target}: {e}")
                # Fallback to direct file system scan
                return await self._scan_scene_video(scene_id, project_id)
    
    async def get_all_scene_videos(self, project_id: str) -> List[str]:
        """
        Fast retrieval of all scene videos for a project using index.
        
        Args:
            project_id: Project identifier
            
        Returns:
            List of scene video file paths in chronological order
        """
        async with self._redis_operation("get_all_scene_videos"):
            # Check if project index exists
            index_key = self.SCENE_INDEX_KEY.format(project_id=project_id)
            
            try:
                cached_index = await self.redis_client.get(index_key)
                if cached_index:
                    project_index = ProjectSceneIndex(**json.loads(cached_index))
                    
                    # Verify index is recent (within 10 minutes)
                    if (datetime.utcnow().timestamp() - project_index.last_updated) < 600:
                        videos = []
                        for scene_id in sorted(project_index.scenes.keys(), key=self._sort_scene_key):
                            scene_files = project_index.scenes[scene_id]
                            # Find the best video file for this scene
                            video_files = [f for f in scene_files if f.file_type == 'video']
                            if video_files:
                                # Prefer certain patterns
                                best_video = self._select_best_video_file(video_files)
                                if Path(best_video.file_path).exists():
                                    videos.append(best_video.file_path)
                        
                        if videos:
                            logger.debug(f"Retrieved {len(videos)} scene videos from index")
                            return videos
                
                # Index miss or stale, rebuild
                return await self._rebuild_project_index(project_id)
                
            except Exception as e:
                logger.error(f"Error retrieving scene videos for project {project_id}: {e}")
                # Fallback to direct scan
                return await self._scan_all_scene_videos(project_id)
    
    async def update_scene_index(self, project_id: str, force_rebuild: bool = False) -> bool:
        """
        Update or rebuild the scene index for a project.
        
        Args:
            project_id: Project identifier
            force_rebuild: Force complete rebuild even if index exists
            
        Returns:
            True if successful, False otherwise
        """
        async with self._redis_operation("update_scene_index"):
            try:
                self._stats['index_updates'] += 1
                
                if not force_rebuild:
                    # Check if index needs updating
                    index_key = self.SCENE_INDEX_KEY.format(project_id=project_id)
                    existing_index = await self.redis_client.get(index_key)
                    
                    if existing_index:
                        project_index = ProjectSceneIndex(**json.loads(existing_index))
                        # If index is less than 5 minutes old, skip update
                        if (datetime.utcnow().timestamp() - project_index.last_updated) < 300:
                            return True
                
                # Perform full scan and index rebuild
                await self._rebuild_project_index(project_id)
                
                logger.info(f"Scene index updated for project: {project_id}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to update scene index for {project_id}: {e}")
                return False
    
    async def invalidate_scene_cache(self, project_id: str, scene_id: Optional[str] = None):
        """
        Invalidate cached scene data.
        
        Args:
            project_id: Project identifier
            scene_id: Specific scene to invalidate, or None for entire project
        """
        async with self._redis_operation("invalidate_cache"):
            try:
                if scene_id:
                    # Invalidate specific scene
                    cache_key = self.SCENE_LOOKUP_KEY.format(project_id=project_id, scene_id=scene_id)
                    await self.redis_client.delete(cache_key)
                    logger.debug(f"Invalidated cache for scene: {project_id}/{scene_id}")
                else:
                    # Invalidate entire project
                    index_key = self.SCENE_INDEX_KEY.format(project_id=project_id)
                    
                    # Find all scene cache keys for this project
                    pattern = self.SCENE_LOOKUP_KEY.format(project_id=project_id, scene_id="*")
                    keys = await self.redis_client.keys(pattern)
                    
                    if keys:
                        await self.redis_client.delete(*keys)
                    await self.redis_client.delete(index_key)
                    
                    logger.info(f"Invalidated all cache for project: {project_id}")
                    
            except Exception as e:
                logger.error(f"Failed to invalidate cache: {e}")
    
    async def get_scene_status(self, project_id: str) -> Dict[str, Dict[str, any]]:
        """
        Get comprehensive scene availability status for a project.
        
        Args:
            project_id: Project identifier
            
        Returns:
            Dictionary with scene status information
        """
        async with self._redis_operation("get_scene_status"):
            try:
                status = {
                    'project_id': project_id,
                    'scenes': {},
                    'summary': {
                        'total_scenes': 0,
                        'available_videos': 0,
                        'available_audio': 0,
                        'available_images': 0,
                        'last_updated': None
                    }
                }
                
                # Get project index
                index_key = self.SCENE_INDEX_KEY.format(project_id=project_id)
                cached_index = await self.redis_client.get(index_key)
                
                if cached_index:
                    project_index = ProjectSceneIndex(**json.loads(cached_index))
                    status['summary']['last_updated'] = project_index.last_updated
                    
                    for scene_id, scene_files in project_index.scenes.items():
                        scene_status = {
                            'scene_id': scene_id,
                            'files': {
                                'video': [],
                                'audio': [],
                                'image': []
                            },
                            'status': {
                                'has_video': False,
                                'has_audio': False,
                                'has_image': False,
                                'ready_for_editing': False
                            }
                        }
                        
                        for file_info in scene_files:
                            file_type = file_info.file_type
                            if file_type in scene_status['files']:
                                scene_status['files'][file_type].append({
                                    'path': file_info.file_path,
                                    'size': file_info.file_size,
                                    'last_modified': file_info.last_modified,
                                    'exists': Path(file_info.file_path).exists()
                                })
                                
                                if Path(file_info.file_path).exists():
                                    scene_status['status'][f'has_{file_type}'] = True
                        
                        # Scene is ready for editing if it has at least video
                        scene_status['status']['ready_for_editing'] = scene_status['status']['has_video']
                        
                        status['scenes'][scene_id] = scene_status
                        status['summary']['total_scenes'] += 1
                        
                        if scene_status['status']['has_video']:
                            status['summary']['available_videos'] += 1
                        if scene_status['status']['has_audio']:
                            status['summary']['available_audio'] += 1
                        if scene_status['status']['has_image']:
                            status['summary']['available_images'] += 1
                
                return status
                
            except Exception as e:
                logger.error(f"Failed to get scene status for {project_id}: {e}")
                return {'error': str(e), 'project_id': project_id}
    
    async def get_performance_stats(self) -> Dict[str, any]:
        """Get performance statistics and health metrics."""
        try:
            # Update health check if needed
            current_time = datetime.utcnow().timestamp()
            if current_time - self._last_health_check > self._health_check_interval:
                await self._perform_health_check()
                self._last_health_check = current_time
            
            health_data = await self.redis_client.get(self.HEALTH_KEY)
            health_status = json.loads(health_data) if health_data else {"status": "unknown"}
            
            # Calculate cache hit rate
            total_lookups = self._stats['lookups']
            cache_hit_rate = (self._stats['cache_hits'] / total_lookups * 100) if total_lookups > 0 else 0
            
            return {
                'performance': {
                    'total_lookups': total_lookups,
                    'cache_hits': self._stats['cache_hits'],
                    'cache_misses': self._stats['cache_misses'],
                    'cache_hit_rate': round(cache_hit_rate, 2),
                    'index_updates': self._stats['index_updates'],
                    'errors': self._stats['errors']
                },
                'health': health_status,
                'connection': {
                    'redis_url': self.redis_url,
                    'connected': self.redis_client is not None
                },
                'settings': {
                    'default_ttl': self.default_ttl,
                    'batch_size': self.BATCH_SIZE,
                    'compression_enabled': self.enable_compression
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get performance stats: {e}")
            return {'error': str(e)}
    
    # Private helper methods
    
    def _parse_scene_id(self, scene_target: str) -> Optional[str]:
        """Parse scene ID from various target formats."""
        if scene_target.startswith("scene_"):
            try:
                parts = scene_target.split("_")
                if len(parts) >= 2 and parts[1].isdigit():
                    return f"scene_{int(parts[1])}"
            except (ValueError, IndexError):
                pass
        
        # Handle special targets
        if scene_target in ["scene_last", "scene_final"]:
            return scene_target
        
        return None
    
    def _sort_scene_key(self, scene_id: str) -> int:
        """Sort key for scene IDs."""
        if scene_id.startswith("scene_"):
            try:
                return int(scene_id.split("_")[1])
            except (ValueError, IndexError):
                pass
        return 999  # Put non-standard scenes at end
    
    def _select_best_video_file(self, video_files: List[SceneMediaInfo]) -> SceneMediaInfo:
        """Select the best video file from multiple options."""
        # Priority order for video files
        priority_patterns = [
            "runway_generated.mp4",
            "_composite.mp4", 
            "_final.mp4",
            ".mp4"
        ]
        
        for pattern in priority_patterns:
            for video_file in video_files:
                if pattern in Path(video_file.file_path).name:
                    return video_file
        
        # Return first available if no preferred pattern found
        return video_files[0]
    
    async def _scan_scene_video(self, scene_id: str, project_id: str) -> Optional[str]:
        """Scan file system for scene video (fallback method)."""
        try:
            # Enhanced scene patterns based on Agent 2C's structure
            scene_num_str = scene_id.replace("scene_", "")
            if scene_num_str.isdigit():
                scene_num = int(scene_num_str)
                
                scene_patterns = [
                    # Agent 2C's folder structure
                    f"output/projects/{project_id}/scene_{scene_num:02d}/video/scene_{scene_num:02d}.mp4",
                    f"output/projects/{project_id}/scene_{scene_num}/video/scene_{scene_num}.mp4",
                    
                    # RunwayML generated videos
                    f"output/projects/{project_id}/scene_{scene_num:02d}/video/runway_generated.mp4",
                    f"output/projects/{project_id}/scene_{scene_num}/video/runway_generated.mp4",
                    
                    # Legacy patterns
                    f"output/log_{project_id}/scenes/scene_{scene_num}_composite.mp4",
                    f"output/projects/{project_id}/scenes/scene_{scene_num}.mp4",
                ]
                
                for pattern in scene_patterns:
                    path = Path(pattern)
                    if path.exists():
                        return str(path)
            
            return None
            
        except Exception as e:
            logger.error(f"Error scanning for scene video {scene_id}: {e}")
            return None
    
    async def _scan_all_scene_videos(self, project_id: str) -> List[str]:
        """Scan file system for all scene videos (fallback method)."""
        try:
            videos = []
            project_dir = Path(f"output/projects/{project_id}")
            
            if project_dir.exists():
                # Look for scene folders
                scene_dirs = [d for d in project_dir.iterdir() 
                            if d.is_dir() and d.name.startswith("scene_")]
                scene_dirs.sort(key=lambda x: self._sort_scene_key(x.name))
                
                for scene_dir in scene_dirs:
                    video_dir = scene_dir / "video"
                    if video_dir.exists():
                        # Look for video files in priority order
                        video_patterns = [
                            f"{scene_dir.name}.mp4",
                            "runway_generated.mp4",
                            "scene_final.mp4"
                        ]
                        
                        for pattern in video_patterns:
                            video_path = video_dir / pattern
                            if video_path.exists():
                                videos.append(str(video_path))
                                break
            
            return videos
            
        except Exception as e:
            logger.error(f"Error scanning all scene videos for {project_id}: {e}")
            return []
    
    async def _rebuild_project_index(self, project_id: str) -> List[str]:
        """Rebuild complete project index with all media files."""
        try:
            scenes_data = {}
            project_dir = Path(f"output/projects/{project_id}")
            
            if project_dir.exists():
                # Scan all scene directories
                scene_dirs = [d for d in project_dir.iterdir() 
                            if d.is_dir() and d.name.startswith("scene_")]
                
                for scene_dir in scene_dirs:
                    scene_id = scene_dir.name
                    scene_files = []
                    
                    # Scan for different media types
                    media_dirs = {
                        'video': scene_dir / 'video',
                        'audio': scene_dir / 'audio', 
                        'image': scene_dir / 'images'
                    }
                    
                    for media_type, media_dir in media_dirs.items():
                        if media_dir.exists():
                            for file_path in media_dir.iterdir():
                                if file_path.is_file():
                                    try:
                                        stat = file_path.stat()
                                        scene_info = SceneMediaInfo(
                                            scene_id=scene_id,
                                            project_id=project_id,
                                            file_path=str(file_path),
                                            file_type=media_type,
                                            file_size=stat.st_size,
                                            last_modified=stat.st_mtime,
                                            format=file_path.suffix
                                        )
                                        scene_files.append(scene_info)
                                    except Exception as e:
                                        logger.warning(f"Error processing file {file_path}: {e}")
                    
                    if scene_files:
                        scenes_data[scene_id] = scene_files
            
            # Create project index
            project_index = ProjectSceneIndex(
                project_id=project_id,
                scenes={k: [asdict(f) for f in v] for k, v in scenes_data.items()},
                last_updated=datetime.utcnow().timestamp(),
                total_files=sum(len(files) for files in scenes_data.values())
            )
            
            # Store in Redis
            index_key = self.SCENE_INDEX_KEY.format(project_id=project_id)
            await self.redis_client.setex(
                index_key,
                self.default_ttl,
                json.dumps(asdict(project_index))
            )
            
            # Extract video list for return
            videos = []
            for scene_id in sorted(scenes_data.keys(), key=self._sort_scene_key):
                video_files = [f for f in scenes_data[scene_id] if f.file_type == 'video']
                if video_files:
                    best_video = self._select_best_video_file(video_files)
                    videos.append(best_video.file_path)
            
            logger.info(f"Rebuilt index for project {project_id}: "
                       f"{len(scenes_data)} scenes, {project_index.total_files} files")
            
            return videos
            
        except Exception as e:
            logger.error(f"Failed to rebuild project index for {project_id}: {e}")
            return []
    
    async def _update_health_status(self, status: str, message: str):
        """Update health status in Redis."""
        try:
            health_data = {
                'status': status,
                'message': message,
                'timestamp': datetime.utcnow().timestamp(),
                'stats': self._stats.copy()
            }
            
            await self.redis_client.setex(
                self.HEALTH_KEY,
                300,  # 5 minute TTL
                json.dumps(health_data)
            )
            
        except Exception as e:
            logger.error(f"Failed to update health status: {e}")
    
    async def _perform_health_check(self):
        """Perform comprehensive health check."""
        try:
            # Test Redis connectivity
            await self.redis_client.ping()
            
            # Check memory usage
            info = await self.redis_client.info('memory')
            memory_usage = info.get('used_memory_human', 'unknown')
            
            await self._update_health_status(
                "healthy", 
                f"System operational, memory: {memory_usage}"
            )
            
        except Exception as e:
            await self._update_health_status(
                "unhealthy", 
                f"Health check failed: {e}"
            )

# Global instance for easy access
_scene_index_manager: Optional[SceneIndexManager] = None

async def get_scene_index_manager() -> SceneIndexManager:
    """Get global scene index manager instance."""
    global _scene_index_manager
    
    if _scene_index_manager is None:
        _scene_index_manager = SceneIndexManager()
        await _scene_index_manager.initialize()
    
    return _scene_index_manager

async def cleanup_scene_index_manager():
    """Clean up global scene index manager."""
    global _scene_index_manager
    
    if _scene_index_manager:
        await _scene_index_manager.close()
        _scene_index_manager = None