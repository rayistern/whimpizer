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
import requests
from urllib.parse import urljoin, urlparse
import logging

from app.models.jobs import JobConfig, JobStatus
from app.services.job_manager import JobManager
from app.services.ai_service import AIService
from app.core.config import settings

logger = logging.getLogger(__name__)

class WhimpizerService:
    """Service that wraps the existing whimpizer pipeline for web use"""
    
    def __init__(self):
        self.job_manager = JobManager()
        self.ai_service = AIService()
        
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
        """Download content directly using requests"""
        try:
            # Create output directory for this job
            download_dir = f"uploads/{job_id}_downloaded"
            os.makedirs(download_dir, exist_ok=True)
            
            downloaded_content = []
            
            for i, url in enumerate(urls):
                try:
                    # Download the web page
                    response = requests.get(url, timeout=30, headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    })
                    response.raise_for_status()
                    
                    # Simple content extraction (could be enhanced with BeautifulSoup)
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Remove script and style elements
                    for script in soup(["script", "style"]):
                        script.extract()
                    
                    # Get text content
                    text = soup.get_text()
                    
                    # Clean up text
                    lines = (line.strip() for line in text.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    text = '\n'.join(chunk for chunk in chunks if chunk)
                    
                    # Save to file
                    filename = f"{job_id}-{i+1}-{urlparse(url).netloc}.txt"
                    filepath = os.path.join(download_dir, filename)
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(f"Source: {url}\n\n{text}")
                    
                    downloaded_content.append({
                        'url': url,
                        'content': text,
                        'file': filepath
                    })
                    
                    logger.info(f"Downloaded content from {url}")
                    
                except Exception as e:
                    logger.error(f"Failed to download {url}: {str(e)}")
                    continue
            
            if not downloaded_content:
                logger.error("No content was successfully downloaded")
                return False
            
            # Store content info for next step
            import json
            with open(f"uploads/{job_id}_content_info.json", 'w') as f:
                json.dump(downloaded_content, f)
                
            return True
            
        except Exception as e:
            logger.error(f"Error in download step: {e}")
            return False
    
    async def _whimperize_content(self, job_id: str, config: JobConfig) -> bool:
        """Process content with AI using the AIService"""
        try:
            # Load downloaded content
            import json
            content_info_file = f"uploads/{job_id}_content_info.json"
            
            if not os.path.exists(content_info_file):
                logger.error("No content info found for whimperization")
                return False
            
            with open(content_info_file, 'r') as f:
                downloaded_content = json.load(f)
            
            # Create output directory
            output_dir = f"uploads/{job_id}_whimperized"
            os.makedirs(output_dir, exist_ok=True)
            
            # Combine all content if requested
            if config.combine_by_group:
                if config.include_source_urls:
                    combined_content = "\n\n---\n\n".join([
                        f"Source: {item['url']}\n\n{item['content']}"
                        for item in downloaded_content
                    ])
                else:
                    combined_content = "\n\n---\n\n".join([
                        item['content'] for item in downloaded_content
                    ])
                
                # Process with AI
                whimperized_content = await self.ai_service.whimperize_content(
                    combined_content, config
                )
                
                # Save whimperized content
                output_file = os.path.join(output_dir, f"{job_id}_whimperized.md")
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(whimperized_content)
                
                logger.info(f"Generated combined whimperized content: {output_file}")
                
            else:
                # Process each piece separately
                for i, item in enumerate(downloaded_content):
                    whimperized_content = await self.ai_service.whimperize_content(
                        item['content'], config
                    )
                    
                    # Save individual whimperized content
                    output_file = os.path.join(output_dir, f"{job_id}_part_{i+1}_whimperized.md")
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(whimperized_content)
                    
                    logger.info(f"Generated whimperized content part {i+1}: {output_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error in whimperization step: {e}")
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
                logger.error("No whimperized content found for PDF generation")
                return False
            
            # Use the first (or combined) markdown file
            input_file = whimper_files[0]
            
            # Check if the original PDF generator exists
            pdf_generator_path = self.src_path / "wimpy_pdf_generator.py"
            
            if pdf_generator_path.exists():
                # Use original PDF generator
                cmd = [
                    sys.executable,
                    str(pdf_generator_path),
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
                    logger.error(f"PDF generation failed: {stderr.decode()}")
                    return False
            else:
                # Fallback: Create a simple PDF
                logger.warning("Original PDF generator not found, using simple fallback")
                await self._create_simple_pdf(input_file, output_pdf)
                
            return True
            
        except Exception as e:
            logger.error(f"Error in PDF generation step: {e}")
            return False
    
    async def _create_simple_pdf(self, input_file: Path, output_pdf: str):
        """Create a simple PDF as fallback"""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import inch
            
            # Read markdown content
            with open(input_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Create PDF
            doc = SimpleDocTemplate(output_pdf, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            # Split content into paragraphs
            paragraphs = content.split('\n\n')
            
            for para in paragraphs:
                if para.strip():
                    # Remove markdown formatting for simple PDF
                    clean_para = para.replace('**', '').replace('*', '').replace('#', '')
                    if clean_para.strip():
                        story.append(Paragraph(clean_para, styles['Normal']))
                        story.append(Spacer(1, 0.2 * inch))
            
            doc.build(story)
            logger.info(f"Created simple PDF: {output_pdf}")
            
        except Exception as e:
            logger.error(f"Failed to create simple PDF: {e}")
            raise
    
