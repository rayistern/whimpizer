"""
Pydantic models for job management
"""
from pydantic import BaseModel, HttpUrl, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class JobStatus(str, Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    GENERATING_PDF = "generating_pdf"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class AIProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"

class JobConfig(BaseModel):
    """Configuration for a whimpizer job"""
    ai_provider: AIProvider = AIProvider.OPENAI
    ai_model: str = "gpt-4"
    pdf_style: str = "handwritten"
    combine_by_group: bool = True
    temperature: float = 0.7
    
class JobSubmissionRequest(BaseModel):
    """Request model for submitting a new job"""
    urls: List[HttpUrl]
    config: Optional[JobConfig] = JobConfig()
    
    @validator('urls')
    def validate_urls(cls, v):
        if not v:
            raise ValueError('At least one URL must be provided')
        if len(v) > 20:
            raise ValueError('Maximum 20 URLs allowed')
        return v

class JobResponse(BaseModel):
    """Response model when a job is created"""
    job_id: str
    status: JobStatus
    message: str
    status_url: str

class JobInfo(BaseModel):
    """Detailed job information"""
    id: str
    status: JobStatus
    progress: int  # 0-100
    message: str
    config: JobConfig
    urls: List[str]
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    download_url: Optional[str] = None
    error_message: Optional[str] = None
    
class JobListResponse(BaseModel):
    """Response for listing jobs"""
    jobs: List[JobInfo]
    total: int
    page: int
    size: int

class ProviderInfo(BaseModel):
    """Information about available AI providers"""
    name: str
    display_name: str
    models: List[str]
    available: bool
    description: str