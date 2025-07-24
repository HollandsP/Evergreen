"""
Video Streaming API Routes - Optimized Video Delivery

Provides high-performance video streaming endpoints with HTTP range support,
adaptive streaming, and scene-based video delivery.

Performance Features:
- HTTP range request support for seeking
- Adaptive chunk sizing based on file size and connection
- Memory-efficient streaming for large files (4K+ video support)
- Redis-cached scene lookups for <100ms response
- Smart content type detection and caching headers
"""

import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, Request, HTTPException, Depends, Path as FastAPIPath, Query
from fastapi.responses import StreamingResponse

from src.utils.video_streaming import get_video_streaming_manager, VideoStreamingManager
from src.services.scene_index_manager import get_scene_index_manager, SceneIndexManager

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/stream", tags=["Video Streaming"])

# Dependency injection
async def get_streaming_manager() -> VideoStreamingManager:
    """Get video streaming manager dependency."""
    return get_video_streaming_manager()

async def get_scene_manager() -> SceneIndexManager:
    """Get scene index manager dependency."""
    return await get_scene_index_manager()

@router.get("/video/{file_path:path}",
           summary="Stream video file with range support")
async def stream_video_file(
    file_path: str = FastAPIPath(..., description="Path to video file"),
    request: Request = None,
    streaming_manager: VideoStreamingManager = Depends(get_streaming_manager)
) -> StreamingResponse:
    """
    Stream a video file with HTTP range support for seeking.
    
    Features:
    - HTTP range requests for video seeking
    - Adaptive chunk sizing for optimal performance
    - Proper MIME type detection
    - Caching headers for performance
    
    Args:
        file_path: Path to video file (URL encoded)
        request: FastAPI request object with range headers
        
    Returns:
        StreamingResponse with video content
    """
    try:
        return await streaming_manager.streamer.stream_video(file_path, request)
        
    except FileNotFoundError:
        raise HTTPException(
            status_code=404, 
            detail=f"Video file not found: {file_path}"
        )
    except Exception as e:
        logger.error(f"Error streaming video file {file_path}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Video streaming failed: {str(e)}"
        )

@router.get("/scene/{project_id}/{scene_id}",
           summary="Stream scene video with optimized lookup")
async def stream_scene_video(
    project_id: str = FastAPIPath(..., description="Project identifier"),
    scene_id: str = FastAPIPath(..., description="Scene identifier (e.g., 'scene_1')"),
    request: Request = None,
    streaming_manager: VideoStreamingManager = Depends(get_streaming_manager)
) -> StreamingResponse:
    """
    Stream a scene video with fast O(1) lookup and range support.
    
    Uses the Scene Index Manager for sub-100ms scene resolution,
    then streams with optimized chunking and range support.
    
    Args:
        project_id: Project identifier
        scene_id: Scene identifier (e.g., 'scene_1', 'scene_2')
        request: FastAPI request object with range headers
        
    Returns:
        StreamingResponse with scene video content
    """
    try:
        return await streaming_manager.stream_scene_video(scene_id, project_id, request)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error streaming scene video {project_id}/{scene_id}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Scene video streaming failed: {str(e)}"
        )

@router.get("/info/{file_path:path}",
           summary="Get video file information")
async def get_video_info(
    file_path: str = FastAPIPath(..., description="Path to video file"),
    streaming_manager: VideoStreamingManager = Depends(get_streaming_manager)
) -> Dict[str, Any]:
    """
    Get video file metadata and streaming information.
    
    Returns information about video duration, resolution, file size,
    and streaming capabilities.
    
    Args:
        file_path: Path to video file
        
    Returns:
        Dictionary with video metadata
    """
    try:
        return await streaming_manager.streamer.get_video_info(file_path)
        
    except FileNotFoundError:
        raise HTTPException(
            status_code=404, 
            detail=f"Video file not found: {file_path}"
        )
    except Exception as e:
        logger.error(f"Error getting video info for {file_path}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Video info failed: {str(e)}"
        )

@router.get("/scene-info/{project_id}/{scene_id}",
           summary="Get scene video information")
