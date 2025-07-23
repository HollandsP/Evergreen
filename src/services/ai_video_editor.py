"""
AI Video Editor with Natural Language Chat Interface.

This service combines GPT-4 for natural language understanding with MoviePy and FFmpeg
for programmatic video editing, enabling chat-based video editing commands.
"""

import os
import json
import asyncio
import logging
import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

import openai
from .moviepy_wrapper import MoviePyWrapper
from .ffmpeg_service import FFmpegService

logger = logging.getLogger(__name__)

class AIVideoEditor:
    """
    AI-powered video editor with natural language chat interface.
    
    Features:
    - Natural language command parsing with GPT-4
    - Storyboard-aware editing decisions
    - Real-time preview generation
    - Chat-based editing interface
    - Integration with MoviePy and FFmpeg
    """
    
    def __init__(self, 
                 openai_api_key: Optional[str] = None,
                 work_dir: str = "./output/editor_workspace"):
        """
        Initialize AI Video Editor.
        
        Args:
            openai_api_key: OpenAI API key for GPT-4
            work_dir: Working directory for temporary files
        """
        self.openai_client = openai.OpenAI(
            api_key=openai_api_key or os.getenv('OPENAI_API_KEY')
        )
        self.moviepy = MoviePyWrapper()
        self.ffmpeg = FFmpegService()
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        
        # Chat history and context
        self.chat_history: List[Dict[str, str]] = []
        self.project_context: Dict[str, Any] = {}
        self.current_timeline: Optional[Dict[str, Any]] = None
        
        # Command parsing system prompt
        self.system_prompt = self._build_system_prompt()
        
        logger.info("Initialized AI Video Editor with GPT-4 integration")
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for GPT-4 command parsing."""
        return """You are an AI video editor assistant. Your job is to parse natural language video editing commands and convert them into structured editing operations.

You have access to these editing capabilities:
1. CUT/TRIM: Remove sections from videos
2. FADE: Add fade in/out transitions
3. SPEED: Change playback speed
4. SYNC: Synchronize audio/video with beats or timestamps
5. TRANSITION: Add transitions between clips
6. OVERLAY: Add text, images, or effects
7. SPLIT: Split clips into multiple parts
8. MERGE: Combine multiple clips
9. AUDIO_MIX: Adjust audio levels and mixing
10. COLOR_GRADE: Apply color corrections

When given a command, respond with a JSON object containing:
{
    "operation": "operation_type",
    "parameters": {
        "target": "scene_number or clip_identifier",
        "values": {...specific parameters...}
    },
    "confidence": 0.0-1.0,
    "explanation": "Brief explanation of what will happen"
}

Example commands and responses:

Command: "Cut the first 3 seconds of scene 2"
Response: {
    "operation": "CUT",
    "parameters": {
        "target": "scene_2",
        "start_time": 0,
        "duration": 3
    },
    "confidence": 0.95,
    "explanation": "Will remove the first 3 seconds from scene 2"
}

Command: "Add fade transition between all scenes"
Response: {
    "operation": "TRANSITION",
    "parameters": {
        "target": "all_scenes",
        "transition_type": "fade",
        "duration": 1.0
    },
    "confidence": 0.9,
    "explanation": "Will add 1-second fade transitions between all scene clips"
}

Command: "Speed up scene 4 by 1.5x"
Response: {
    "operation": "SPEED",
    "parameters": {
        "target": "scene_4", 
        "multiplier": 1.5
    },
    "confidence": 0.95,
    "explanation": "Will increase playback speed of scene 4 by 1.5x"
}

