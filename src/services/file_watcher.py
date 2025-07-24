"""
File Watcher Service - Real-time Scene Change Monitoring

Monitors scene directories for file changes and updates the scene index automatically.
Designed for sub-1 second update propagation with intelligent batching.

Performance Targets:
- Update propagation: < 1 second
- Memory usage: < 50MB for 100 projects
- CPU overhead: < 5% during normal operation
- Batch processing: 100 events/second
"""

import os
import asyncio
import logging
import json
from typing import Dict, List, Set, Optional, Callable, Any
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass
from collections import defaultdict, deque
from contextlib import asynccontextmanager

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileSystemEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    FileSystemEventHandler = None
    FileSystemEvent = None

from .scene_index_manager import SceneIndexManager, get_scene_index_manager

logger = logging.getLogger(__name__)

@dataclass
class FileChangeEvent:
    """File change event information."""
    event_type: str  # 'created', 'modified', 'deleted', 'moved'
    file_path: str
    project_id: str
    scene_id: Optional[str]
    file_type: Optional[str]  # 'video', 'audio', 'image'
    timestamp: float
    
    def __post_init__(self):
        if self.timestamp == 0:
            self.timestamp = datetime.utcnow().timestamp()

@dataclass
class WatcherStats:
    """File watcher statistics."""
    events_processed: int = 0
    batches_processed: int = 0
    index_updates: int = 0
    errors: int = 0
    last_activity: float = 0
    watched_directories: int = 0
    
    def __post_init__(self):
        if self.last_activity == 0:
            self.last_activity = datetime.utcnow().timestamp()

class SceneFileHandler(FileSystemEventHandler):
    """Watchdog event handler for scene file changes."""
    
    def __init__(self, file_watcher: 'FileWatcher'):
        super().__init__()
        self.file_watcher = file_watcher
        self.logger = logging.getLogger(f"{__name__}.SceneFileHandler")
    
    def on_created(self, event: FileSystemEvent):
        """Handle file creation events."""
        if not event.is_directory:
            asyncio.create_task(self.file_watcher._handle_file_event('created', event.src_path))
    
    def on_modified(self, event: FileSystemEvent):
        """Handle file modification events."""
        if not event.is_directory:
            asyncio.create_task(self.file_watcher._handle_file_event('modified', event.src_path))
    
    def on_deleted(self, event: FileSystemEvent):
        """Handle file deletion events."""
        if not event.is_directory:
            asyncio.create_task(self.file_watcher._handle_file_event('deleted', event.src_path))
    
    def on_moved(self, event: FileSystemEvent):
        """Handle file move events."""
        if not event.is_directory and hasattr(event, 'dest_path'):
            # Handle move as delete + create
            asyncio.create_task(self.file_watcher._handle_file_event('deleted', event.src_path))
            asyncio.create_task(self.file_watcher._handle_file_event('created', event.dest_path))

