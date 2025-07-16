"""
Configuration settings for Whimpizer Web API
"""
from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # App settings
    APP_NAME: str = "Whimpizer API"
    DEBUG: bool = False
    ALLOWED_HOSTS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Redis settings for job queue
    REDIS_URL: str = "redis://localhost:6379"
    
    # AI Provider settings
    AI_BASE_URL: str = "https://api.portkey.ai/v1"  # Default to Portkey
    AI_API_KEY: str = ""
    AI_DEFAULT_PROVIDER: str = "openai"
    AI_DEFAULT_MODEL: str = "gpt-4"
    
    # File handling
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    UPLOAD_DIR: str = "uploads"
    OUTPUT_DIR: str = "outputs"
    
    # Job settings
    JOB_TIMEOUT: int = 3600  # 1 hour
    MAX_JOBS_PER_USER: int = 10
    
    # Original whimpizer settings (inherit from existing config)
    WHIMPIZER_CONFIG_PATH: str = "../../config/config.yaml"
    WHIMPIZER_SRC_PATH: str = "../../src"
    WHIMPIZER_RESOURCES_PATH: str = "../../resources"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create global settings instance
settings = Settings()