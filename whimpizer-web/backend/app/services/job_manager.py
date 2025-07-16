"""
Job Manager Service - Handles job persistence and lifecycle management
"""
import json
import os
import redis
from typing import List, Optional, Tuple
from datetime import datetime

from app.models.jobs import JobInfo, JobStatus
from app.core.config import settings

class JobManager:
    """Manages job storage and retrieval using Redis"""
    
    def __init__(self):
        # Connect to Redis
        self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.job_prefix = "whimpizer:job:"
        self.job_list_key = "whimpizer:jobs"
        
    async def create_job(self, job_info: JobInfo) -> bool:
        """Create a new job record"""
        try:
            # Store job data in Redis hash
            job_key = f"{self.job_prefix}{job_info.id}"
            job_data = job_info.dict()
            
            # Convert datetime objects to ISO strings for Redis storage
            for field in ['created_at', 'started_at', 'completed_at']:
                if job_data.get(field):
                    job_data[field] = job_data[field].isoformat()
            
            # Store as JSON string
            self.redis_client.set(job_key, json.dumps(job_data))
            
            # Add to job list with timestamp
            self.redis_client.zadd(
                self.job_list_key, 
                {job_info.id: datetime.utcnow().timestamp()}
            )
            
            return True
            
        except Exception as e:
            print(f"Error creating job: {e}")
            return False
    
    async def get_job(self, job_id: str) -> Optional[JobInfo]:
        """Retrieve a job by ID"""
        try:
            job_key = f"{self.job_prefix}{job_id}"
            job_data = self.redis_client.get(job_key)
            
            if not job_data:
                return None
                
            # Parse JSON and convert back to JobInfo
            data = json.loads(job_data)
            
            # Convert ISO strings back to datetime objects
            for field in ['created_at', 'started_at', 'completed_at']:
                if data.get(field):
                    data[field] = datetime.fromisoformat(data[field])
            
            return JobInfo(**data)
            
        except Exception as e:
            print(f"Error getting job {job_id}: {e}")
            return None
    
    async def update_job_status(
        self, 
        job_id: str, 
        status: JobStatus, 
        message: str, 
        progress: int = None,
        error_message: str = None
    ) -> bool:
        """Update job status and progress"""
        try:
            job_info = await self.get_job(job_id)
            if not job_info:
                return False
            
            # Update fields
            job_info.status = status
            job_info.message = message
            
            if progress is not None:
                job_info.progress = progress
                
            if error_message:
                job_info.error_message = error_message
            
            # Set timestamps based on status
            now = datetime.utcnow()
            if status == JobStatus.DOWNLOADING and not job_info.started_at:
                job_info.started_at = now
            elif status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                job_info.completed_at = now
                if status == JobStatus.COMPLETED:
                    job_info.download_url = f"/api/jobs/{job_id}/download"
            
            # Save updated job
            return await self.create_job(job_info)
            
        except Exception as e:
            print(f"Error updating job status: {e}")
            return False
    
    async def list_jobs(
        self, 
        page: int = 1, 
        size: int = 10, 
        status: Optional[JobStatus] = None,
        user_id: Optional[str] = None
    ) -> Tuple[List[JobInfo], int]:
        """List jobs with pagination and optional status filter"""
        try:
            # Get all job IDs ordered by timestamp (newest first)
            start = (page - 1) * size
            end = start + size - 1
            
            job_ids = self.redis_client.zrevrange(self.job_list_key, start, end)
            
            jobs = []
            for job_id in job_ids:
                job_info = await self.get_job(job_id)
                if job_info and (not status or job_info.status == status):
                    # Filter by user if specified
                    if user_id and job_info.user_id != user_id:
                        continue
                    jobs.append(job_info)
            
            # Get total count
            total = self.redis_client.zcard(self.job_list_key)
            
            return jobs, total
            
        except Exception as e:
            print(f"Error listing jobs: {e}")
            return [], 0
    
    async def cleanup_job_files(self, job_id: str) -> bool:
        """Clean up files associated with a job"""
        try:
            # Remove output files
            output_files = [
                f"outputs/{job_id}.pdf",
                f"uploads/{job_id}_urls.txt"
            ]
            
            for file_path in output_files:
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            return True
            
        except Exception as e:
            print(f"Error cleaning up job files: {e}")
            return False
    
    async def delete_job(self, job_id: str) -> bool:
        """Completely delete a job and its files"""
        try:
            # Clean up files first
            await self.cleanup_job_files(job_id)
            
            # Remove from Redis
            job_key = f"{self.job_prefix}{job_id}"
            self.redis_client.delete(job_key)
            self.redis_client.zrem(self.job_list_key, job_id)
            
            return True
            
        except Exception as e:
            print(f"Error deleting job: {e}")
            return False