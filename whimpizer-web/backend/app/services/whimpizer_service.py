"""
Whimpizer Service - Wraps the existing pipeline for web API use
"""
import os
import sys
import subprocess
import asyncio
from pathlib import Path
from typing import List
import tempfile

from app.models.jobs import JobConfig, JobStatus
from app.services.job_manager import JobManager
from app.core.config import settings

class WhimpizerService:
    """Service that wraps the existing whimpizer pipeline for web use"""
    
    def __init__(self):
        self.job_manager = JobManager()
        
        # Paths to original whimpizer components
        self.src_path = Path(settings.WHIMPIZER_SRC_PATH)
        self.resources_path = Path(settings.WHIMPIZER_RESOURCES_PATH)
        self.config_path = Path(settings.WHIMPIZER_CONFIG_PATH)
    
    async def process_job(self, job_id: str, urls: List[str], config: JobConfig):
        """Process a complete whimpizer job in the background"""
        try:
            # Update status to downloading
            await self.job_manager.update_job_status(
                job_id, JobStatus.DOWNLOADING, "Starting download...", 10
            )
            
            # Step 1: Download content
            download_success = await self._download_content(job_id, urls)
            if not download_success:
                await self.job_manager.update_job_status(
                    job_id, JobStatus.FAILED, "Failed to download content", 
                    error_message="Download step failed"
                )
                return
                
            await self.job_manager.update_job_status(
                job_id, JobStatus.PROCESSING, "Processing with AI...", 40
            )
            
            # Step 2: AI Processing (Whimperize)
            processing_success = await self._whimperize_content(job_id, config)
            if not processing_success:
                await self.job_manager.update_job_status(
                    job_id, JobStatus.FAILED, "Failed to process content with AI",
                    error_message="AI processing step failed"
                )
                return
                
            await self.job_manager.update_job_status(
                job_id, JobStatus.GENERATING_PDF, "Generating PDF...", 70
            )
            
            # Step 3: Generate PDF
            pdf_success = await self._generate_pdf(job_id, config)
            if not pdf_success:
                await self.job_manager.update_job_status(
                    job_id, JobStatus.FAILED, "Failed to generate PDF",
                    error_message="PDF generation step failed"
                )
                return
            
            # Success!
            await self.job_manager.update_job_status(
                job_id, JobStatus.COMPLETED, "Job completed successfully!", 100
            )
            
        except Exception as e:
            await self.job_manager.update_job_status(
                job_id, JobStatus.FAILED, f"Unexpected error: {str(e)}",
                error_message=str(e)
            )
    
    async def _download_content(self, job_id: str, urls: List[str]) -> bool:
        """Download content using the existing bulk downloader"""
        try:
            # Create URLs file for the job
            urls_file = f"uploads/{job_id}_urls.txt"
            os.makedirs("uploads", exist_ok=True)
            
            with open(urls_file, 'w') as f:
                for url in urls:
                    f.write(f"{url}\n")
            
            # Create output directory for this job
            download_dir = f"uploads/{job_id}_downloaded"
            os.makedirs(download_dir, exist_ok=True)
            
            # Run bulk downloader
            cmd = [
                sys.executable,
                str(self.src_path / "bulk_downloader.py"),
                "--input", urls_file,
                "--output-dir", download_dir
            ]
            
            # Run the command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                print(f"Download failed: {stderr.decode()}")
                return False
                
            return True
            
        except Exception as e:
            print(f"Error in download step: {e}")
            return False
    
    async def _whimperize_content(self, job_id: str, config: JobConfig) -> bool:
        """Process content with AI using the existing whimperizer"""
        try:
            download_dir = f"uploads/{job_id}_downloaded"
            output_dir = f"uploads/{job_id}_whimperized"
            os.makedirs(output_dir, exist_ok=True)
            
            # Create temporary config file with job-specific settings
            temp_config = await self._create_temp_config(config)
            
            # Run whimperizer
            cmd = [
                sys.executable,
                str(self.src_path / "whimperizer.py"),
                "--config", temp_config,
                "--input-dir", download_dir,
                "--output-dir", output_dir,
                "--provider", config.ai_provider,
                "--verbose"
            ]
            
            # Run the command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, "AI_PROVIDER": config.ai_provider}
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                print(f"Whimperization failed: {stderr.decode()}")
                return False
                
            return True
            
        except Exception as e:
            print(f"Error in whimperization step: {e}")
            return False
    
    async def _generate_pdf(self, job_id: str, config: JobConfig) -> bool:
        """Generate PDF using the existing PDF generator"""
        try:
            whimper_dir = f"uploads/{job_id}_whimperized"
            output_pdf = f"outputs/{job_id}.pdf"
            os.makedirs("outputs", exist_ok=True)
            
            # Find the whimperized markdown file
            whimper_files = list(Path(whimper_dir).glob("*.md"))
            if not whimper_files:
                print("No whimperized content found")
                return False
            
            # Use the first (or combined) markdown file
            input_file = whimper_files[0]
            
            # Run PDF generator
            cmd = [
                sys.executable,
                str(self.src_path / "wimpy_pdf_generator.py"),
                "--input", str(input_file),
                "--output", output_pdf,
                "--style", config.pdf_style,
                "--resources", str(self.resources_path)
            ]
            
            # Run the command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                print(f"PDF generation failed: {stderr.decode()}")
                return False
                
            return True
            
        except Exception as e:
            print(f"Error in PDF generation step: {e}")
            return False
    
    async def _create_temp_config(self, config: JobConfig) -> str:
        """Create a temporary config file for this job"""
        try:
            # Read the base config
            import yaml
            with open(self.config_path, 'r') as f:
                base_config = yaml.safe_load(f)
            
            # Override with job-specific settings
            base_config['api']['default_provider'] = config.ai_provider
            base_config['api']['providers'][config.ai_provider]['model'] = config.ai_model
            base_config['api']['providers'][config.ai_provider]['temperature'] = config.temperature
            base_config['options']['combine_by_group'] = config.combine_by_group
            
            # Write temporary config
            temp_config_path = f"uploads/{job_id}_config.yaml"
            with open(temp_config_path, 'w') as f:
                yaml.dump(base_config, f)
                
            return temp_config_path
            
        except Exception as e:
            print(f"Error creating temp config: {e}")
            # Fall back to original config
            return str(self.config_path)