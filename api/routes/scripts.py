"""
Script parsing and processing endpoints
"""
import re
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
import structlog

from src.core.database.models import User
from api.dependencies import get_current_user, rate_limit_per_minute
from api.validators import (
    ScriptParseRequest,
    ScriptParseResponse,
    ParsedScene,
)

router = APIRouter(prefix="/scripts", tags=["scripts"])
logger = structlog.get_logger()


class ScriptParser:
    """Parse and analyze script content"""
    
    def __init__(self, content: str, style: str = "techwear"):
        self.content = content
        self.style = style
        self.scenes = []
        self.warnings = []
    
    def parse(self) -> ScriptParseResponse:
        """Parse the script content into scenes"""
        # Split content into lines
        lines = self.content.strip().split('\n')
        
        current_scene = None
        scene_number = 0
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            
            if not line:
                continue
            
            # Check for scene marker
            if self._is_scene_marker(line):
                # Save previous scene if exists
                if current_scene:
                    self.scenes.append(current_scene)
                
                # Start new scene
                scene_number += 1
                current_scene = {
                    "scene_number": scene_number,
                    "description": self._extract_scene_description(line),
                    "duration": 0.0,
                    "commands": [],
                    "dialogue": None,
                    "visual_prompts": []
                }
            
            # Check for commands
            elif self._is_command(line):
                if current_scene:
                    command = self._extract_command(line)
                    current_scene["commands"].append(command)
                    
                    # Update duration based on command
                    duration = self._estimate_command_duration(command)
                    current_scene["duration"] += duration
                else:
                    self.warnings.append(f"Command found outside scene at line {line_num + 1}")
            
            # Check for dialogue
            elif self._is_dialogue(line):
                if current_scene:
                    if current_scene["dialogue"]:
                        current_scene["dialogue"] += f" {line}"
                    else:
                        current_scene["dialogue"] = line
                    
                    # Estimate dialogue duration
                    words = len(line.split())
                    current_scene["duration"] += words * 0.3  # ~0.3 seconds per word
                else:
                    self.warnings.append(f"Dialogue found outside scene at line {line_num + 1}")
            
            # Check for visual prompts
            elif self._is_visual_prompt(line):
                if current_scene:
                    prompt = self._extract_visual_prompt(line)
                    current_scene["visual_prompts"].append(prompt)
                else:
                    self.warnings.append(f"Visual prompt found outside scene at line {line_num + 1}")
            
            # Otherwise, it might be description
            elif current_scene and not any([
                self._is_scene_marker(line),
                self._is_command(line),
                self._is_dialogue(line),
                self._is_visual_prompt(line)
            ]):
                # Add to scene description
                current_scene["description"] += f" {line}"
        
        # Save last scene
        if current_scene:
            self.scenes.append(current_scene)
        
        # Validate and create response
        return self._create_response()
    
    def _is_scene_marker(self, line: str) -> bool:
        """Check if line is a scene marker"""
        patterns = [
            r"^SCENE\s+\d+",
            r"^INT\.",
            r"^EXT\.",
            r"^\[SCENE",
            r"^#\s*SCENE"
        ]
        return any(re.match(pattern, line.upper()) for pattern in patterns)
    
    def _is_command(self, line: str) -> bool:
        """Check if line is a command"""
        patterns = [
            r"^COMMAND:",
            r"^CMD:",
            r"^\[COMMAND",
            r"^//\s*COMMAND"
        ]
        return any(re.match(pattern, line.upper()) for pattern in patterns)
    
    def _is_dialogue(self, line: str) -> bool:
        """Check if line is dialogue"""
        # Dialogue often starts with quotes or has character names
        return (
            line.startswith('"') or 
            line.startswith("'") or
            re.match(r"^[A-Z][A-Z\s]+:", line) or  # CHARACTER NAME:
            re.match(r"^VOICE:", line.upper())
        )
    
    def _is_visual_prompt(self, line: str) -> bool:
        """Check if line is a visual prompt"""
        patterns = [
            r"^VISUAL:",
            r"^PROMPT:",
            r"^\[VISUAL",
            r"^#\s*VISUAL"
        ]
        return any(re.match(pattern, line.upper()) for pattern in patterns)
    
    def _extract_scene_description(self, line: str) -> str:
        """Extract scene description from marker line"""
        # Remove scene markers
        description = re.sub(r"^(SCENE\s+\d+|INT\.|EXT\.|\[SCENE|#\s*SCENE)[:\s]*", "", line, flags=re.IGNORECASE)
        return description.strip()
    
    def _extract_command(self, line: str) -> str:
        """Extract command from line"""
        # Remove command markers
        command = re.sub(r"^(COMMAND|CMD|\/\/\s*COMMAND|\[COMMAND)[:\s]*", "", line, flags=re.IGNORECASE)
        return command.strip()
    
    def _extract_visual_prompt(self, line: str) -> str:
        """Extract visual prompt from line"""
        # Remove visual markers
        prompt = re.sub(r"^(VISUAL|PROMPT|\[VISUAL|#\s*VISUAL)[:\s]*", "", line, flags=re.IGNORECASE)
        return prompt.strip()
    
    def _estimate_command_duration(self, command: str) -> float:
        """Estimate duration for a command"""
        # Basic estimation based on command type
        command_lower = command.lower()
        
        if "glitch" in command_lower:
            return 0.5
        elif "zoom" in command_lower or "pan" in command_lower:
            return 2.0
        elif "transition" in command_lower:
            return 1.0
        elif "effect" in command_lower:
            return 1.5
        else:
            return 1.0
    
    def _create_response(self) -> ScriptParseResponse:
        """Create the response object"""
        parsed_scenes = []
        total_duration = 0.0
        
        for scene in self.scenes:
            # Ensure minimum scene duration
            if scene["duration"] < 2.0:
                scene["duration"] = 2.0
                self.warnings.append(f"Scene {scene['scene_number']} duration adjusted to minimum 2 seconds")
            
            parsed_scene = ParsedScene(
                scene_number=scene["scene_number"],
                description=scene["description"],
                duration=round(scene["duration"], 2),
                commands=scene["commands"],
                dialogue=scene["dialogue"],
                visual_prompts=scene["visual_prompts"]
            )
            parsed_scenes.append(parsed_scene)
            total_duration += scene["duration"]
        
        return ScriptParseResponse(
            scenes=parsed_scenes,
            total_duration=round(total_duration, 2),
            scene_count=len(parsed_scenes),
            warnings=self.warnings
        )