class FileWatcher:
    """
    Real-time file system watcher for scene directories.
    
    Features:
    - Intelligent event batching and debouncing
    - Automatic scene index updates
    - Project-specific directory monitoring
    - Performance monitoring and health checks
    - Graceful degradation when watchdog unavailable
    """
    
    # Performance settings
    BATCH_INTERVAL = 2.0      # Batch events every 2 seconds
    DEBOUNCE_INTERVAL = 0.5   # Debounce rapid file changes
    MAX_BATCH_SIZE = 100      # Maximum events per batch
    WATCH_PATTERNS = {         # File patterns to watch
        'video': {'.mp4', '.avi', '.mov', '.mkv'},
        'audio': {'.mp3', '.wav', '.aac', '.m4a'},
        'image': {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
    }
    
    def __init__(self, 
                 scene_index_manager: Optional[SceneIndexManager] = None,
                 watch_root: str = "./output/projects",
                 enable_auto_discovery: bool = True):
        """
        Initialize File Watcher.
        
        Args:
            scene_index_manager: Scene index manager instance
            watch_root: Root directory to watch for projects
            enable_auto_discovery: Automatically discover and watch new projects
        """
        self.scene_index_manager = scene_index_manager
        self.watch_root = Path(watch_root)
        self.enable_auto_discovery = enable_auto_discovery
        
        # Watchdog components
        self.observer: Optional[Observer] = None
        self.event_handler: Optional[SceneFileHandler] = None
        self.watched_paths: Dict[str, Any] = {}  # path -> watch handle
        
        # Event processing
        self._event_queue: deque = deque()
        self._event_batch: List[FileChangeEvent] = []
        self._last_batch_time = 0
        self._processing_task: Optional[asyncio.Task] = None
        self._is_running = False
        
        # Debouncing
        self._pending_events: Dict[str, FileChangeEvent] = {}  # file_path -> latest event
        self._debounce_timers: Dict[str, asyncio.Handle] = {}
        
        # Statistics and monitoring
        self.stats = WatcherStats()
        self._health_check_interval = 60  # seconds
        self._last_health_check = 0
        
        # Callbacks for external integration
        self._change_callbacks: List[Callable[[FileChangeEvent], None]] = []
        
        logger.info(f"Initialized FileWatcher for: {self.watch_root}")
        
        if not WATCHDOG_AVAILABLE:
            logger.warning("Watchdog not available, file watching disabled")
    
    async def start(self) -> bool:
        """Start the file watcher."""
        try:
            if not WATCHDOG_AVAILABLE:
                logger.warning("Cannot start file watcher: watchdog not available")
                return False
            
            # Initialize scene index manager if not provided
            if self.scene_index_manager is None:
                self.scene_index_manager = await get_scene_index_manager()
            
            # Start watchdog observer
            self.observer = Observer()
            self.event_handler = SceneFileHandler(self)
            
            # Start event processing
            self._is_running = True
            self._processing_task = asyncio.create_task(self._process_events())
            
            # Discover and watch existing projects
            if self.enable_auto_discovery:
                await self._discover_projects()
            
            # Start observer
            self.observer.start()
            
            logger.info("File watcher started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start file watcher: {e}")
            return False
    
    async def stop(self):
        """Stop the file watcher."""
        try:
            self._is_running = False
            
            # Cancel debounce timers
            for timer in self._debounce_timers.values():
                timer.cancel()
            self._debounce_timers.clear()
            
            # Stop processing task
            if self._processing_task:
                self._processing_task.cancel()
                try:
                    await self._processing_task
                except asyncio.CancelledError:
                    pass
            
            # Stop watchdog observer
            if self.observer:
                self.observer.stop()
                self.observer.join(timeout=5)
            
            logger.info("File watcher stopped")
            
        except Exception as e:
            logger.error(f"Error stopping file watcher: {e}")
    
    async def watch_project(self, project_id: str) -> bool:
        """
        Start watching a specific project directory.
        
        Args:
            project_id: Project identifier
            
        Returns:
            True if watching started successfully
        """
        try:
            if not WATCHDOG_AVAILABLE or not self.observer:
                return False
            
            project_path = self.watch_root / project_id
            if not project_path.exists():
                logger.warning(f"Project directory does not exist: {project_path}")
                return False
            
            # Don't watch if already watching
            if str(project_path) in self.watched_paths:
                logger.debug(f"Already watching project: {project_id}")
                return True
            
            # Add watch for project directory
            watch_handle = self.observer.schedule(
                self.event_handler,
                str(project_path),
                recursive=True
            )
            
            self.watched_paths[str(project_path)] = watch_handle
            self.stats.watched_directories += 1
            
            logger.info(f"Started watching project: {project_id} at {project_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to watch project {project_id}: {e}")
            return False
    
    async def unwatch_project(self, project_id: str) -> bool:
        """
        Stop watching a specific project directory.
        
        Args:
            project_id: Project identifier
            
        Returns:
            True if unwatching successful
        """
        try:
            project_path = str(self.watch_root / project_id)
            
            if project_path in self.watched_paths:
                watch_handle = self.watched_paths[project_path]
                if self.observer:
                    self.observer.unschedule(watch_handle)
                
                del self.watched_paths[project_path]
                self.stats.watched_directories -= 1
                
                logger.info(f"Stopped watching project: {project_id}")
                return True
            else:
                logger.debug(f"Project not being watched: {project_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to unwatch project {project_id}: {e}")
            return False
    
    def add_change_callback(self, callback: Callable[[FileChangeEvent], None]):
        """Add callback for file change notifications."""
        self._change_callbacks.append(callback)
        logger.debug(f"Added change callback: {callback.__name__}")
    
    def remove_change_callback(self, callback: Callable[[FileChangeEvent], None]):
        """Remove file change callback."""
        if callback in self._change_callbacks:
            self._change_callbacks.remove(callback)
            logger.debug(f"Removed change callback: {callback.__name__}")
    
    async def get_status(self) -> Dict[str, Any]:
        """Get file watcher status and statistics."""
        current_time = datetime.utcnow().timestamp()
        
        # Perform health check if needed
        if current_time - self._last_health_check > self._health_check_interval:
            await self._perform_health_check()
            self._last_health_check = current_time
        
        return {
            'status': {
                'running': self._is_running,
                'watchdog_available': WATCHDOG_AVAILABLE,
                'observer_running': self.observer.is_alive() if self.observer else False
            },
            'statistics': {
                'events_processed': self.stats.events_processed,
                'batches_processed': self.stats.batches_processed,
                'index_updates': self.stats.index_updates,
                'errors': self.stats.errors,
                'watched_directories': self.stats.watched_directories,
                'last_activity': self.stats.last_activity
            },
            'configuration': {
                'watch_root': str(self.watch_root),
                'batch_interval': self.BATCH_INTERVAL,
                'debounce_interval': self.DEBOUNCE_INTERVAL,
                'max_batch_size': self.MAX_BATCH_SIZE,
                'auto_discovery': self.enable_auto_discovery
            },
            'watched_projects': list(self.watched_paths.keys())
        }
    
    # Private methods
    
    async def _handle_file_event(self, event_type: str, file_path: str):
        """Handle individual file system events."""
        try:
            path_obj = Path(file_path)
            
            # Check if this is a scene-related file
            if not self._is_scene_file(path_obj):
                return
            
            # Parse project and scene information
            project_id, scene_id = self._extract_project_scene_info(path_obj)
            if not project_id:
                return
            
            # Determine file type
            file_type = self._get_file_type(path_obj)
            
            # Create event
            event = FileChangeEvent(
                event_type=event_type,
                file_path=file_path,
                project_id=project_id,
                scene_id=scene_id,
                file_type=file_type,
                timestamp=datetime.utcnow().timestamp()
            )
            
            # Add to debouncing system
            await self._debounce_event(event)
            
        except Exception as e:
            logger.error(f"Error handling file event {event_type} for {file_path}: {e}")
            self.stats.errors += 1
    
    async def _debounce_event(self, event: FileChangeEvent):
        """Debounce rapid file changes for the same file."""
        file_path = event.file_path
        
        # Cancel existing timer for this file
        if file_path in self._debounce_timers:
            self._debounce_timers[file_path].cancel()
        
        # Store latest event
        self._pending_events[file_path] = event
        
        # Set new timer
        loop = asyncio.get_event_loop()
        timer = loop.call_later(
            self.DEBOUNCE_INTERVAL,
            lambda: asyncio.create_task(self._flush_debounced_event(file_path))
        )
        self._debounce_timers[file_path] = timer
    
    async def _flush_debounced_event(self, file_path: str):
        """Flush a debounced event to the processing queue."""
        try:
            if file_path in self._pending_events:
                event = self._pending_events.pop(file_path)
                self._event_queue.append(event)
                
                # Cleanup timer
                if file_path in self._debounce_timers:
                    del self._debounce_timers[file_path]
                
                self.stats.last_activity = datetime.utcnow().timestamp()
                
        except Exception as e:
            logger.error(f"Error flushing debounced event for {file_path}: {e}")
            self.stats.errors += 1
    
    async def _process_events(self):
        """Main event processing loop."""
        logger.info("Started file watcher event processing")
        
        while self._is_running:
            try:
                await asyncio.sleep(0.1)  # Small delay to prevent busy loop
                
                current_time = datetime.utcnow().timestamp()
                
                # Process events in batches
                if (self._event_queue and 
                    (current_time - self._last_batch_time >= self.BATCH_INTERVAL or
                     len(self._event_batch) >= self.MAX_BATCH_SIZE)):
                    
                    # Move events from queue to batch
                    while self._event_queue and len(self._event_batch) < self.MAX_BATCH_SIZE:
                        self._event_batch.append(self._event_queue.popleft())
                    
                    if self._event_batch:
                        await self._process_event_batch()
                        self._last_batch_time = current_time
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in event processing loop: {e}")
                self.stats.errors += 1
                await asyncio.sleep(1)  # Back off on errors
        
        logger.info("Stopped file watcher event processing")
    
    async def _process_event_batch(self):
        """Process a batch of file change events."""
        if not self._event_batch:
            return
        
        try:
            batch = self._event_batch.copy()
            self._event_batch.clear()
            
            logger.debug(f"Processing batch of {len(batch)} file events")
            
            # Group events by project for efficient index updates
            project_events = defaultdict(list)
            for event in batch:
                project_events[event.project_id].append(event)
                self.stats.events_processed += 1
            
            # Update scene index for affected projects
            for project_id, events in project_events.items():
                try:
                    # Notify callbacks first
                    for event in events:
                        for callback in self._change_callbacks:
                            try:
                                callback(event)
                            except Exception as e:
                                logger.error(f"Error in change callback: {e}")
                    
                    # Update scene index
                    if self.scene_index_manager:
                        await self.scene_index_manager.update_scene_index(project_id)
                        self.stats.index_updates += 1
                        
                        # Invalidate specific scene caches if possible
                        scene_ids = {event.scene_id for event in events if event.scene_id}
                        for scene_id in scene_ids:
                            await self.scene_index_manager.invalidate_scene_cache(project_id, scene_id)
                    
                    logger.debug(f"Updated scene index for project {project_id} "
                               f"with {len(events)} events")
                    
                except Exception as e:
                    logger.error(f"Error updating scene index for project {project_id}: {e}")
                    self.stats.errors += 1
            
            self.stats.batches_processed += 1
            logger.debug(f"Completed batch processing for {len(project_events)} projects")
            
        except Exception as e:
            logger.error(f"Error processing event batch: {e}")
            self.stats.errors += 1
    
    async def _discover_projects(self):
        """Discover existing projects and start watching them."""
        try:
            if not self.watch_root.exists():
                logger.warning(f"Watch root directory does not exist: {self.watch_root}")
                return
            
            project_count = 0
            for project_dir in self.watch_root.iterdir():
                if project_dir.is_dir():
                    project_id = project_dir.name
                    if await self.watch_project(project_id):
                        project_count += 1
            
            logger.info(f"Auto-discovered and watching {project_count} projects")
            
        except Exception as e:
            logger.error(f"Error discovering projects: {e}")
            self.stats.errors += 1
    
    def _is_scene_file(self, path: Path) -> bool:
        """Check if a file is scene-related and should be monitored."""
        # Check file extension
        if path.suffix.lower() not in {ext for exts in self.WATCH_PATTERNS.values() for ext in exts}:
            return False
        
        # Check if path contains scene directory structure
        path_parts = path.parts
        for part in path_parts:
            if part.startswith('scene_'):
                return True
        
        return False
    
    def _extract_project_scene_info(self, path: Path) -> Tuple[Optional[str], Optional[str]]:
        """Extract project ID and scene ID from file path."""
        try:
            path_parts = path.parts
            
            # Find project ID (should be under output/projects/)
            project_id = None
            scene_id = None
            
            for i, part in enumerate(path_parts):
                if part == 'projects' and i + 1 < len(path_parts):
                    project_id = path_parts[i + 1]
                elif part.startswith('scene_'):
                    scene_id = part
                    break
            
            return project_id, scene_id
            
        except Exception as e:
            logger.error(f"Error extracting project/scene info from {path}: {e}")
            return None, None
    
    def _get_file_type(self, path: Path) -> Optional[str]:
        """Determine file type based on extension."""
        ext = path.suffix.lower()
        
        for file_type, extensions in self.WATCH_PATTERNS.items():
            if ext in extensions:
                return file_type
        
        return None
    
    async def _perform_health_check(self):
        """Perform health check on file watcher system."""
        try:
            health_issues = []
            
            # Check watchdog availability
            if not WATCHDOG_AVAILABLE:
                health_issues.append("Watchdog library not available")
            
            # Check observer status
            if self.observer and not self.observer.is_alive():
                health_issues.append("Watchdog observer not running")
            
            # Check watch root
            if not self.watch_root.exists():
                health_issues.append(f"Watch root directory missing: {self.watch_root}")
            
            # Check recent activity
            current_time = datetime.utcnow().timestamp()
            if current_time - self.stats.last_activity > 3600:  # 1 hour
                logger.info("No file system activity in the last hour (normal during idle periods)")
            
            if health_issues:
                logger.warning(f"File watcher health issues: {'; '.join(health_issues)}")
            else:
                logger.debug("File watcher health check passed")
                
        except Exception as e:
            logger.error(f"Error in file watcher health check: {e}")

# Global instance for easy access
_file_watcher: Optional[FileWatcher] = None

async def get_file_watcher() -> FileWatcher:
    """Get global file watcher instance."""
    global _file_watcher
    
    if _file_watcher is None:
        _file_watcher = FileWatcher()
        await _file_watcher.start()
    
    return _file_watcher

async def cleanup_file_watcher():
    """Clean up global file watcher."""
    global _file_watcher
    
    if _file_watcher:
        await _file_watcher.stop()
        _file_watcher = None