"""
Jobs API endpoints for Whimpizer Web
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from fastapi.responses import FileResponse
from typing import Optional
import uuid
import os
from datetime import datetime

from app.models.jobs import (
    JobSubmissionRequest, JobResponse, JobInfo, JobListResponse, 
    JobStatus, JobConfig
)
from app.services.job_manager import JobManager
from app.services.whimpizer_service import WhimpizerService

router = APIRouter()
job_manager = JobManager()
whimpizer_service = WhimpizerService()

@router.post("/", response_model=JobResponse)
async def submit_job(
    request: JobSubmissionRequest,
    background_tasks: BackgroundTasks
):
    """Submit a new whimpizer job"""
    try:
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Create job record
        job_info = JobInfo(
            id=job_id,
            status=JobStatus.PENDING,
            progress=0,
            message="Job submitted successfully",
            config=request.config,
            urls=[str(url) for url in request.urls],
            created_at=datetime.utcnow()
        )
        
        # Store job info
        await job_manager.create_job(job_info)
        
        # Start background processing
        background_tasks.add_task(
            whimpizer_service.process_job,
            job_id,
            [str(url) for url in request.urls],
            request.config
        )
        
        return JobResponse(
            job_id=job_id,
            status=JobStatus.PENDING,
            message="Job submitted successfully",
            status_url=f"/api/jobs/{job_id}/status"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit job: {str(e)}")

@router.get("/{job_id}/status", response_model=JobInfo)
async def get_job_status(job_id: str):
    """Get the status of a specific job"""
    try:
        job_info = await job_manager.get_job(job_id)
        if not job_info:
            raise HTTPException(status_code=404, detail="Job not found")
        return job_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")

@router.get("/", response_model=JobListResponse)
async def list_jobs(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    status: Optional[JobStatus] = None
):
    """List jobs with pagination"""
    try:
        jobs, total = await job_manager.list_jobs(page=page, size=size, status=status)
        return JobListResponse(
            jobs=jobs,
            total=total,
            page=page,
            size=size
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list jobs: {str(e)}")

@router.get("/{job_id}/download")
async def download_pdf(job_id: str):
    """Download the generated PDF for a completed job"""
    try:
        job_info = await job_manager.get_job(job_id)
        if not job_info:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job_info.status != JobStatus.COMPLETED:
            raise HTTPException(status_code=400, detail="Job not completed yet")
        
        if not job_info.download_url:
            raise HTTPException(status_code=404, detail="Download file not found")
        
        # Construct file path
        file_path = os.path.join("outputs", f"{job_id}.pdf")
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Download file not found")
        
        return FileResponse(
            path=file_path,
            filename=f"whimpizer-{job_id}.pdf",
            media_type="application/pdf"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download file: {str(e)}")

@router.delete("/{job_id}")
async def cancel_job(job_id: str):
    """Cancel a running job or delete a completed job"""
    try:
        job_info = await job_manager.get_job(job_id)
        if not job_info:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Update job status to cancelled
        await job_manager.update_job_status(
            job_id, 
            JobStatus.CANCELLED, 
            "Job cancelled by user"
        )
        
        # Clean up files if they exist
        await job_manager.cleanup_job_files(job_id)
        
        return {"message": "Job cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel job: {str(e)}")