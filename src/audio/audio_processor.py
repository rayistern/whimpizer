"""
Audio Processor Module

Handles audio file manipulation, format conversion, concatenation, and optimization
for audiobook generation. Provides utilities for audio post-processing and enhancement.
"""

import os
import logging
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
import torch
import torchaudio
import numpy as np
from pydub import AudioSegment as PydubSegment
from pydub.effects import normalize, compress_dynamic_range
import tempfile

logger = logging.getLogger(__name__)


class AudioProcessor:
    """
    Audio processing utilities for audiobook generation
    
    Provides audio manipulation, format conversion, concatenation, and optimization
    features for creating high-quality audiobooks from CSM-generated speech.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Audio Processor
        
        Args:
            config: Configuration dictionary with audio processing settings
        """
        self.config = config
        self.audio_config = config.get('audio', {})
        self.processing_config = self.audio_config.get('processing', {})
        
        # Audio settings
        self.sample_rate = self.audio_config.get('output', {}).get('sample_rate', 24000)
        self.channels = self.audio_config.get('output', {}).get('channels', 1)
        self.bit_depth = self.audio_config.get('output', {}).get('bit_depth', 16)
        
        # Processing settings
        self.normalize_volume = self.processing_config.get('normalize_volume', True)
        self.compress_audio = self.processing_config.get('compress_audio', True)
        self.silence_padding_ms = self.processing_config.get('silence_padding_ms', 500)
        self.fade_in_ms = self.processing_config.get('fade_in_ms', 100)
        self.fade_out_ms = self.processing_config.get('fade_out_ms', 100)
        
        logger.info(f"Initialized Audio Processor - Sample rate: {self.sample_rate}Hz, Channels: {self.channels}")
    
    def process_audio_tensor(
        self,
        audio: torch.Tensor,
        apply_effects: bool = True
    ) -> torch.Tensor:
        """
        Process raw audio tensor with enhancements
        
        Args:
            audio: Input audio tensor
            apply_effects: Whether to apply audio effects
            
        Returns:
            torch.Tensor: Processed audio tensor
        """
        try:
            # Ensure audio is on CPU
            if audio.device != torch.device('cpu'):
                audio = audio.cpu()
            
            # Ensure correct shape (channels, samples)
            if audio.dim() == 1:
                audio = audio.unsqueeze(0)
            elif audio.dim() == 3:
                audio = audio.squeeze(0)
            
            # Convert to target channels
            if audio.shape[0] != self.channels:
                if self.channels == 1 and audio.shape[0] > 1:
                    # Convert to mono by averaging channels
                    audio = torch.mean(audio, dim=0, keepdim=True)
                elif self.channels == 2 and audio.shape[0] == 1:
                    # Convert to stereo by duplicating mono channel
                    audio = audio.repeat(2, 1)
            
            if apply_effects:
                audio = self._apply_audio_effects(audio)
            
            return audio
            
        except Exception as e:
            logger.error(f"Audio processing failed: {str(e)}")
            return audio  # Return original if processing fails
    
    def _apply_audio_effects(self, audio: torch.Tensor) -> torch.Tensor:
        """Apply audio effects like fading and normalization"""
        try:
            # Apply fade in/out
            audio = self._apply_fade(audio)
            
            # Normalize volume if enabled
            if self.normalize_volume:
                audio = self._normalize_audio(audio)
            
            # Apply gentle compression if enabled
            if self.compress_audio:
                audio = self._apply_compression(audio)
            
            return audio
            
        except Exception as e:
            logger.warning(f"Failed to apply audio effects: {str(e)}")
            return audio
    
    def _apply_fade(self, audio: torch.Tensor) -> torch.Tensor:
        """Apply fade in and fade out effects"""
        try:
            samples = audio.shape[-1]
            fade_in_samples = int(self.fade_in_ms * self.sample_rate / 1000)
            fade_out_samples = int(self.fade_out_ms * self.sample_rate / 1000)
            
            # Apply fade in
            if fade_in_samples > 0 and samples > fade_in_samples:
                fade_in = torch.linspace(0, 1, fade_in_samples)
                audio[:, :fade_in_samples] *= fade_in
            
            # Apply fade out
            if fade_out_samples > 0 and samples > fade_out_samples:
                fade_out = torch.linspace(1, 0, fade_out_samples)
                audio[:, -fade_out_samples:] *= fade_out
            
            return audio
            
        except Exception as e:
            logger.warning(f"Failed to apply fade effects: {str(e)}")
            return audio
    
    def _normalize_audio(self, audio: torch.Tensor) -> torch.Tensor:
        """Normalize audio volume"""
        try:
            # Calculate RMS and normalize to target level
            rms = torch.sqrt(torch.mean(audio ** 2))
            if rms > 0:
                target_rms = 0.2  # Target RMS level
                audio = audio * (target_rms / rms)
            
            # Prevent clipping
            max_val = torch.max(torch.abs(audio))
            if max_val > 0.95:
                audio = audio * (0.95 / max_val)
            
            return audio
            
        except Exception as e:
            logger.warning(f"Failed to normalize audio: {str(e)}")
            return audio
    
    def _apply_compression(self, audio: torch.Tensor) -> torch.Tensor:
        """Apply gentle dynamic range compression"""
        try:
            # Simple soft compression
            threshold = 0.7
            ratio = 0.5
            
            # Apply compression above threshold
            mask = torch.abs(audio) > threshold
            compressed = torch.sign(audio) * (
                threshold + (torch.abs(audio) - threshold) * ratio
            )
            audio = torch.where(mask, compressed, audio)
            
            return audio
            
        except Exception as e:
            logger.warning(f"Failed to apply compression: {str(e)}")
            return audio
    
    def concatenate_audio_files(
        self,
        audio_files: List[str],
        output_path: str,
        add_silence: bool = True
    ) -> str:
        """
        Concatenate multiple audio files into a single file
        
        Args:
            audio_files: List of audio file paths to concatenate
            output_path: Output file path
            add_silence: Whether to add silence between segments
            
        Returns:
            str: Path to concatenated audio file
        """
        try:
            if not audio_files:
                raise ValueError("No audio files provided for concatenation")
            
            # Load and concatenate audio segments
            combined_audio = None
            
            for i, audio_file in enumerate(audio_files):
                if not os.path.exists(audio_file):
                    logger.warning(f"Audio file not found: {audio_file}")
                    continue
                
                # Load audio
                audio, sample_rate = torchaudio.load(audio_file)
                
                # Resample if necessary
                if sample_rate != self.sample_rate:
                    resampler = torchaudio.transforms.Resample(sample_rate, self.sample_rate)
                    audio = resampler(audio)
                
                # Process audio
                audio = self.process_audio_tensor(audio)
                
                # Add to combined audio
                if combined_audio is None:
                    combined_audio = audio
                else:
                    # Add silence padding if requested
                    if add_silence:
                        silence = self._create_silence(self.silence_padding_ms)
                        combined_audio = torch.cat([combined_audio, silence, audio], dim=-1)
                    else:
                        combined_audio = torch.cat([combined_audio, audio], dim=-1)
                
                logger.debug(f"Added audio segment {i+1}/{len(audio_files)}")
            
            if combined_audio is not None:
                # Save concatenated audio
                self.save_audio(combined_audio, output_path)
                logger.info(f"Concatenated {len(audio_files)} audio files to: {output_path}")
                return output_path
            else:
                raise RuntimeError("No valid audio files found for concatenation")
                
        except Exception as e:
            logger.error(f"Audio concatenation failed: {str(e)}")
            raise RuntimeError(f"Audio concatenation failed: {str(e)}")
    
    def _create_silence(self, duration_ms: int) -> torch.Tensor:
        """Create a silence tensor of specified duration"""
        samples = int(duration_ms * self.sample_rate / 1000)
        return torch.zeros(self.channels, samples)
    
    def convert_format(
        self,
        input_path: str,
        output_path: str,
        target_format: str = "mp3",
        quality: str = "high"
    ) -> str:
        """
        Convert audio file to different format
        
        Args:
            input_path: Input audio file path
            output_path: Output audio file path
            target_format: Target format (mp3, wav, flac, etc.)
            quality: Quality setting (low, medium, high)
            
        Returns:
            str: Path to converted file
        """
        try:
            # Load audio using pydub for format conversion
            audio_segment = PydubSegment.from_file(input_path)
            
            # Set quality parameters based on target format
            export_params = self._get_export_params(target_format, quality)
            
            # Export in target format
            audio_segment.export(output_path, format=target_format, **export_params)
            
            logger.info(f"Converted audio from {input_path} to {output_path} ({target_format})")
            return output_path
            
        except Exception as e:
            logger.error(f"Audio format conversion failed: {str(e)}")
            raise RuntimeError(f"Audio format conversion failed: {str(e)}")
    
    def _get_export_params(self, format: str, quality: str) -> Dict[str, Any]:
        """Get export parameters for different formats and qualities"""
        params = {}
        
        if format.lower() == "mp3":
            if quality == "high":
                params = {"bitrate": "320k"}
            elif quality == "medium":
                params = {"bitrate": "192k"}
            else:  # low
                params = {"bitrate": "128k"}
        elif format.lower() == "wav":
            # WAV doesn't use bitrate
            params = {}
        elif format.lower() == "flac":
            # FLAC is lossless
            params = {}
        
        return params
    
    def save_audio(
        self,
        audio: torch.Tensor,
        output_path: str,
        format: str = "wav"
    ) -> None:
        """
        Save audio tensor to file
        
        Args:
            audio: Audio tensor to save
            output_path: Output file path
            format: Audio format
        """
        try:
            # Ensure output directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Process audio
            audio = self.process_audio_tensor(audio)
            
            # Save using torchaudio
            torchaudio.save(
                output_path,
                audio,
                self.sample_rate,
                format=format.upper() if format.upper() in ['WAV', 'FLAC'] else None
            )
            
            logger.debug(f"Audio saved to: {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to save audio: {str(e)}")
            raise RuntimeError(f"Audio saving failed: {str(e)}")
    
    def create_audiobook_structure(
        self,
        chapter_files: List[str],
        output_dir: str,
        book_title: str,
        formats: List[str] = None
    ) -> Dict[str, str]:
        """
        Create complete audiobook structure with multiple formats
        
        Args:
            chapter_files: List of chapter audio files
            output_dir: Output directory for audiobook
            book_title: Title of the book
            formats: List of output formats to create
            
        Returns:
            Dict mapping format to output file path
        """
        if formats is None:
            formats = self.audio_config.get('output', {}).get('formats', ['wav', 'mp3'])
        
        output_paths = {}
        
        try:
            # Create output directory
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            # Create master WAV file first
            safe_title = "".join(c for c in book_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            master_wav_path = os.path.join(output_dir, f"{safe_title}_audiobook.wav")
            
            # Concatenate all chapters
            self.concatenate_audio_files(
                chapter_files,
                master_wav_path,
                add_silence=True
            )
            
            output_paths['wav'] = master_wav_path
            
            # Create other formats if requested
            for format_name in formats:
                if format_name.lower() != 'wav':
                    output_path = os.path.join(output_dir, f"{safe_title}_audiobook.{format_name}")
                    converted_path = self.convert_format(
                        master_wav_path,
                        output_path,
                        format_name,
                        quality="high"
                    )
                    output_paths[format_name] = converted_path
            
            # Create metadata file
            metadata_path = os.path.join(output_dir, "metadata.txt")
            self._create_metadata_file(metadata_path, book_title, chapter_files, output_paths)
            
            logger.info(f"Created audiobook structure in: {output_dir}")
            return output_paths
            
        except Exception as e:
            logger.error(f"Failed to create audiobook structure: {str(e)}")
            raise RuntimeError(f"Audiobook creation failed: {str(e)}")
    
    def _create_metadata_file(
        self,
        metadata_path: str,
        book_title: str,
        chapter_files: List[str],
        output_paths: Dict[str, str]
    ) -> None:
        """Create metadata file for the audiobook"""
        try:
            with open(metadata_path, 'w', encoding='utf-8') as f:
                f.write(f"Title: {book_title}\n")
                f.write(f"Generated by: Whimperizer CSM Voice Integration\n")
                f.write(f"Total chapters: {len(chapter_files)}\n")
                f.write(f"Sample rate: {self.sample_rate}Hz\n")
                f.write(f"Channels: {self.channels}\n")
                f.write("\nOutput files:\n")
                for format_name, path in output_paths.items():
                    file_size = os.path.getsize(path) / (1024 * 1024)  # MB
                    f.write(f"- {format_name.upper()}: {os.path.basename(path)} ({file_size:.1f} MB)\n")
                
                f.write("\nChapter files:\n")
                for i, chapter_file in enumerate(chapter_files, 1):
                    f.write(f"- Chapter {i}: {os.path.basename(chapter_file)}\n")
            
            logger.debug(f"Metadata file created: {metadata_path}")
            
        except Exception as e:
            logger.warning(f"Failed to create metadata file: {str(e)}")
    
    def get_audio_info(self, audio_path: str) -> Dict[str, Any]:
        """
        Get information about an audio file
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dict with audio information
        """
        try:
            # Load audio metadata
            audio, sample_rate = torchaudio.load(audio_path)
            
            info = {
                'path': audio_path,
                'duration_seconds': audio.shape[-1] / sample_rate,
                'sample_rate': sample_rate,
                'channels': audio.shape[0],
                'samples': audio.shape[-1],
                'file_size_mb': os.path.getsize(audio_path) / (1024 * 1024),
                'format': Path(audio_path).suffix.lower().lstrip('.')
            }
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to get audio info: {str(e)}")
            return {'path': audio_path, 'error': str(e)}
    
    def cleanup_temp_files(self, temp_dir: str) -> None:
        """Clean up temporary audio files"""
        try:
            if os.path.exists(temp_dir):
                for file in os.listdir(temp_dir):
                    file_path = os.path.join(temp_dir, file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        logger.debug(f"Removed temp file: {file_path}")
                
                # Remove directory if empty
                if not os.listdir(temp_dir):
                    os.rmdir(temp_dir)
                    logger.debug(f"Removed temp directory: {temp_dir}")
                    
        except Exception as e:
            logger.warning(f"Failed to cleanup temp files: {str(e)}")