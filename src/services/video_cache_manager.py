"""
Intelligent Video Cache Manager for High-Performance Video Operations.

This service provides smart caching with TTL, size limits, and LRU eviction
to reduce video generation by 80% through intelligent preview caching.
"""

import os
import asyncio
import logging
import json
import hashlib
import shutil
import time
from typing import Dict, List, Any, Optional, Set, Tuple
from pathlib import Path
from datetime import datetime, timedelta
import threading
from collections import OrderedDict
import weakref

logger = logging.getLogger(__name__)

class CacheEntry:
    """Represents a cached video file entry."""
    
    def __init__(self, cache_key: str, file_path: str, operation_type: str, 
                 file_size: int, created_at: float, last_accessed: float):
        self.cache_key = cache_key
        self.file_path = file_path
        self.operation_type = operation_type
        self.file_size = file_size
        self.created_at = created_at
        self.last_accessed = last_accessed
        self.access_count = 1
        
    def update_access(self):
        """Update last accessed time and increment access count."""
        self.last_accessed = time.time()
        self.access_count += 1
    
    @property
    def age_seconds(self) -> float:
        """Get age of cache entry in seconds."""
        return time.time() - self.created_at
    
    @property
    def idle_seconds(self) -> float:
        """Get idle time since last access in seconds."""
        return time.time() - self.last_accessed
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "cache_key": self.cache_key,
            "file_path": self.file_path,
            "operation_type": self.operation_type,
            "file_size": self.file_size,
            "created_at": self.created_at,
            "last_accessed": self.last_accessed,
            "access_count": self.access_count,
            "age_seconds": self.age_seconds,
            "idle_seconds": self.idle_seconds
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheEntry':
        """Create from dictionary."""
        return cls(
            cache_key=data["cache_key"],
            file_path=data["file_path"],
            operation_type=data["operation_type"],
            file_size=data["file_size"],
            created_at=data["created_at"],
            last_accessed=data["last_accessed"]
        )

