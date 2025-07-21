"""
Database models for AI Content Generation Pipeline
"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps"""
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class User(Base, TimestampMixin):
    """User model for authentication and authorization"""
    __tablename__ = "users"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    generation_jobs = relationship("GenerationJob", back_populates="user", cascade="all, delete-orphan")


class Project(Base, TimestampMixin):
    """Project model for video generation projects"""
    __tablename__ = "projects"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    script_content = Column(Text, nullable=False)
    style = Column(String(50), nullable=False, default="techwear")
    voice_type = Column(String(50), nullable=False, default="male_calm")
    series_id = Column(PGUUID(as_uuid=True), nullable=True)
    status = Column(
        Enum(
            "draft",
            "processing",
            "completed",
            "failed",
            name="project_status",
        ),
        default="draft",
        nullable=False,
    )
    video_url = Column(String(500), nullable=True)
    project_metadata = Column("metadata", JSON, default={})
    
    # Relationships
    user = relationship("User", back_populates="projects")
    scripts = relationship("Script", back_populates="project", cascade="all, delete-orphan")
    media_assets = relationship("MediaAsset", back_populates="project", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="project", cascade="all, delete-orphan")
    generation_jobs = relationship("GenerationJob", back_populates="project", cascade="all, delete-orphan")


class Script(Base, TimestampMixin):
    """Script model for storing parsed scripts"""
    __tablename__ = "scripts"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(PGUUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    content = Column(Text, nullable=False)
    parsed_data = Column(JSON, default={})
    project_metadata = Column("metadata", JSON, default={})
    processed_at = Column(DateTime, nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="scripts")
    segments = relationship("ScriptSegment", back_populates="script", cascade="all, delete-orphan")


class ScriptSegment(Base):
    """Individual script segments for processing"""
    __tablename__ = "script_segments"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    script_id = Column(PGUUID(as_uuid=True), ForeignKey("scripts.id"), nullable=False)
    sequence = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    speaker = Column(String(100), nullable=True)
    duration = Column(Float, nullable=False)
    timestamp = Column(Float, nullable=False)
    scene_description = Column(Text, nullable=True)
    
    # Relationships
    script = relationship("Script", back_populates="segments")


class MediaAsset(Base, TimestampMixin):
    """Media assets (audio, video, images) for projects"""
    __tablename__ = "media_assets"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(PGUUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    type = Column(
        Enum("audio", "video", "image", "overlay", name="media_type"),
        nullable=False,
    )
    file_path = Column(String(500), nullable=False)
    s3_key = Column(String(500), nullable=True)
    duration = Column(Float, nullable=True)
    resolution = Column(String(20), nullable=True)
    format = Column(String(20), nullable=True)
    size_bytes = Column(Integer, nullable=True)
    project_metadata = Column("metadata", JSON, default={})
    
    # Relationships
    project = relationship("Project", back_populates="media_assets")


class Job(Base, TimestampMixin):
    """Job tracking for async tasks"""
    __tablename__ = "jobs"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(PGUUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    type = Column(
        Enum(
            "script_parsing",
            "voice_synthesis",
            "video_generation",
            "media_assembly",
            "export",
            name="job_type",
        ),
        nullable=False,
    )
    status = Column(
        Enum(
            "pending",
            "queued",
            "processing",
            "completed",
            "failed",
            "cancelled",
            name="job_status",
        ),
        default="pending",
        nullable=False,
    )
    celery_task_id = Column(String(255), nullable=True)
    progress = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    result = Column(JSON, default={})
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="jobs")


class VoiceProfile(Base, TimestampMixin):
    """Voice profiles for character voices"""
    __tablename__ = "voice_profiles"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(100), unique=True, nullable=False)
    provider = Column(
        Enum("elevenlabs", "google_tts", "azure", name="voice_provider"),
        default="elevenlabs",
        nullable=False,
    )
    voice_id = Column(String(255), nullable=False)
    settings = Column(JSON, default={})
    sample_audio_url = Column(String(500), nullable=True)
    is_active = Column(Integer, default=1)  # SQLite doesn't have boolean


class VisualTemplate(Base, TimestampMixin):
    """Visual templates for scene generation"""
    __tablename__ = "visual_templates"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(100), unique=True, nullable=False)
    category = Column(String(50), nullable=False)
    prompt_template = Column(Text, nullable=False)
    style_modifiers = Column(JSON, default=[])
    camera_settings = Column(JSON, default={})
    duration_seconds = Column(Float, default=5.0)
    is_active = Column(Integer, default=1)


class GenerationJob(Base, TimestampMixin):
    """Generation job tracking for video generation process"""
    __tablename__ = "generation_jobs"

    id = Column(String(255), primary_key=True)  # Using string ID for job tracking
    project_id = Column(PGUUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status = Column(
        Enum(
            "pending",
            "processing",
            "completed",
            "failed",
            name="generation_status",
        ),
        default="pending",
        nullable=False,
    )
    progress = Column(Float, default=0.0, nullable=False)
    current_step = Column(String(255), nullable=True)
    error = Column(Text, nullable=True)
    output_url = Column(String(500), nullable=True)
    project_metadata = Column("metadata", JSON, default={})
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="generation_jobs")
    user = relationship("User", back_populates="generation_jobs")


class AuditLog(Base):
    """Audit log for tracking all system actions"""
    __tablename__ = "audit_logs"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    user_id = Column(String(255), nullable=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(PGUUID(as_uuid=True), nullable=True)
    details = Column(JSON, default={})
    ip_address = Column(String(45), nullable=True)