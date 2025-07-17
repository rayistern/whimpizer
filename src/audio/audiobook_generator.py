"""
Audiobook Generator Module

High-level audiobook generation orchestrator that combines CSM generation,
voice management, and audio processing to create complete audiobooks from text content.
"""

import os
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import yaml
from datetime import datetime

from .csm_generator import CSMGenerator, AudioSegment
from .audio_processor import AudioProcessor
from .voice_manager import VoiceManager, DialogueSegment

logger = logging.getLogger(__name__)


class AudiobookGenerator:
    """
    High-level audiobook generation system
    
    Orchestrates the complete audiobook generation process from text input
    to final audio output, including voice assignment, audio generation,
    and post-processing.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Audiobook Generator
        
        Args:
            config: Configuration dictionary for audio generation
        """
        self.config = config
        self.audio_config = config.get('audio', {})
        
        # Initialize components
        self.csm_generator = None
        self.audio_processor = AudioProcessor(config)
        self.voice_manager = VoiceManager(config)
        
        # Generation settings
        self.output_dir = self.audio_config.get('paths', {}).get('output_dir', './output/audiobooks')
        self.temp_dir = self.audio_config.get('paths', {}).get('temp_dir', './output/audiobooks/temp')
        self.enabled = self.audio_config.get('enabled', True)
        
        # Performance settings
        self.streaming_enabled = self.audio_config.get('quality', {}).get('enable_streaming', True)
        self.batch_size = self.audio_config.get('quality', {}).get('batch_size', 1)
        
        # Create directories
        self._ensure_directories()
        
        logger.info(f"Initialized Audiobook Generator - Output: {self.output_dir}")
    
    def _ensure_directories(self) -> None:
        """Ensure required directories exist"""
        directories = [self.output_dir, self.temp_dir]
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def _initialize_csm_generator(self) -> None:
        """Initialize CSM generator if not already done"""
        if self.csm_generator is None:
            logger.info("Initializing CSM generator...")
            self.csm_generator = CSMGenerator(self.config)
            # Load model on first use to save memory
            self.csm_generator.load_model()
    
    def generate_audiobook(
        self,
        content: str,
        title: str,
        chapters: Optional[List[str]] = None,
        output_formats: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """
        Generate complete audiobook from text content
        
        Args:
            content: Text content to convert to audiobook
            title: Title of the audiobook
            chapters: Optional list of chapter texts (if None, content is treated as single chapter)
            output_formats: Output formats to generate (defaults to config)
            
        Returns:
            Dict mapping format to output file path
        """
        if not self.enabled:
            logger.warning("Audio generation is disabled")
            return {}
        
        try:
            start_time = time.time()
            logger.info(f"Starting audiobook generation for: {title}")
            
            # Initialize CSM generator
            self._initialize_csm_generator()
            
            # Process chapters
            if chapters is None:
                chapters = [content]
            
            # Generate audio for each chapter
            chapter_files = []
            total_chapters = len(chapters)
            
            for i, chapter_content in enumerate(chapters):
                logger.info(f"Processing chapter {i+1}/{total_chapters}")
                
                chapter_file = self._generate_chapter_audio(
                    chapter_content,
                    f"{title}_chapter_{i+1:02d}",
                    i
                )
                
                if chapter_file:
                    chapter_files.append(chapter_file)
                    logger.info(f"Completed chapter {i+1}/{total_chapters}")
                else:
                    logger.warning(f"Failed to generate chapter {i+1}")
            
            if not chapter_files:
                raise RuntimeError("No chapters were successfully generated")
            
            # Create final audiobook
            output_paths = self.audio_processor.create_audiobook_structure(
                chapter_files,
                self.output_dir,
                title,
                output_formats
            )
            
            # Generate metadata
            metadata = self._create_audiobook_metadata(
                title, chapters, chapter_files, output_paths, start_time
            )
            
            # Save metadata
            metadata_path = os.path.join(self.output_dir, f"{title}_metadata.yaml")
            self._save_metadata(metadata, metadata_path)
            
            # Cleanup temporary files
            self._cleanup_temp_files(chapter_files)
            
            generation_time = time.time() - start_time
            logger.info(f"Audiobook generation completed in {generation_time:.2f} seconds")
            
            return output_paths
            
        except Exception as e:
            logger.error(f"Audiobook generation failed: {str(e)}")
            raise RuntimeError(f"Audiobook generation failed: {str(e)}")
    
    def _generate_chapter_audio(
        self,
        chapter_content: str,
        chapter_name: str,
        chapter_index: int
    ) -> Optional[str]:
        """
        Generate audio for a single chapter
        
        Args:
            chapter_content: Text content of the chapter
            chapter_name: Name/identifier for the chapter
            chapter_index: Index of the chapter (for context)
            
        Returns:
            Optional[str]: Path to generated chapter audio file
        """
        try:
            # Assign voices to text segments
            voice_assignments = self.voice_manager.assign_voices_to_text(chapter_content)
            
            if not voice_assignments:
                logger.warning(f"No voice assignments found for chapter: {chapter_name}")
                return None
            
            # Generate audio segments
            segment_files = []
            context_segments = []
            
            for i, (text_segment, speaker_id, speaker_name) in enumerate(voice_assignments):
                if not text_segment.strip():
                    continue
                
                try:
                    # Generate audio for this segment
                    audio_tensor = self.csm_generator.generate_speech(
                        text_segment,
                        speaker_id,
                        context_segments[-3:] if context_segments else None  # Use last 3 for context
                    )
                    
                    # Save segment audio
                    segment_filename = f"{chapter_name}_segment_{i:04d}.wav"
                    segment_path = os.path.join(self.temp_dir, segment_filename)
                    
                    self.csm_generator.save_audio(audio_tensor, segment_path)
                    segment_files.append(segment_path)
                    
                    # Add to context for next generation
                    context_segment = AudioSegment(
                        text=text_segment,
                        speaker=speaker_id,
                        speaker_name=speaker_name,
                        audio=audio_tensor
                    )
                    context_segments.append(context_segment)
                    
                    logger.debug(f"Generated segment {i+1}/{len(voice_assignments)} for chapter {chapter_name}")
                    
                except Exception as e:
                    logger.error(f"Failed to generate segment {i+1} in chapter {chapter_name}: {str(e)}")
                    continue
            
            if not segment_files:
                logger.error(f"No segments were generated for chapter: {chapter_name}")
                return None
            
            # Concatenate segments into chapter audio
            chapter_filename = f"{chapter_name}.wav"
            chapter_path = os.path.join(self.temp_dir, chapter_filename)
            
            self.audio_processor.concatenate_audio_files(
                segment_files,
                chapter_path,
                add_silence=True
            )
            
            # Clean up segment files to save space
            for segment_file in segment_files:
                try:
                    os.remove(segment_file)
                except:
                    pass
            
            logger.info(f"Generated chapter audio: {chapter_path}")
            return chapter_path
            
        except Exception as e:
            logger.error(f"Chapter audio generation failed for {chapter_name}: {str(e)}")
            return None
    
    def _create_audiobook_metadata(
        self,
        title: str,
        chapters: List[str],
        chapter_files: List[str],
        output_paths: Dict[str, str],
        start_time: float
    ) -> Dict[str, Any]:
        """Create comprehensive metadata for the audiobook"""
        generation_time = time.time() - start_time
        
        metadata = {
            'audiobook': {
                'title': title,
                'generated_at': datetime.now().isoformat(),
                'generation_time_seconds': round(generation_time, 2),
                'total_chapters': len(chapters),
                'generator_version': '1.0.0'
            },
            'audio_settings': {
                'sample_rate': self.audio_processor.sample_rate,
                'channels': self.audio_processor.channels,
                'bit_depth': self.audio_processor.bit_depth,
            },
            'voice_settings': self.voice_manager.export_voice_mapping(),
            'output_files': {},
            'chapters': []
        }
        
        # Add output file information
        for format_name, file_path in output_paths.items():
            try:
                file_info = self.audio_processor.get_audio_info(file_path)
                metadata['output_files'][format_name] = file_info
            except:
                metadata['output_files'][format_name] = {'path': file_path, 'error': 'Could not read file info'}
        
        # Add chapter information
        for i, (chapter_content, chapter_file) in enumerate(zip(chapters, chapter_files)):
            chapter_info = {
                'index': i + 1,
                'word_count': len(chapter_content.split()),
                'character_count': len(chapter_content),
                'audio_file': os.path.basename(chapter_file) if chapter_file else None
            }
            
            # Add audio info if file exists
            if chapter_file and os.path.exists(chapter_file):
                try:
                    audio_info = self.audio_processor.get_audio_info(chapter_file)
                    chapter_info.update({
                        'duration_seconds': audio_info.get('duration_seconds'),
                        'file_size_mb': audio_info.get('file_size_mb')
                    })
                except:
                    pass
            
            metadata['chapters'].append(chapter_info)
        
        return metadata
    
    def _save_metadata(self, metadata: Dict[str, Any], metadata_path: str) -> None:
        """Save metadata to YAML file"""
        try:
            with open(metadata_path, 'w', encoding='utf-8') as f:
                yaml.dump(metadata, f, default_flow_style=False, allow_unicode=True)
            logger.debug(f"Metadata saved to: {metadata_path}")
        except Exception as e:
            logger.warning(f"Failed to save metadata: {str(e)}")
    
    def _cleanup_temp_files(self, chapter_files: List[str]) -> None:
        """Clean up temporary chapter files"""
        for chapter_file in chapter_files:
            try:
                if os.path.exists(chapter_file):
                    os.remove(chapter_file)
                    logger.debug(f"Cleaned up temp file: {chapter_file}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file {chapter_file}: {str(e)}")
    
    def generate_audio_preview(
        self,
        text: str,
        speaker_name: str = "narrator",
        max_length: int = 2000
    ) -> Optional[str]:
        """
        Generate a short audio preview for testing
        
        Args:
            text: Text to convert (will be truncated if too long)
            speaker_name: Voice to use for generation
            max_length: Maximum length of text in characters
            
        Returns:
            Optional[str]: Path to generated preview audio file
        """
        try:
            # Initialize CSM generator
            self._initialize_csm_generator()
            
            # Truncate text if necessary
            preview_text = text[:max_length] if len(text) > max_length else text
            
            # Get voice profile
            voice_profile = self.voice_manager.get_voice_for_character(speaker_name)
            speaker_id = voice_profile.speaker_id if voice_profile else 0
            
            # Generate audio
            audio_tensor = self.csm_generator.generate_speech(
                preview_text,
                speaker_id,
                max_length_ms=10000
            )
            
            # Save preview
            preview_filename = f"preview_{speaker_name}_{int(time.time())}.wav"
            preview_path = os.path.join(self.temp_dir, preview_filename)
            
            self.csm_generator.save_audio(audio_tensor, preview_path)
            
            logger.info(f"Generated audio preview: {preview_path}")
            return preview_path
            
        except Exception as e:
            logger.error(f"Preview generation failed: {str(e)}")
            return None
    
    def get_generation_status(self) -> Dict[str, Any]:
        """Get status information about the generator"""
        status = {
            'enabled': self.enabled,
            'csm_loaded': self.csm_generator is not None and self.csm_generator.is_loaded,
            'output_dir': self.output_dir,
            'temp_dir': self.temp_dir,
            'streaming_enabled': self.streaming_enabled,
            'voice_profiles': len(self.voice_manager.voice_profiles)
        }
        
        if self.csm_generator:
            status['model_info'] = self.csm_generator.get_model_info()
        
        status['voice_stats'] = self.voice_manager.get_voice_statistics()
        
        return status
    
    def estimate_generation_time(
        self,
        text_content: str,
        words_per_minute: int = 150
    ) -> Dict[str, float]:
        """
        Estimate audiobook generation time
        
        Args:
            text_content: Text content to analyze
            words_per_minute: Estimated reading speed
            
        Returns:
            Dict with time estimates
        """
        word_count = len(text_content.split())
        char_count = len(text_content)
        
        # Estimate audio duration based on reading speed
        estimated_audio_minutes = word_count / words_per_minute
        estimated_audio_seconds = estimated_audio_minutes * 60
        
        # Estimate generation time (rough approximation)
        # CSM is typically 10-20x slower than real-time on CPU
        generation_factor = 15  # Conservative estimate for CPU
        estimated_generation_seconds = estimated_audio_seconds * generation_factor
        
        return {
            'word_count': word_count,
            'character_count': char_count,
            'estimated_audio_duration_minutes': round(estimated_audio_minutes, 2),
            'estimated_audio_duration_seconds': round(estimated_audio_seconds, 2),
            'estimated_generation_time_minutes': round(estimated_generation_seconds / 60, 2),
            'estimated_generation_time_seconds': round(estimated_generation_seconds, 2)
        }
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate the current configuration"""
        validation = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'info': []
        }
        
        try:
            # Check directories
            if not os.path.exists(self.output_dir):
                validation['warnings'].append(f"Output directory does not exist: {self.output_dir}")
            
            # Check voice configuration
            voice_stats = self.voice_manager.get_voice_statistics()
            if voice_stats['total_voices'] == 0:
                validation['errors'].append("No voice profiles configured")
                validation['valid'] = False
            
            # Check CSM model availability
            try:
                self._initialize_csm_generator()
                validation['info'].append("CSM model loaded successfully")
            except Exception as e:
                validation['errors'].append(f"CSM model loading failed: {str(e)}")
                validation['valid'] = False
            
            # Check audio processor
            if self.audio_processor.sample_rate <= 0:
                validation['errors'].append("Invalid sample rate configuration")
                validation['valid'] = False
            
        except Exception as e:
            validation['errors'].append(f"Configuration validation failed: {str(e)}")
            validation['valid'] = False
        
        return validation
    
    def unload_model(self) -> None:
        """Unload the CSM model to free memory"""
        if self.csm_generator:
            self.csm_generator.unload_model()
            logger.info("CSM model unloaded")
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        try:
            if hasattr(self, 'csm_generator') and self.csm_generator:
                self.csm_generator.unload_model()
        except:
            pass