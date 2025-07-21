"""
Application configuration using Pydantic settings
"""
import os
from functools import lru_cache
from typing import Optional, List, Union

from pydantic_settings import BaseSettings
from pydantic import PostgresDsn, RedisDsn, field_validator


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application
    APP_NAME: str = "AI Content Generation Pipeline"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    TESTING: bool = False
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Database
    DATABASE_URL: PostgresDsn = "postgresql://pipeline:pipeline@localhost:5432/pipeline"
    
    # Redis
    REDIS_URL: RedisDsn = "redis://localhost:6379/0"
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    
    # AWS
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    S3_BUCKET: str = "content-pipeline-media"
    
    # AI Services
    ELEVENLABS_API_KEY: Optional[str] = None
    ELEVENLABS_RATE_LIMIT: int = 100  # requests per minute
    
    RUNWAY_API_KEY: Optional[str] = None
    RUNWAY_TIMEOUT: int = 300  # seconds
    
    OPENAI_API_KEY: Optional[str] = None
    
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    
    # Media Processing
    MAX_VIDEO_DURATION: int = 600  # 10 minutes
    DEFAULT_VIDEO_RESOLUTION: str = "1920x1080"
    DEFAULT_VIDEO_FPS: int = 30
    DEFAULT_AUDIO_SAMPLE_RATE: int = 44100
    
    # File Storage
    UPLOAD_DIR: str = "./output/uploads"
    TEMP_DIR: str = "./output/temp"
    EXPORT_DIR: str = "./output/exports"
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # Monitoring
    SENTRY_DSN: Optional[str] = None
    LOG_LEVEL: str = "INFO"
    
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Ensure DATABASE_URL is properly formatted"""
        if not v:
            raise ValueError("DATABASE_URL must be set")
        return v
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def validate_cors_origins(cls, v):
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True
    }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()