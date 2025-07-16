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
    ENVIRONMENT: str = "development"  # development, staging, production
    
    # CORS settings - more flexible for deployment
    ALLOWED_HOSTS: List[str] = [
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "https://*.netlify.app",  # Netlify deployments
        "https://*.vercel.app"    # Vercel deployments (alternative)
    ]
    
    # Redis settings for job queue
    REDIS_URL: str = "redis://localhost:6379"
    
    # AI Provider settings (Portkey configuration)
    AI_BASE_URL: str = "https://api.portkey.ai/v1"  # Portkey gateway
    AI_API_KEY: str = ""  # Portkey API key
    AI_DEFAULT_PROVIDER: str = "openai"
    AI_DEFAULT_MODEL: str = "gpt-4"
    
    # Portkey specific settings
    PORTKEY_APP_ID: str = ""  # Optional: Portkey app ID for analytics
    PORTKEY_TRACE_ID_PREFIX: str = "whimpizer"
    
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
    
    # Database (Supabase for production)
    DATABASE_URL: str = ""  # Will use Redis for now, Supabase later if needed
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    def get_cors_origins(self) -> List[str]:
        """Get CORS origins based on environment"""
        if self.ENVIRONMENT == "production":
            # In production, be more restrictive
            return [origin for origin in self.ALLOWED_HOSTS if origin.startswith("https://")]
        else:
            # In development, allow localhost
            return self.ALLOWED_HOSTS

# Create global settings instance
settings = Settings()