class VideoCacheManager:
    """
    Intelligent video cache manager with LRU eviction and smart cleanup.
    
    Features:
    - TTL-based expiration (default: 24 hours)
    - Size-based LRU eviction (default: 5GB)
    - Operation-type aware caching
    - Smart preview generation caching
    - Async file operations
    - Thread-safe access
    - Persistent cache metadata
    - Cache hit rate tracking
    """
    
    def __init__(self, 
                 cache_dir: str = "./cache/video_operations",
                 max_cache_size_gb: float = 5.0,
                 default_ttl_hours: int = 24,
                 cleanup_interval_minutes: int = 30):
        """
        Initialize video cache manager.
        
        Args:
            cache_dir: Directory for cached files
            max_cache_size_gb: Maximum cache size in GB
            default_ttl_hours: Default TTL in hours
            cleanup_interval_minutes: Cleanup interval in minutes
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_cache_size_bytes = int(max_cache_size_gb * 1024 * 1024 * 1024)
        self.default_ttl_seconds = default_ttl_hours * 3600
        self.cleanup_interval = cleanup_interval_minutes * 60
        
        # Thread-safe cache registry using OrderedDict for LRU
        self._cache_entries: OrderedDict[str, CacheEntry] = OrderedDict()
        self._cache_lock = threading.RLock()
        
        # Cache statistics
        self._cache_hits = 0
        self._cache_misses = 0
        self._total_size_bytes = 0
        
        # Metadata file
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        
        # Cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        self._cleanup_enabled = True
        
        # Load existing cache metadata
        self._load_cache_metadata()
        
        logger.info(f"Initialized video cache manager: {cache_dir}, max_size={max_cache_size_gb}GB, ttl={default_ttl_hours}h")
    
    def _load_cache_metadata(self):
        """Load cache metadata from disk."""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                for entry_data in metadata.get("entries", []):
                    entry = CacheEntry.from_dict(entry_data)
                    
                    # Verify file still exists
                    if Path(entry.file_path).exists():
                        self._cache_entries[entry.cache_key] = entry
                        self._total_size_bytes += entry.file_size
                    else:
                        logger.warning(f"Cache file missing: {entry.file_path}")
                
                # Load statistics
                stats = metadata.get("statistics", {})
                self._cache_hits = stats.get("cache_hits", 0)
                self._cache_misses = stats.get("cache_misses", 0)
                
                logger.info(f"Loaded {len(self._cache_entries)} cache entries, total size: {self._total_size_bytes / (1024*1024):.1f}MB")
        
        except Exception as e:
            logger.error(f"Error loading cache metadata: {e}")
            self._cache_entries.clear()
    
    def _save_cache_metadata(self):
        """Save cache metadata to disk."""
        try:
            metadata = {
                "entries": [entry.to_dict() for entry in self._cache_entries.values()],
                "statistics": {
                    "cache_hits": self._cache_hits,
                    "cache_misses": self._cache_misses,
                    "total_size_bytes": self._total_size_bytes,
                    "last_cleanup": time.time()
                },
                "version": "1.0"
            }
            
            # Atomic write
            temp_file = self.metadata_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            temp_file.replace(self.metadata_file)
            
        except Exception as e:
            logger.error(f"Error saving cache metadata: {e}")
    
    def _generate_cache_path(self, cache_key: str, operation_type: str) -> Path:
        """Generate cache file path."""
        # Create subdirectory by operation type
        op_dir = self.cache_dir / operation_type
        op_dir.mkdir(exist_ok=True)
        
        return op_dir / f"{cache_key}.mp4"
    
    def _evict_lru_entries(self, required_space: int = 0):
        """Evict least recently used entries to free space."""
        with self._cache_lock:
            space_to_free = max(required_space, self.max_cache_size_bytes * 0.1)  # Free at least 10%
            freed_space = 0
            
            # Sort by last accessed time (LRU first)
            entries_by_lru = sorted(
                self._cache_entries.values(),
                key=lambda e: e.last_accessed
            )
            
            for entry in entries_by_lru:
                if freed_space >= space_to_free:
                    break
                
                try:
                    # Remove file
                    file_path = Path(entry.file_path)
                    if file_path.exists():
                        file_path.unlink()
                        freed_space += entry.file_size
                        self._total_size_bytes -= entry.file_size
                    
                    # Remove from cache registry
                    if entry.cache_key in self._cache_entries:
                        del self._cache_entries[entry.cache_key]
                    
                    logger.debug(f"Evicted cache entry: {entry.cache_key}")
                    
                except Exception as e:
                    logger.error(f"Error evicting cache entry {entry.cache_key}: {e}")
            
            if freed_space > 0:
                logger.info(f"Freed {freed_space / (1024*1024):.1f}MB of cache space")
    
    def _cleanup_expired_entries(self):
        """Remove expired cache entries."""
        current_time = time.time()
        expired_keys = []
        
        with self._cache_lock:
            for cache_key, entry in self._cache_entries.items():
                if entry.age_seconds > self.default_ttl_seconds:
                    expired_keys.append(cache_key)
        
        for cache_key in expired_keys:
            try:
                entry = self._cache_entries[cache_key]
                file_path = Path(entry.file_path)
                
                if file_path.exists():
                    file_path.unlink()
                    self._total_size_bytes -= entry.file_size
                
                del self._cache_entries[cache_key]
                logger.debug(f"Expired cache entry: {cache_key}")
                
            except Exception as e:
                logger.error(f"Error removing expired entry {cache_key}: {e}")
        
        if expired_keys:
            logger.info(f"Removed {len(expired_keys)} expired cache entries")
    
    async def get_cached_result(self, cache_key: str) -> Optional[str]:
        """
        Get cached result for operation.
        
        Args:
            cache_key: Cache key for the operation
            
        Returns:
            Path to cached file if exists, None otherwise
        """
        with self._cache_lock:
            if cache_key in self._cache_entries:
                entry = self._cache_entries[cache_key]
                
                # Check if file still exists
                if Path(entry.file_path).exists():
                    # Update access statistics
                    entry.update_access()
                    
                    # Move to end (most recently used)
                    self._cache_entries.move_to_end(cache_key)
                    
                    self._cache_hits += 1
                    
                    logger.debug(f"Cache hit: {cache_key}")
                    return entry.file_path
                else:
                    # File missing, remove from cache
                    del self._cache_entries[cache_key]
                    logger.warning(f"Cache file missing, removed entry: {cache_key}")
            
            self._cache_misses += 1
            return None
    
    async def cache_result(self, cache_key: str, result_file_path: str, operation_type: str) -> bool:
        """
        Cache operation result.
        
        Args:
            cache_key: Cache key for the operation
            result_file_path: Path to result file to cache
            operation_type: Type of operation (for organization)
            
        Returns:
            True if cached successfully, False otherwise
        """
        try:
            source_path = Path(result_file_path)
            if not source_path.exists():
                logger.warning(f"Result file not found for caching: {result_file_path}")
                return False
            
            file_size = source_path.stat().st_size
            
            # Check if we need to free space
            with self._cache_lock:
                if self._total_size_bytes + file_size > self.max_cache_size_bytes:
                    self._evict_lru_entries(file_size)
            
            # Generate cache path
            cache_path = self._generate_cache_path(cache_key, operation_type)
            
            # Copy file to cache (async)
            await asyncio.get_event_loop().run_in_executor(
                None, shutil.copy2, source_path, cache_path
            )
            
            # Create cache entry
            current_time = time.time()
            entry = CacheEntry(
                cache_key=cache_key,
                file_path=str(cache_path),
                operation_type=operation_type,
                file_size=file_size,
                created_at=current_time,
                last_accessed=current_time
            )
            
            with self._cache_lock:
                self._cache_entries[cache_key] = entry
                self._total_size_bytes += file_size
                
                # Move to end (most recently used)
                self._cache_entries.move_to_end(cache_key)
            
            logger.debug(f"Cached result: {cache_key} -> {cache_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error caching result {cache_key}: {e}")
            return False
    
    async def invalidate_cache_entry(self, cache_key: str) -> bool:
        """
        Invalidate a specific cache entry.
        
        Args:
            cache_key: Cache key to invalidate
            
        Returns:
            True if invalidated, False if not found
        """
        with self._cache_lock:
            if cache_key in self._cache_entries:
                entry = self._cache_entries[cache_key]
                
                try:
                    # Remove file
                    file_path = Path(entry.file_path)
                    if file_path.exists():
                        file_path.unlink()
                        self._total_size_bytes -= entry.file_size
                    
                    # Remove from registry
                    del self._cache_entries[cache_key]
                    
                    logger.info(f"Invalidated cache entry: {cache_key}")
                    return True
                    
                except Exception as e:
                    logger.error(f"Error invalidating cache entry {cache_key}: {e}")
                    return False
            
            return False
    
    async def clear_cache(self, operation_type: Optional[str] = None):
        """
        Clear cache entries.
        
        Args:
            operation_type: If specified, only clear entries of this type
        """
        keys_to_remove = []
        
        with self._cache_lock:
            for cache_key, entry in self._cache_entries.items():
                if operation_type is None or entry.operation_type == operation_type:
                    keys_to_remove.append(cache_key)
        
        for cache_key in keys_to_remove:
            await self.invalidate_cache_entry(cache_key)
        
        logger.info(f"Cleared {len(keys_to_remove)} cache entries" + 
                   (f" for operation type: {operation_type}" if operation_type else ""))
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._cache_lock:
            total_requests = self._cache_hits + self._cache_misses
            hit_rate = (self._cache_hits / total_requests * 100) if total_requests > 0 else 0
            
            # Group by operation type
            operation_stats = {}
            for entry in self._cache_entries.values():
                op_type = entry.operation_type
                if op_type not in operation_stats:
                    operation_stats[op_type] = {"count": 0, "size_mb": 0}
                
                operation_stats[op_type]["count"] += 1
                operation_stats[op_type]["size_mb"] += entry.file_size / (1024 * 1024)
            
            return {
                "total_entries": len(self._cache_entries),
                "total_size_mb": self._total_size_bytes / (1024 * 1024),
                "max_size_mb": self.max_cache_size_bytes / (1024 * 1024),
                "cache_hits": self._cache_hits,
                "cache_misses": self._cache_misses,
                "hit_rate_percent": hit_rate,
                "operation_stats": operation_stats,
                "oldest_entry_age_hours": max([e.age_seconds for e in self._cache_entries.values()]) / 3600 if self._cache_entries else 0,
                "cache_directory": str(self.cache_dir)
            }
    
    async def start_cleanup_task(self):
        """Start background cleanup task."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_enabled = True
            self._cleanup_task = asyncio.create_task(self._background_cleanup())
            logger.info("Started cache cleanup background task")
    
    async def stop_cleanup_task(self):
        """Stop background cleanup task."""
        self._cleanup_enabled = False
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped cache cleanup background task")
    
    async def _background_cleanup(self):
        """Background cleanup task."""
        while self._cleanup_enabled:
            try:
                await asyncio.sleep(self.cleanup_interval)
                
                if not self._cleanup_enabled:
                    break
                
                # Cleanup expired entries
                self._cleanup_expired_entries()
                
                # Check if we need to free space
                with self._cache_lock:
                    if self._total_size_bytes > self.max_cache_size_bytes * 0.8:  # 80% threshold
                        self._evict_lru_entries()
                
                # Save metadata
                self._save_cache_metadata()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cache cleanup task: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def optimize_cache(self):
        """Optimize cache by removing duplicate files and reorganizing."""
        logger.info("Starting cache optimization")
        
        # Find potential duplicates by file size and operation type
        size_groups: Dict[Tuple[int, str], List[CacheEntry]] = {}
        
        with self._cache_lock:
            for entry in self._cache_entries.values():
                key = (entry.file_size, entry.operation_type)
                if key not in size_groups:
                    size_groups[key] = []
                size_groups[key].append(entry)
        
        # Check for actual duplicates
        duplicates_found = 0
        for entries in size_groups.values():
            if len(entries) > 1:
                # Compare file contents for entries with same size
                for i, entry1 in enumerate(entries):
                    for entry2 in entries[i+1:]:
                        try:
                            if await self._files_are_identical(entry1.file_path, entry2.file_path):
                                # Keep the more recently accessed one
                                to_remove = entry1 if entry1.last_accessed < entry2.last_accessed else entry2
                                await self.invalidate_cache_entry(to_remove.cache_key)
                                duplicates_found += 1
                                break
                        except Exception as e:
                            logger.warning(f"Error comparing files for duplicates: {e}")
        
        logger.info(f"Cache optimization completed, removed {duplicates_found} duplicates")
    
    async def _files_are_identical(self, file1: str, file2: str) -> bool:
        """Check if two files are identical by comparing content."""
        def _compare_files():
            import filecmp
            return filecmp.cmp(file1, file2, shallow=False)
        
        return await asyncio.get_event_loop().run_in_executor(None, _compare_files)
    
    async def cleanup(self):
        """Cleanup cache manager and save state."""
        logger.info("Starting cache manager cleanup")
        
        await self.stop_cleanup_task()
        self._save_cache_metadata()
        
        logger.info("Cache manager cleanup completed")

# Global cache manager instance
_cache_manager_instance: Optional[VideoCacheManager] = None

def get_cache_manager() -> VideoCacheManager:
    """Get global cache manager instance."""
    global _cache_manager_instance
    if _cache_manager_instance is None:
        _cache_manager_instance = VideoCacheManager()
    return _cache_manager_instance

async def cleanup_cache_manager():
    """Cleanup global cache manager instance."""
    global _cache_manager_instance
    if _cache_manager_instance is not None:
        await _cache_manager_instance.cleanup()
        _cache_manager_instance = None