async def get_scene_video_info(
    project_id: str = FastAPIPath(..., description="Project identifier"),
    scene_id: str = FastAPIPath(..., description="Scene identifier"),
    scene_manager: SceneIndexManager = Depends(get_scene_manager),
    streaming_manager: VideoStreamingManager = Depends(get_streaming_manager)
) -> Dict[str, Any]:
    """
    Get scene video metadata and streaming information.
    
    Combines fast scene lookup with detailed video metadata.
    
    Args:
        project_id: Project identifier
        scene_id: Scene identifier
        
    Returns:
        Dictionary with scene video metadata
    """
    try:
        # Find scene video using optimized lookup
        video_path = await scene_manager.find_scene_video(scene_id, project_id)
        
        if not video_path:
            raise HTTPException(
                status_code=404,
                detail=f"Scene video not found: {project_id}/{scene_id}"
            )
        
        # Get video metadata
        video_info = await streaming_manager.streamer.get_video_info(video_path)
        
        # Add scene-specific information
        video_info.update({
            'project_id': project_id,
            'scene_id': scene_id,
            'streaming_endpoint': f"/api/v1/stream/scene/{project_id}/{scene_id}"
        })
        
        return video_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting scene video info {project_id}/{scene_id}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Scene video info failed: {str(e)}"
        )

@router.get("/playlist/{project_id}",
           summary="Get project video playlist")
async def get_project_playlist(
    project_id: str = FastAPIPath(..., description="Project identifier"),
    include_metadata: bool = Query(False, description="Include detailed video metadata"),
    scene_manager: SceneIndexManager = Depends(get_scene_manager),
    streaming_manager: VideoStreamingManager = Depends(get_streaming_manager)
) -> Dict[str, Any]:
    """
    Get playlist of all scene videos for a project.
    
    Returns chronologically ordered list of scene videos with
    streaming endpoints and optional metadata.
    
    Args:
        project_id: Project identifier
        include_metadata: Whether to include detailed video metadata
        
    Returns:
        Dictionary with project playlist information
    """
    try:
        # Get all scene videos using optimized lookup
        scene_videos = await scene_manager.get_all_scene_videos(project_id)
        
        playlist = {
            'project_id': project_id,
            'total_scenes': len(scene_videos),
            'scenes': []
        }
        
        for i, video_path in enumerate(scene_videos):
            scene_number = i + 1
            scene_id = f"scene_{scene_number}"
            
            scene_info = {
                'scene_number': scene_number,
                'scene_id': scene_id,
                'video_path': video_path,
                'streaming_endpoint': f"/api/v1/stream/scene/{project_id}/{scene_id}"
            }
            
            # Add detailed metadata if requested
            if include_metadata:
                try:
                    video_metadata = await streaming_manager.streamer.get_video_info(video_path)
                    scene_info.update({
                        'file_size': video_metadata.get('file_size'),
                        'duration': video_metadata.get('duration'),
                        'resolution': video_metadata.get('resolution'),
                        'format': video_metadata.get('format')
                    })
                except Exception as e:
                    logger.warning(f"Could not get metadata for {video_path}: {e}")
                    scene_info['metadata_error'] = str(e)
            
            playlist['scenes'].append(scene_info)
        
        return playlist
        
    except Exception as e:
        logger.error(f"Error creating playlist for project {project_id}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Playlist creation failed: {str(e)}"
        )

@router.get("/stats",
           summary="Get video streaming statistics")
async def get_streaming_stats(
    streaming_manager: VideoStreamingManager = Depends(get_streaming_manager)
) -> Dict[str, Any]:
    """
    Get video streaming performance statistics.
    
    Returns metrics about streaming performance, cache usage,
    and system configuration.
    
    Returns:
        Dictionary with streaming statistics
    """
    try:
        return await streaming_manager.get_streaming_stats()
        
    except Exception as e:
        logger.error(f"Error getting streaming stats: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Streaming stats failed: {str(e)}"
        )

@router.post("/preload/{project_id}",
            summary="Preload project videos for optimal streaming")
async def preload_project_videos(
    project_id: str = FastAPIPath(..., description="Project identifier"),
    scene_manager: SceneIndexManager = Depends(get_scene_manager)
) -> Dict[str, Any]:
    """
    Preload project videos into cache for optimal streaming performance.
    
    This endpoint triggers index updates and cache warming for
    improved streaming performance.
    
    Args:
        project_id: Project identifier
        
    Returns:
        Dictionary with preload results
    """
    try:
        # Update scene index to ensure latest files are cached
        success = await scene_manager.update_scene_index(project_id, force_rebuild=False)
        
        # Get scene videos to warm the cache
        scene_videos = await scene_manager.get_all_scene_videos(project_id)
        
        return {
            'project_id': project_id,
            'preload_status': 'success' if success else 'partial',
            'scenes_cached': len(scene_videos),
            'message': f"Preloaded {len(scene_videos)} scene videos for optimal streaming"
        }
        
    except Exception as e:
        logger.error(f"Error preloading project {project_id}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Video preload failed: {str(e)}"
        )

# Add router to main application
def include_video_streaming_routes(app):
    """Include video streaming routes in FastAPI app."""
    app.include_router(router)