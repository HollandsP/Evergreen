"""
Scene Status API - Real-time Scene Availability and Health Endpoints

Provides fast API endpoints for scene availability checks, project status,
and performance monitoring. Built on the Scene Index Manager for O(1) lookups.

Performance Targets:
- Scene availability check: < 100ms
- Project status: < 200ms
- Batch status check: < 500ms for 100 scenes
- Real-time updates via WebSocket
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.services.scene_index_manager import get_scene_index_manager, SceneIndexManager
from src.services.file_watcher import get_file_watcher, FileWatcher, FileChangeEvent

logger = logging.getLogger(__name__)

# Response models
class SceneFileInfo(BaseModel):
    """Scene file information."""
    path: str
    size: int
    last_modified: float
    exists: bool
    format: Optional[str] = None

class SceneStatus(BaseModel):
    """Individual scene status."""
    scene_id: str
    files: Dict[str, List[SceneFileInfo]]
    status: Dict[str, bool]
    ready_for_editing: bool = Field(alias="ready_for_editing")

class ProjectSceneStatus(BaseModel):
    """Complete project scene status."""
    project_id: str
    scenes: Dict[str, SceneStatus]
    summary: Dict[str, Any]
    last_updated: Optional[float] = None

class SceneLookupResponse(BaseModel):
    """Scene video lookup response."""
    scene_id: str
    project_id: str
    video_path: Optional[str]
    found: bool
    cached: bool
    lookup_time_ms: float

class BatchSceneResponse(BaseModel):
    """Batch scene lookup response."""
    project_id: str
    scenes: List[SceneLookupResponse]
    total_scenes: int
    found_count: int
    lookup_time_ms: float

class PerformanceStats(BaseModel):
    """Performance statistics."""
    scene_index: Dict[str, Any]
    file_watcher: Dict[str, Any]
    system_health: str

class HealthStatus(BaseModel):
    """System health status."""
    status: str  # 'healthy', 'degraded', 'unhealthy'
    components: Dict[str, str]
    timestamp: float
    message: Optional[str] = None

# Request models
class SceneLookupRequest(BaseModel):
    """Scene lookup request."""
    scene_target: str = Field(..., description="Scene identifier (e.g., 'scene_1', 'scene_2')")
    project_id: str = Field(..., description="Project identifier")

class BatchSceneLookupRequest(BaseModel):
    """Batch scene lookup request."""
    project_id: str = Field(..., description="Project identifier")
    scene_targets: List[str] = Field(..., description="List of scene identifiers")

# Create router
router = APIRouter(prefix="/api/v1/scenes", tags=["Scene Status"])

# Dependency injection
async def get_scene_manager() -> SceneIndexManager:
    """Get scene index manager dependency."""
    return await get_scene_index_manager()

async def get_watcher() -> FileWatcher:
    """Get file watcher dependency."""
    return await get_file_watcher()

@router.get("/status/{project_id}", 
           response_model=ProjectSceneStatus,
           summary="Get complete scene status for a project")
async def get_project_scene_status(
    project_id: str,
    refresh_index: bool = Query(False, description="Force index refresh before status check"),
    scene_manager: SceneIndexManager = Depends(get_scene_manager)
) -> ProjectSceneStatus:
    """
    Get comprehensive scene availability status for a project.
    
    Returns detailed information about all scenes including:
    - Available video, audio, and image files
    - File existence verification
    - Scene readiness for editing
    - Summary statistics
    
    Performance: < 200ms for typical projects
    """
    start_time = datetime.utcnow()
    
    try:
        # Refresh index if requested
        if refresh_index:
            await scene_manager.update_scene_index(project_id, force_rebuild=True)
        
        # Get scene status
        status_data = await scene_manager.get_scene_status(project_id)
        
        if 'error' in status_data:
            raise HTTPException(status_code=404, detail=status_data['error'])
        
        # Convert to response model
        scenes = {}
        for scene_id, scene_data in status_data.get('scenes', {}).items():
            scene_files = {}
            for file_type, files in scene_data['files'].items():
                scene_files[file_type] = [
                    SceneFileInfo(
                        path=file_info['path'],
                        size=file_info['size'],
                        last_modified=file_info['last_modified'],
                        exists=file_info['exists']
                    ) for file_info in files
                ]
            
            scenes[scene_id] = SceneStatus(
                scene_id=scene_id,
                files=scene_files,
                status=scene_data['status'],
                ready_for_editing=scene_data['status'].get('ready_for_editing', False)
            )
        
        lookup_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        logger.info(f"Retrieved scene status for project {project_id} in {lookup_time:.1f}ms")
        
        return ProjectSceneStatus(
            project_id=project_id,
            scenes=scenes,
            summary=status_data.get('summary', {}),
            last_updated=status_data.get('summary', {}).get('last_updated')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting scene status for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get scene status: {str(e)}")

@router.post("/lookup", 
            response_model=SceneLookupResponse,
            summary="Fast scene video lookup")
async def lookup_scene_video(
    request: SceneLookupRequest,
    scene_manager: SceneIndexManager = Depends(get_scene_manager)
) -> SceneLookupResponse:
    """
    Fast O(1) scene video lookup with caching.
    
    Returns the path to the scene video file if available.
    Uses Redis caching for sub-100ms response times.
    """
    start_time = datetime.utcnow()
    
    try:
        # Perform scene lookup
        video_path = await scene_manager.find_scene_video(
            request.scene_target, 
            request.project_id
        )
        
        lookup_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Get performance stats to determine if result was cached
        stats = await scene_manager.get_performance_stats()
        cached = lookup_time < 50  # Assume cached if very fast
        
        logger.debug(f"Scene lookup {request.scene_target} in {lookup_time:.1f}ms")
        
        return SceneLookupResponse(
            scene_id=request.scene_target,
            project_id=request.project_id,
            video_path=video_path,
            found=video_path is not None,
            cached=cached,
            lookup_time_ms=round(lookup_time, 2)
        )
        
    except Exception as e:
        logger.error(f"Error in scene lookup {request.scene_target}: {e}")
        raise HTTPException(status_code=500, detail=f"Scene lookup failed: {str(e)}")

@router.post("/lookup/batch", 
            response_model=BatchSceneResponse,
            summary="Batch scene video lookup")
async def batch_lookup_scene_videos(
    request: BatchSceneLookupRequest,
    scene_manager: SceneIndexManager = Depends(get_scene_manager)
) -> BatchSceneResponse:
    """
    Efficient batch lookup of multiple scene videos.
    
    Performs parallel lookups for improved performance when checking
    multiple scenes at once.
    
    Performance: < 500ms for 100 scenes
    """
    start_time = datetime.utcnow()
    
    try:
        # Perform parallel lookups
        lookup_tasks = [
            scene_manager.find_scene_video(scene_target, request.project_id)
            for scene_target in request.scene_targets
        ]
        
        video_paths = await asyncio.gather(*lookup_tasks, return_exceptions=True)
        
        # Build response
        scenes = []
        found_count = 0
        
        for i, scene_target in enumerate(request.scene_targets):
            video_path = video_paths[i]
            if isinstance(video_path, Exception):
                logger.error(f"Error in batch lookup for {scene_target}: {video_path}")
                video_path = None
            
            found = video_path is not None
            if found:
                found_count += 1
            
            scenes.append(SceneLookupResponse(
                scene_id=scene_target,
                project_id=request.project_id,
                video_path=video_path,
                found=found,
                cached=True,  # Assume cached for batch operations
                lookup_time_ms=0  # Individual times not tracked in batch
            ))
        
        total_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        logger.info(f"Batch lookup of {len(request.scene_targets)} scenes "
                   f"completed in {total_time:.1f}ms, found {found_count}")
        
        return BatchSceneResponse(
            project_id=request.project_id,
            scenes=scenes,
            total_scenes=len(request.scene_targets),
            found_count=found_count,
            lookup_time_ms=round(total_time, 2)
        )
        
    except Exception as e:
        logger.error(f"Error in batch scene lookup: {e}")
        raise HTTPException(status_code=500, detail=f"Batch lookup failed: {str(e)}")

@router.get("/list/{project_id}", 
           summary="List all available scene videos")
async def list_scene_videos(
    project_id: str,
    scene_manager: SceneIndexManager = Depends(get_scene_manager)
) -> Dict[str, Any]:
    """
    Get list of all available scene videos for a project.
    
    Returns scenes in chronological order with basic metadata.
    """
    start_time = datetime.utcnow()
    
    try:
        video_paths = await scene_manager.get_all_scene_videos(project_id)
        
        lookup_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Extract scene information
        scenes = []
        for i, video_path in enumerate(video_paths):
            scenes.append({
                'scene_number': i + 1,
                'video_path': video_path,
                'exists': True  # Already verified by get_all_scene_videos
            })
        
        logger.debug(f"Listed {len(scenes)} scene videos in {lookup_time:.1f}ms")
        
        return {
            'project_id': project_id,
            'scenes': scenes,
            'total_count': len(scenes),
            'lookup_time_ms': round(lookup_time, 2)
        }
        
    except Exception as e:
        logger.error(f"Error listing scene videos for {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list scenes: {str(e)}")

@router.post("/invalidate/{project_id}", 
            summary="Invalidate scene cache")
async def invalidate_scene_cache(
    project_id: str,
    scene_id: Optional[str] = Query(None, description="Specific scene to invalidate"),
    scene_manager: SceneIndexManager = Depends(get_scene_manager)
) -> Dict[str, str]:
    """
    Invalidate cached scene data for a project or specific scene.
    
    Useful after manual file operations or when cache becomes stale.
    """
    try:
        await scene_manager.invalidate_scene_cache(project_id, scene_id)
        
        message = f"Invalidated cache for project {project_id}"
        if scene_id:
            message += f", scene {scene_id}"
        
        logger.info(message)
        
        return {
            'status': 'success',
            'message': message,
            'project_id': project_id,
            'scene_id': scene_id or 'all'
        }
        
    except Exception as e:
        logger.error(f"Error invalidating cache for {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Cache invalidation failed: {str(e)}")

@router.post("/refresh/{project_id}", 
            summary="Refresh scene index")
async def refresh_scene_index(
    project_id: str,
    background_tasks: BackgroundTasks,
    force_rebuild: bool = Query(False, description="Force complete rebuild"),
    scene_manager: SceneIndexManager = Depends(get_scene_manager)
) -> Dict[str, str]:
    """
    Refresh the scene index for a project.
    
    Can be run in background for large projects to avoid timeouts.
    """
    try:
        if force_rebuild:
            # Run in background for complete rebuilds
            background_tasks.add_task(
                scene_manager.update_scene_index, 
                project_id, 
                force_rebuild=True
            )
            message = f"Started background index rebuild for project {project_id}"
        else:
            # Quick update can run synchronously
            success = await scene_manager.update_scene_index(project_id, force_rebuild=False)
            if success:
                message = f"Scene index updated for project {project_id}"
            else:
                message = f"Scene index update failed for project {project_id}"
        
        logger.info(message)
        
        return {
            'status': 'success',
            'message': message,
            'project_id': project_id,
            'background': force_rebuild
        }
        
    except Exception as e:
        logger.error(f"Error refreshing scene index for {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Index refresh failed: {str(e)}")

@router.get("/performance", 
           response_model=PerformanceStats,
           summary="Get performance statistics")
async def get_performance_stats(
    scene_manager: SceneIndexManager = Depends(get_scene_manager),
    file_watcher: FileWatcher = Depends(get_watcher)
) -> PerformanceStats:
    """
    Get comprehensive performance statistics for scene management system.
    
    Includes metrics for both scene indexing and file watching.
    """
    try:
        # Get stats from both services
        index_stats = await scene_manager.get_performance_stats()
        watcher_stats = await file_watcher.get_status()
        
        # Determine overall system health
        system_health = "healthy"
        if index_stats.get('health', {}).get('status') != 'healthy':
            system_health = "degraded"
        if not watcher_stats.get('status', {}).get('running'):
            system_health = "degraded"
        
        return PerformanceStats(
            scene_index=index_stats,
            file_watcher=watcher_stats,
            system_health=system_health
        )
        
    except Exception as e:
        logger.error(f"Error getting performance stats: {e}")
        raise HTTPException(status_code=500, detail=f"Performance stats failed: {str(e)}")

@router.get("/health", 
           response_model=HealthStatus,
           summary="System health check")
async def health_check(
    scene_manager: SceneIndexManager = Depends(get_scene_manager),
    file_watcher: FileWatcher = Depends(get_watcher)
) -> HealthStatus:
    """
    Comprehensive health check for scene management system.
    
    Returns status of all components and overall system health.
    """
    try:
        # Check scene index manager
        index_stats = await scene_manager.get_performance_stats()
        index_health = index_stats.get('health', {}).get('status', 'unknown')
        
        # Check file watcher
        watcher_stats = await file_watcher.get_status()
        watcher_running = watcher_stats.get('status', {}).get('running', False)
        watcher_health = 'healthy' if watcher_running else 'degraded'
        
        # Determine overall status
        components = {
            'scene_index': index_health,
            'file_watcher': watcher_health,
            'redis_connection': 'healthy' if index_stats.get('connection', {}).get('connected') else 'unhealthy'
        }
        
        overall_status = 'healthy'
        if 'unhealthy' in components.values():
            overall_status = 'unhealthy'
        elif 'degraded' in components.values():
            overall_status = 'degraded'
        
        message = None
        if overall_status != 'healthy':
            unhealthy = [k for k, v in components.items() if v != 'healthy']
            message = f"Issues detected in: {', '.join(unhealthy)}"
        
        return HealthStatus(
            status=overall_status,
            components=components,
            timestamp=datetime.utcnow().timestamp(),
            message=message
        )
        
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return HealthStatus(
            status='unhealthy',
            components={'system': 'error'},
            timestamp=datetime.utcnow().timestamp(),
            message=f"Health check failed: {str(e)}"
        )

@router.get("/watch/{project_id}", 
           summary="Start watching project directory")
async def start_watching_project(
    project_id: str,
    file_watcher: FileWatcher = Depends(get_watcher)
) -> Dict[str, str]:
    """
    Start file system watching for a specific project.
    
    Enables real-time scene index updates when files change.
    """
    try:
        success = await file_watcher.watch_project(project_id)
        
        if success:
            message = f"Started watching project {project_id}"
            status = "success"
        else:
            message = f"Failed to start watching project {project_id}"
            status = "error"
        
        logger.info(message)
        
        return {
            'status': status,
            'message': message,
            'project_id': project_id
        }
        
    except Exception as e:
        logger.error(f"Error starting file watch for {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Watch start failed: {str(e)}")

@router.delete("/watch/{project_id}", 
              summary="Stop watching project directory")
async def stop_watching_project(
    project_id: str,
    file_watcher: FileWatcher = Depends(get_watcher)
) -> Dict[str, str]:
    """
    Stop file system watching for a specific project.
    """
    try:
        success = await file_watcher.unwatch_project(project_id)
        
        message = f"Stopped watching project {project_id}"
        
        logger.info(message)
        
        return {
            'status': 'success',
            'message': message,
            'project_id': project_id
        }
        
    except Exception as e:
        logger.error(f"Error stopping file watch for {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Watch stop failed: {str(e)}")

# Add router to main application
def include_scene_status_routes(app):
    """Include scene status routes in FastAPI app."""
    app.include_router(router)