Always provide valid JSON responses. If unsure about a command, set confidence < 0.7 and ask for clarification."""

    async def process_chat_command(self, 
                                 command: str, 
                                 project_id: str,
                                 storyboard_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a natural language editing command through chat interface.
        
        Args:
            command: Natural language editing command
            project_id: Project identifier for context
            storyboard_data: Storyboard information for context-aware editing
            
        Returns:
            Processing result with operation details and preview
        """
        try:
            # Update project context
            if storyboard_data:
                self.project_context[project_id] = storyboard_data
            
            # Add command to chat history
            self.chat_history.append({
                "role": "user",
                "content": command,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Parse command with GPT-4
            parsed_operation = await self._parse_command_with_gpt4(command, project_id)
            
            if parsed_operation["confidence"] < 0.7:
                return {
                    "success": False,
                    "message": "Command unclear. " + parsed_operation.get("explanation", "Please rephrase."),
                    "suggestions": await self._get_command_suggestions()
                }
            
            # Execute the operation
            result = await self._execute_operation(parsed_operation, project_id)
            
            # Add response to chat history
            self.chat_history.append({
                "role": "assistant", 
                "content": result["message"],
                "timestamp": datetime.utcnow().isoformat(),
                "operation": parsed_operation
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing chat command: {e}")
            return {
                "success": False,
                "message": f"Error processing command: {str(e)}",
                "error": str(e)
            }
    
    async def _parse_command_with_gpt4(self, command: str, project_id: str) -> Dict[str, Any]:
        """Parse natural language command using GPT-4."""
        try:
            # Build context for the AI
            context_info = ""
            if project_id in self.project_context:
                storyboard = self.project_context[project_id]
                scenes = storyboard.get("scenes", [])
                context_info = f"\nProject has {len(scenes)} scenes: {[f'Scene {i+1}' for i in range(len(scenes))]}"
            
            # Recent chat history for context
            recent_history = ""
            if len(self.chat_history) > 0:
                recent_msgs = self.chat_history[-3:]  # Last 3 messages
                recent_history = "\nRecent conversation:\n" + "\n".join([
                    f"{msg['role']}: {msg['content']}" for msg in recent_msgs
                ])
            
            full_prompt = f"{self.system_prompt}{context_info}{recent_history}\n\nCommand: {command}"
            
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model="gpt-4",
                messages=[
                    {"role": "system", "content": full_prompt},
                    {"role": "user", "content": command}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            # Parse the JSON response
            response_text = response.choices[0].message.content.strip()
            
            # Extract JSON from response (GPT-4 sometimes adds explanatory text)
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "{" in response_text:
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                response_text = response_text[json_start:json_end]
            
            parsed = json.loads(response_text)
            logger.info(f"GPT-4 parsed command: {parsed}")
            return parsed
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse GPT-4 response as JSON: {e}")
            return {
                "operation": "UNKNOWN",
                "parameters": {},
                "confidence": 0.0,
                "explanation": "Failed to understand the command format."
            }
        except Exception as e:
            logger.error(f"Error calling GPT-4: {e}")
            return {
                "operation": "ERROR",
                "parameters": {},
                "confidence": 0.0,
                "explanation": f"Error processing command: {str(e)}"
            }
    
    async def _execute_operation(self, operation: Dict[str, Any], project_id: str) -> Dict[str, Any]:
        """Execute a parsed editing operation."""
        try:
            op_type = operation["operation"]
            params = operation["parameters"]
            target = params.get("target", "")
            
            # Generate unique operation ID
            operation_id = str(uuid.uuid4())
            
            if op_type == "CUT":
                result = await self._execute_cut_operation(params, project_id, operation_id)
            elif op_type == "FADE":
                result = await self._execute_fade_operation(params, project_id, operation_id)
            elif op_type == "SPEED":
                result = await self._execute_speed_operation(params, project_id, operation_id)
            elif op_type == "TRANSITION":
                result = await self._execute_transition_operation(params, project_id, operation_id)
            elif op_type == "SYNC":
                result = await self._execute_sync_operation(params, project_id, operation_id)
            elif op_type == "OVERLAY":
                result = await self._execute_overlay_operation(params, project_id, operation_id)
            elif op_type == "AUDIO_MIX":
                result = await self._execute_audio_mix_operation(params, project_id, operation_id)
            else:
                result = {
                    "success": False,
                    "message": f"Operation '{op_type}' not yet implemented",
                    "operation_id": operation_id
                }
            
            # Generate preview if successful
            if result["success"] and "output_path" in result:
                preview_path = await self._generate_preview(result["output_path"], operation_id)
                result["preview_url"] = f"/api/editor/preview/{operation_id}"
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing operation: {e}")
            return {
                "success": False,
                "message": f"Error executing operation: {str(e)}",
                "error": str(e)
            }
    
    async def _execute_cut_operation(self, params: Dict[str, Any], project_id: str, operation_id: str) -> Dict[str, Any]:
        """Execute cut/trim operation."""
        target = params.get("target", "")
        start_time = params.get("start_time", 0)
        duration = params.get("duration")
        end_time = params.get("end_time")
        
        # Find target video file
        input_path = self._find_scene_video(target, project_id)
        if not input_path:
            return {
                "success": False,
                "message": f"Could not find video for {target}",
                "operation_id": operation_id
            }
        
        # Generate output path
        output_path = self.work_dir / f"{operation_id}_cut.mp4"
        
        # Use MoviePy for precise cutting
        await asyncio.to_thread(
            self.moviepy.trim_video,
            str(input_path),
            str(output_path),
            start_time=start_time,
            duration=duration,
            end_time=end_time
        )
        
        return {
            "success": True,
            "message": f"Cut applied to {target}",
            "operation_id": operation_id,
            "output_path": str(output_path),
            "operation_type": "CUT",
            "parameters": params
        }
    
    async def _execute_fade_operation(self, params: Dict[str, Any], project_id: str, operation_id: str) -> Dict[str, Any]:
        """Execute fade in/out operation."""
        target = params.get("target", "")
        fade_type = params.get("fade_type", "in")  # "in", "out", or "both"
        duration = params.get("duration", 1.0)
        
        input_path = self._find_scene_video(target, project_id)
        if not input_path:
            return {
                "success": False,
                "message": f"Could not find video for {target}",
                "operation_id": operation_id
            }
        
        output_path = self.work_dir / f"{operation_id}_fade.mp4"
        
        # Use MoviePy for fade effects
        await asyncio.to_thread(
            self.moviepy.add_fade_effect,
            str(input_path),
            str(output_path),
            fade_type=fade_type,
            duration=duration
        )
        
        return {
            "success": True,
            "message": f"Fade {fade_type} applied to {target}",
            "operation_id": operation_id,
            "output_path": str(output_path),
            "operation_type": "FADE",
            "parameters": params
        }
    
    async def _execute_speed_operation(self, params: Dict[str, Any], project_id: str, operation_id: str) -> Dict[str, Any]:
        """Execute speed change operation."""
        target = params.get("target", "")
        multiplier = params.get("multiplier", 1.0)
        
        input_path = self._find_scene_video(target, project_id)
        if not input_path:
            return {
                "success": False,
                "message": f"Could not find video for {target}",
                "operation_id": operation_id
            }
        
        output_path = self.work_dir / f"{operation_id}_speed.mp4"
        
        # Use MoviePy for speed adjustment
        await asyncio.to_thread(
            self.moviepy.change_speed,
            str(input_path),
            str(output_path),
            speed_factor=multiplier
        )
        
        return {
            "success": True,
            "message": f"Speed changed to {multiplier}x for {target}",
            "operation_id": operation_id,
            "output_path": str(output_path),
            "operation_type": "SPEED",
            "parameters": params
        }
    
    async def _execute_transition_operation(self, params: Dict[str, Any], project_id: str, operation_id: str) -> Dict[str, Any]:
        """Execute transition between clips operation."""
        target = params.get("target", "")
        transition_type = params.get("transition_type", "fade")
        duration = params.get("duration", 1.0)
        
        if target == "all_scenes":
            # Add transitions between all scenes
            scene_videos = self._get_all_scene_videos(project_id)
            if len(scene_videos) < 2:
                return {
                    "success": False,
                    "message": "Need at least 2 scenes for transitions",
                    "operation_id": operation_id
                }
            
            output_path = self.work_dir / f"{operation_id}_transitions.mp4"
            
            # Use MoviePy to create transitions
            await asyncio.to_thread(
                self.moviepy.add_transitions_between_clips,
                scene_videos,
                str(output_path),
                transition_type=transition_type,
                duration=duration
            )
            
            return {
                "success": True,
                "message": f"Added {transition_type} transitions between all scenes",
                "operation_id": operation_id,
                "output_path": str(output_path),
                "operation_type": "TRANSITION",
                "parameters": params
            }
        else:
            return {
                "success": False,
                "message": "Specific scene transitions not yet implemented",
                "operation_id": operation_id
            }
    
    async def _execute_sync_operation(self, params: Dict[str, Any], project_id: str, operation_id: str) -> Dict[str, Any]:
        """Execute audio-video sync operation."""
        target = params.get("target", "")
        sync_type = params.get("sync_type", "beat")  # "beat", "timestamp", "audio"
        
        # This is a complex operation that would analyze audio beats
        # For now, return a placeholder implementation
        return {
            "success": False,
            "message": f"Audio sync feature coming soon for {target}",
            "operation_id": operation_id,
            "operation_type": "SYNC",
            "parameters": params
        }
    
    async def _execute_overlay_operation(self, params: Dict[str, Any], project_id: str, operation_id: str) -> Dict[str, Any]:
        """Execute overlay (text, images, effects) operation."""
        target = params.get("target", "")
        overlay_type = params.get("overlay_type", "text")
        content = params.get("content", "")
        position = params.get("position", "center")
        
        input_path = self._find_scene_video(target, project_id)
        if not input_path:
            return {
                "success": False,
                "message": f"Could not find video for {target}",
                "operation_id": operation_id
            }
        
        output_path = self.work_dir / f"{operation_id}_overlay.mp4"
        
        if overlay_type == "text":
            # Use MoviePy to add text overlay
            await asyncio.to_thread(
                self.moviepy.add_text_overlay,
                str(input_path),
                str(output_path),
                text=content,
                position=position
            )
        else:
            return {
                "success": False,
                "message": f"Overlay type '{overlay_type}' not yet supported",
                "operation_id": operation_id
            }
        
        return {
            "success": True,
            "message": f"Added {overlay_type} overlay to {target}",
            "operation_id": operation_id,
            "output_path": str(output_path),
            "operation_type": "OVERLAY",
            "parameters": params
        }
    
    async def _execute_audio_mix_operation(self, params: Dict[str, Any], project_id: str, operation_id: str) -> Dict[str, Any]:
        """Execute audio mixing operation."""
        target = params.get("target", "")
        volume_level = params.get("volume", 1.0)
        
        input_path = self._find_scene_video(target, project_id)
        if not input_path:
            return {
                "success": False,
                "message": f"Could not find video for {target}",
                "operation_id": operation_id
            }
        
        output_path = self.work_dir / f"{operation_id}_audio_mix.mp4"
        
        # Use MoviePy to adjust audio levels
        await asyncio.to_thread(
            self.moviepy.adjust_audio_volume,
            str(input_path),
            str(output_path),
            volume_factor=volume_level
        )
        
        return {
            "success": True,
            "message": f"Audio volume adjusted to {volume_level}x for {target}",
            "operation_id": operation_id,
            "output_path": str(output_path),
            "operation_type": "AUDIO_MIX",
            "parameters": params
        }
    
    def _find_scene_video(self, target: str, project_id: str) -> Optional[Path]:
        """Find video file for a specific scene target."""
        # Parse target (e.g., "scene_2", "scene_1", etc.)
        if target.startswith("scene_"):
            try:
                scene_num = int(target.split("_")[1])
                # Look for the scene video in project output directory
                scene_patterns = [
                    f"output/log_{project_id}/scenes/scene_{scene_num}_composite.mp4",
                    f"output/projects/{project_id}/scenes/scene_{scene_num}.mp4",
                    f"output/scenes/scene_{scene_num}.mp4"
                ]
                
                for pattern in scene_patterns:
                    path = Path(pattern)
                    if path.exists():
                        return path
                        
            except (ValueError, IndexError):
                pass
        
        # Try direct path matching
        possible_paths = [
            Path(f"output/{target}.mp4"),
            Path(f"output/scenes/{target}.mp4"),
            Path(target)  # Direct path
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        return None
    
    def _get_all_scene_videos(self, project_id: str) -> List[str]:
        """Get all scene video files for a project."""
        scene_videos = []
        
        # Look in common scene directories
        scene_dirs = [
            Path(f"output/log_{project_id}/scenes/"),
            Path(f"output/projects/{project_id}/scenes/"),
            Path("output/scenes/")
        ]
        
        for scene_dir in scene_dirs:
            if scene_dir.exists():
                # Find all scene files
                for scene_file in sorted(scene_dir.glob("scene_*_composite.mp4")):
                    scene_videos.append(str(scene_file))
                if scene_videos:
                    break  # Use first directory that has scenes
        
        return scene_videos
    
    async def _generate_preview(self, video_path: str, operation_id: str) -> str:
        """Generate a preview thumbnail and short clip for the operation result."""
        try:
            preview_dir = self.work_dir / "previews"
            preview_dir.mkdir(exist_ok=True)
            
            # Generate thumbnail
            thumbnail_path = preview_dir / f"{operation_id}_thumb.jpg"
            await asyncio.to_thread(
                self.ffmpeg.generate_thumbnail,
                video_path,
                str(thumbnail_path),
                timestamp=1.0
            )
            
            # Generate short preview clip (first 5 seconds)
            preview_clip_path = preview_dir / f"{operation_id}_preview.mp4"
            await asyncio.to_thread(
                self.ffmpeg.extract_segment,
                video_path,
                str(preview_clip_path),
                start_time=0,
                duration=5
            )
            
            return str(preview_clip_path)
            
        except Exception as e:
            logger.error(f"Error generating preview: {e}")
            return ""
    
    async def _get_command_suggestions(self) -> List[str]:
        """Get suggested commands for the user."""
        return [
            "Cut the first 3 seconds of scene 1",
            "Add fade transition between all scenes", 
            "Speed up scene 2 by 1.5x",
            "Add text overlay 'THE END' to the last scene",
            "Reduce audio volume to 50% for scene 3",
            "Add fade out at the end of the video"
        ]
    
    def get_chat_history(self) -> List[Dict[str, str]]:
        """Get the current chat history."""
        return self.chat_history.copy()
    
    def clear_chat_history(self):
        """Clear the chat history."""
        self.chat_history.clear()
        logger.info("Chat history cleared")
    
    def get_project_context(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project context information."""
        return self.project_context.get(project_id)
    
    def set_project_context(self, project_id: str, context: Dict[str, Any]):
        """Set project context information."""
        self.project_context[project_id] = context
        logger.info(f"Updated project context for {project_id}")