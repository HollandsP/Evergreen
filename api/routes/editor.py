"""
Video editor API endpoints for AI-powered video editing.
"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
import structlog

from ..dependencies import get_current_user
from ..validators import validate_request
from src.services.ai_video_editor import AIVideoEditor

logger = structlog.get_logger()

router = APIRouter(prefix="/editor", tags=["editor"])

# Global AI Video Editor instance
ai_editor: Optional[AIVideoEditor] = None

def get_ai_editor() -> AIVideoEditor:
    """Get or create the AI Video Editor instance."""
    global ai_editor
    if ai_editor is None:
        ai_editor = AIVideoEditor()
    return ai_editor

class ProcessCommandRequest(BaseModel):
    """Request model for processing video editing commands."""
    command: str = Field(..., description="Natural language editing command")
    project_id: str = Field(..., description="Project identifier")
    storyboard_data: Optional[Dict[str, Any]] = Field(None, description="Storyboard context data")

class ProcessCommandResponse(BaseModel):
    """Response model for processed editing commands."""
    success: bool
    message: str
    operation: Optional[Dict[str, Any]] = None
    operation_id: Optional[str] = None
    preview_url: Optional[str] = None
    output_path: Optional[str] = None
    error: Optional[str] = None
    suggestions: Optional[list[str]] = None

class ChatHistoryResponse(BaseModel):
    """Response model for chat history."""
    messages: list[Dict[str, Any]]
    project_context: Optional[Dict[str, Any]] = None

class ProjectContextRequest(BaseModel):
    """Request model for setting project context."""
    project_id: str = Field(..., description="Project identifier")
    context: Dict[str, Any] = Field(..., description="Project context data")

@router.post("/process-command", response_model=ProcessCommandResponse)
async def process_command(
    request: ProcessCommandRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Process a natural language video editing command.
    
    This endpoint accepts natural language commands like:
    - "Cut the first 3 seconds of scene 2"
    - "Add fade transition between all scenes"
    - "Speed up scene 4 by 1.5x"
    - "Add text overlay 'THE END' to the last scene"
    """
    try:
        # Validate the request
        validate_request(request.dict(), {
            'command': {'required': True, 'min_length': 1},
            'project_id': {'required': True, 'min_length': 1}
        })
        
        editor = get_ai_editor()
        
        # Process the command asynchronously
        result = await editor.process_chat_command(
            command=request.command,
            project_id=request.project_id,
            storyboard_data=request.storyboard_data
        )
        
        logger.info(
            "Processed editing command",
            command=request.command,
            project_id=request.project_id,
            success=result.get('success'),
            operation_type=result.get('operation', {}).get('operation')
        )
        
        return ProcessCommandResponse(
            success=result.get('success', False),
            message=result.get('message', 'Command processed'),
            operation=result.get('operation'),
            operation_id=result.get('operation_id'),
            preview_url=result.get('preview_url'),
            output_path=result.get('output_path'),
            error=result.get('error'),
            suggestions=result.get('suggestions')
        )
        
    except ValueError as e:
        logger.warning("Invalid command request", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error processing editing command", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/chat-history/{project_id}", response_model=ChatHistoryResponse)
async def get_chat_history(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get the chat history for a project."""
    try:
        editor = get_ai_editor()
        
        messages = editor.get_chat_history()
        project_context = editor.get_project_context(project_id)
        
        return ChatHistoryResponse(
            messages=messages,
            project_context=project_context
        )
        
    except Exception as e:
        logger.error("Error retrieving chat history", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/chat-history")
async def clear_chat_history(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Clear the chat history."""
    try:
        editor = get_ai_editor()
        editor.clear_chat_history()
        
        return {"success": True, "message": "Chat history cleared"}
        
    except Exception as e:
        logger.error("Error clearing chat history", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/project-context")
async def set_project_context(
    request: ProjectContextRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Set project context for better editing decisions."""
    try:
        editor = get_ai_editor()
        editor.set_project_context(request.project_id, request.context)
        
        logger.info(
            "Updated project context",
            project_id=request.project_id,
            context_keys=list(request.context.keys())
        )
        
        return {"success": True, "message": "Project context updated"}
        
    except Exception as e:
        logger.error("Error setting project context", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/project-context/{project_id}")
async def get_project_context(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get project context."""
    try:
        editor = get_ai_editor()
        context = editor.get_project_context(project_id)
        
        return {
            "success": True,
            "project_id": project_id,
            "context": context
        }
        
    except Exception as e:
        logger.error("Error retrieving project context", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/suggestions")
async def get_command_suggestions(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get suggested editing commands."""
    try:
        suggestions = [
            "Cut the first 3 seconds of scene 1",
            "Add fade transition between all scenes",
            "Speed up scene 2 by 1.5x", 
            "Add text overlay 'THE END' to the last scene",
            "Reduce audio volume to 50% for scene 3",
            "Add fade out at the end of the video",
            "Split scene 4 at 5 seconds",
            "Add crossfade between scene 1 and 2",
            "Brighten scene 3 by 20%",
            "Remove audio from scene 2"
        ]
        
        return {
            "success": True,
            "suggestions": suggestions
        }
        
    except Exception as e:
        logger.error("Error getting suggestions", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/operations/{operation_id}/status")
async def get_operation_status(
    operation_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get the status of a video editing operation."""
    try:
        # This would check the status of a background operation
        # For now, return a mock status
        return {
            "success": True,
            "operation_id": operation_id,
            "status": "completed",
            "progress": 100,
            "message": "Operation completed successfully",
            "output_available": True
        }
        
    except Exception as e:
        logger.error("Error getting operation status", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/health")
async def editor_health_check():
    """Comprehensive health check endpoint for the video editor service."""
    try:
        editor = get_ai_editor()
        
        # Get comprehensive health status
        health_status = await editor.get_health_status()
        health_status["timestamp"] = datetime.utcnow().isoformat()
        
        return health_status
        
    except Exception as e:
        logger.error("Editor health check failed", error=str(e))
        return {
            "overall_health": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "can_edit_videos": False
        }