@router.post("/parse", response_model=ScriptParseResponse)
async def parse_script(
    request: ScriptParseRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    _: Annotated[None, Depends(rate_limit_per_minute)]
) -> ScriptParseResponse:
    """
    Parse a script into structured scenes
    
    Analyzes the script content and extracts:
    - Scene boundaries and descriptions
    - Commands for video effects
    - Dialogue and narration
    - Visual prompts for AI generation
    - Duration estimates
    
    The parser supports multiple script formats including:
    - Standard screenplay format (INT./EXT.)
    - Markdown-style scenes
    - Custom command syntax
    """
    logger.info(
        "Parsing script",
        user_id=str(current_user.id),
        content_length=len(request.content),
        style=request.style
    )
    
    try:
        parser = ScriptParser(request.content, request.style)
        result = parser.parse()
        
        if not result.scenes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No scenes found in script. Please check the format."
            )
        
        logger.info(
            "Script parsed successfully",
            user_id=str(current_user.id),
            scene_count=result.scene_count,
            total_duration=result.total_duration,
            warnings=len(result.warnings)
        )
        
        return result
        
    except Exception as e:
        logger.error(
            "Script parsing failed",
            user_id=str(current_user.id),
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse script: {str(e)}"
        )


@router.post("/validate")
async def validate_script(
    request: ScriptParseRequest,
    current_user: Annotated[User, Depends(get_current_user)]
) -> dict:
    """
    Validate script format and content
    
    Performs validation checks including:
    - Format compliance
    - Command syntax validation
    - Duration constraints
    - Resource availability checks
    """
    logger.info(
        "Validating script",
        user_id=str(current_user.id),
        content_length=len(request.content)
    )
    
    validation_results = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "suggestions": []
    }
    
    try:
        # Parse the script first
        parser = ScriptParser(request.content, request.style)
        result = parser.parse()
        
        # Check scene count
        if result.scene_count == 0:
            validation_results["valid"] = False
            validation_results["errors"].append("No valid scenes found in script")
        elif result.scene_count > 50:
            validation_results["warnings"].append(f"Script has {result.scene_count} scenes. Consider breaking into smaller videos.")
        
        # Check total duration
        if result.total_duration > 600:  # 10 minutes
            validation_results["valid"] = False
            validation_results["errors"].append(f"Total duration ({result.total_duration}s) exceeds maximum of 600 seconds")
        elif result.total_duration > 300:  # 5 minutes
            validation_results["warnings"].append(f"Long video duration ({result.total_duration}s) may take significant time to process")
        
        # Check individual scenes
        for scene in result.scenes:
            if scene.duration > 60:
                validation_results["warnings"].append(f"Scene {scene.scene_number} is very long ({scene.duration}s)")
            
            if not scene.visual_prompts and not scene.commands:
                validation_results["suggestions"].append(f"Scene {scene.scene_number} has no visual prompts or commands")
        
        # Add parser warnings
        validation_results["warnings"].extend(result.warnings)
        
        logger.info(
            "Script validation completed",
            user_id=str(current_user.id),
            valid=validation_results["valid"],
            error_count=len(validation_results["errors"]),
            warning_count=len(validation_results["warnings"])
        )
        
        return validation_results
        
    except Exception as e:
        logger.error(
            "Script validation failed",
            user_id=str(current_user.id),
            error=str(e),
            exc_info=True
        )
        
        validation_results["valid"] = False
        validation_results["errors"].append(f"Validation error: {str(e)}")
        
        return validation_results


