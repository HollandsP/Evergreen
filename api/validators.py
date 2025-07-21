"""
Pydantic models for request/response validation
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator, EmailStr, ConfigDict
from uuid import UUID


# Enums
class ProjectStatus(str, Enum):
    """Project status enumeration"""
    DRAFT = "draft"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class VideoStyle(str, Enum):
    """Video style enumeration"""
    TECHWEAR = "techwear"
    PHOTOREALISTIC = "photorealistic"
    FILM_NOIR = "film_noir"
    ANIME = "anime"
    CUSTOM = "custom"


class VoiceType(str, Enum):
    """Voice type enumeration"""
    MALE_CALM = "male_calm"
    FEMALE_CALM = "female_calm"
    MALE_DRAMATIC = "male_dramatic"
    FEMALE_DRAMATIC = "female_dramatic"
    CUSTOM = "custom"


class GenerationStatus(str, Enum):
    """Generation job status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobStatus(str, Enum):
    """Job status enumeration"""
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Base Models
class BaseRequest(BaseModel):
    """Base request model"""
    model_config = ConfigDict(
        use_enum_values=True,
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )


class BaseResponse(BaseModel):
    """Base response model"""
    model_config = ConfigDict(
        use_enum_values=True,
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }
    )


# Auth Models
class UserCreate(BaseRequest):
    """User registration request"""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: str = Field(..., min_length=1, max_length=100)


class UserLogin(BaseRequest):
    """User login request"""
    username: EmailStr
    password: str


class Token(BaseResponse):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data"""
    username: Optional[str] = None


class UserResponse(BaseResponse):
    """User response model"""
    id: UUID
    email: EmailStr
    full_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


# Project Models
class ProjectCreate(BaseRequest):
    """Create project request"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    script_content: str = Field(..., min_length=10)
    style: VideoStyle = VideoStyle.TECHWEAR
    voice_type: VoiceType = VoiceType.MALE_CALM
    
    @field_validator("script_content")
    @classmethod
    def validate_script_content(cls, v):
        """Validate script has some content"""
        if not v.strip():
            raise ValueError("Script content cannot be empty")
        return v


class ProjectUpdate(BaseRequest):
    """Update project request"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    script_content: Optional[str] = Field(None, min_length=10)
    style: Optional[VideoStyle] = None
    voice_type: Optional[VoiceType] = None


class ProjectResponse(BaseResponse):
    """Project response model"""
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str]
    script_content: str
    style: VideoStyle
    voice_type: VoiceType
    status: ProjectStatus
    video_url: Optional[str]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class ProjectListResponse(BaseResponse):
    """Project list response"""
    items: List[ProjectResponse]
    total: int
    skip: int
    limit: int


# Script Models
class ScriptParseRequest(BaseRequest):
    """Script parsing request"""
    content: str = Field(..., min_length=10)
    style: Optional[VideoStyle] = VideoStyle.TECHWEAR
    
    @field_validator("content")
    @classmethod
    def validate_content(cls, v):
        """Validate script content"""
        if not v.strip():
            raise ValueError("Script content cannot be empty")
        # Check for basic structure
        if "SCENE" not in v.upper() and "COMMAND" not in v.upper():
            raise ValueError("Script must contain SCENE or COMMAND directives")
        return v


class ParsedScene(BaseModel):
    """Parsed scene information"""
    scene_number: int
    description: str
    duration: float
    commands: List[str]
    dialogue: Optional[str]
    visual_prompts: List[str]


class ScriptParseResponse(BaseResponse):
    """Script parsing response"""
    scenes: List[ParsedScene]
    total_duration: float
    scene_count: int
    warnings: List[str] = []


# Generation Models
class GenerationRequest(BaseRequest):
    """Video generation request"""
    project_id: UUID
    quality: str = Field(default="high", pattern="^(low|medium|high|ultra)$")
    priority: int = Field(default=5, ge=1, le=10)
    webhook_url: Optional[str] = None
    
    @field_validator("webhook_url")
    @classmethod
    def validate_webhook_url(cls, v):
        """Validate webhook URL if provided"""
        if v and not v.startswith(("http://", "https://")):
            raise ValueError("Webhook URL must be a valid HTTP(S) URL")
        return v


class GenerationResponse(BaseResponse):
    """Generation job response"""
    job_id: UUID
    project_id: UUID
    status: GenerationStatus
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    message: Optional[str]
    estimated_completion: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class GenerationProgressResponse(BaseResponse):
    """Generation progress response"""
    job_id: UUID
    status: GenerationStatus
    progress: float
    current_step: Optional[str]
    steps_completed: int
    total_steps: int
    messages: List[str]
    video_url: Optional[str]
    error: Optional[str]


# Health Check Models
class HealthCheckResponse(BaseResponse):
    """Health check response"""
    status: str
    service: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class DetailedHealthCheckResponse(HealthCheckResponse):
    """Detailed health check response"""
    checks: Dict[str, str]
    
    
class ReadinessResponse(BaseResponse):
    """Readiness probe response"""
    ready: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class LivenessResponse(BaseResponse):
    """Liveness probe response"""
    alive: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Error Models
class ErrorDetail(BaseModel):
    """Error detail model"""
    loc: Optional[List[str]]
    msg: str
    type: str


class ErrorResponse(BaseResponse):
    """Error response model"""
    detail: str
    status_code: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    errors: Optional[List[ErrorDetail]] = None


# Pagination Models
class PaginationParams(BaseModel):
    """Pagination parameters"""
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)