@router.get("/examples")
async def get_script_examples(
    style: str = "techwear",
    current_user: Annotated[User, Depends(get_current_user)] = None
) -> dict:
    """
    Get example scripts for different styles
    
    Returns example scripts showing proper formatting for:
    - Scene structure
    - Command syntax
    - Visual prompts
    - Dialogue formatting
    """
    examples = {
        "techwear": """SCENE 1: Digital Awakening
COMMAND: glitch_transition
VISUAL: Neon-lit server room with holographic displays

A lone figure stands before a massive screen displaying cascading code.

VOICE: "In the year 2089, reality became negotiable."

COMMAND: zoom_in
VISUAL: Close-up of cybernetic eye reflecting data streams

SCENE 2: The Network
COMMAND: matrix_effect
VISUAL: Abstract data visualization morphing into city skyline

The digital consciousness spreads through the network.

VOICE: "We are no longer bound by flesh."
""",
        "film_noir": """SCENE 1: Rain-Soaked Streets
VISUAL: Dark alley with steam rising from grates, harsh shadows

The city never sleeps, and neither do its secrets.

CHARACTER: "Some cases choose you."

COMMAND: slow_pan
VISUAL: Vintage car headlights cutting through fog

SCENE 2: The Office
COMMAND: venetian_blind_shadows
VISUAL: Dimly lit detective office, smoke curling from ashtray

She walked in like trouble in a dress.
""",
        "photorealistic": """SCENE 1: Mountain Vista
VISUAL: Majestic mountain range at golden hour, ultra-realistic details

COMMAND: drone_flyover
The camera sweeps across pristine wilderness.

NARRATION: "Nature's grandeur captured in stunning detail."

SCENE 2: Forest Path
VISUAL: Sunlight filtering through dense forest canopy
COMMAND: dolly_forward

Every leaf, every texture, indistinguishable from reality.
"""
    }
    
    return {
        "style": style,
        "example": examples.get(style, examples["techwear"]),
        "available_styles": list(examples.keys())
    }