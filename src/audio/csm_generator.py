"""
CSM Generator Module

Core wrapper for Sesame's CSM (Conversational Speech Model) that provides
text-to-speech conversion with context-aware generation and multi-speaker support.
"""

import os
import logging
import warnings
from typing import Optional, List, Dict, Any, Union
from pathlib import Path
import torch
import torchaudio
from transformers import AutoProcessor, CsmForConditionalGeneration
from dataclasses import dataclass

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

logger = logging.getLogger(__name__)


@dataclass
class AudioSegment:
    """Represents an audio segment with metadata"""
    text: str
    speaker: int
    audio: Optional[torch.Tensor] = None
    duration_ms: Optional[float] = None
    speaker_name: Optional[str] = None


class CSMGenerator:
    """
    CSM (Conversational Speech Model) Generator
    
    Provides text-to-speech conversion using Sesame's CSM model with support for
    multi-speaker generation, context-aware synthesis, and conversation modeling.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize CSM Generator
        
        Args:
            config: Configuration dictionary containing model and generation settings
        """
        self.config = config
        self.model_config = config.get('audio', {}).get('model', {})
        self.generation_config = config.get('audio', {}).get('generation', {})
        
        self.model_name = self.model_config.get('name', 'sesame/csm-1b')
        self.device = self._determine_device()
        self.sample_rate = config.get('audio', {}).get('output', {}).get('sample_rate', 24000)
        
        # Model components
        self.model = None
        self.processor = None
        self.is_loaded = False
        
        # Performance settings
        self.precision = self.model_config.get('precision', 'float32')
        self.cache_dir = self.model_config.get('cache_dir', './models/cache')
        
        logger.info(f"Initialized CSM Generator with model: {self.model_name}")
        logger.info(f"Device: {self.device}, Sample rate: {self.sample_rate}")
    
    def _determine_device(self) -> str:
        """Determine the best available device for inference"""
        configured_device = self.model_config.get('device', 'cpu')
        
        if configured_device == 'cuda' and torch.cuda.is_available():
            device = 'cuda'
            logger.info(f"GPU detected: {torch.cuda.get_device_name()}")
        elif configured_device == 'mps' and torch.backends.mps.is_available():
            device = 'mps'
            logger.info("Apple Silicon GPU (MPS) detected")
        else:
            device = 'cpu'
            if configured_device != 'cpu':
                logger.warning(f"Requested device '{configured_device}' not available, falling back to CPU")
        
        return device
    
    def load_model(self) -> None:
        """Load the CSM model and processor"""
        if self.is_loaded:
            logger.info("Model already loaded")
            return
        
        try:
            logger.info(f"Loading CSM model: {self.model_name}")
            
            # Ensure cache directory exists
            Path(self.cache_dir).mkdir(parents=True, exist_ok=True)
            
            # Load processor
            logger.info("Loading processor...")
            self.processor = AutoProcessor.from_pretrained(
                self.model_name,
                cache_dir=self.cache_dir
            )
            
            # Load model
            logger.info("Loading model...")
            self.model = CsmForConditionalGeneration.from_pretrained(
                self.model_name,
                device_map=self.device,
                cache_dir=self.cache_dir,
                torch_dtype=torch.float32 if self.precision == 'float32' else torch.float16
            )
            
            # Set model to evaluation mode
            self.model.eval()
            
            # Apply optimizations
            self._apply_optimizations()
            
            self.is_loaded = True
            logger.info(f"Model loaded successfully on {self.device}")
            
        except Exception as e:
            logger.error(f"Failed to load CSM model: {str(e)}")
            raise RuntimeError(f"Model loading failed: {str(e)}")
    
    def _apply_optimizations(self) -> None:
        """Apply performance optimizations to the model"""
        try:
            # Disable gradient computation for inference
            for param in self.model.parameters():
                param.requires_grad = False
            
            # Enable quantization if configured
            if self.config.get('audio', {}).get('quality', {}).get('quantization', False):
                logger.info("Applying model quantization...")
                # Note: Quantization implementation would go here
                # This is a placeholder for future optimization
            
            logger.info("Model optimizations applied")
            
        except Exception as e:
            logger.warning(f"Failed to apply some optimizations: {str(e)}")
    
    def generate_speech(
        self,
        text: str,
        speaker: int = 0,
        context: Optional[List[AudioSegment]] = None,
        max_length_ms: int = 10000,
        **generation_kwargs
    ) -> torch.Tensor:
        """
        Generate speech from text using CSM
        
        Args:
            text: Text to convert to speech
            speaker: Speaker ID for voice selection
            context: Previous conversation context for better generation
            max_length_ms: Maximum audio length in milliseconds
            **generation_kwargs: Additional generation parameters
        
        Returns:
            torch.Tensor: Generated audio tensor
        """
        if not self.is_loaded:
            self.load_model()
        
        try:
            # Prepare the conversation for CSM
            conversation = self._prepare_conversation(text, speaker, context)
            
            # Process inputs
            inputs = self.processor.apply_chat_template(
                conversation,
                tokenize=True,
                return_dict=True,
            ).to(self.device)
            
            # Merge generation config with kwargs
            gen_config = {
                'temperature': self.generation_config.get('temperature', 0.8),
                'top_k': self.generation_config.get('top_k', 50),
                'top_p': self.generation_config.get('top_p', 0.9),
                'do_sample': self.generation_config.get('do_sample', True),
                'max_new_tokens': self.generation_config.get('max_new_tokens', 1000),
                'output_audio': True,
                **generation_kwargs
            }
            
            # Generate audio
            logger.debug(f"Generating speech for text: '{text[:50]}...'")
            with torch.no_grad():
                audio_output = self.model.generate(**inputs, **gen_config)
            
            # Extract audio tensor
            if isinstance(audio_output, tuple):
                audio = audio_output[0]
            else:
                audio = audio_output
            
            # Ensure audio is on CPU for further processing
            if hasattr(audio, 'cpu'):
                audio = audio.cpu()
            
            logger.debug(f"Generated audio shape: {audio.shape if hasattr(audio, 'shape') else 'unknown'}")
            return audio
            
        except Exception as e:
            logger.error(f"Speech generation failed: {str(e)}")
            raise RuntimeError(f"Speech generation failed: {str(e)}")
    
    def _prepare_conversation(
        self,
        text: str,
        speaker: int,
        context: Optional[List[AudioSegment]] = None
    ) -> List[Dict[str, Any]]:
        """
        Prepare conversation format for CSM input
        
        Args:
            text: Current text to generate
            speaker: Speaker ID
            context: Previous conversation context
        
        Returns:
            List of conversation turns in CSM format
        """
        conversation = []
        
        # Add context if provided
        if context:
            for segment in context:
                turn = {
                    "role": str(segment.speaker),
                    "content": [{"type": "text", "text": segment.text}]
                }
                
                # Add audio context if available
                if segment.audio is not None:
                    turn["content"].append({
                        "type": "audio", 
                        "path": segment.audio
                    })
                
                conversation.append(turn)
        
        # Add current text to generate
        conversation.append({
            "role": str(speaker),
            "content": [{"type": "text", "text": text}]
        })
        
        return conversation
    
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
            format: Audio format (wav, mp3, etc.)
        """
        try:
            # Ensure output directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Ensure audio is 2D (channels, samples)
            if audio.dim() == 1:
                audio = audio.unsqueeze(0)
            elif audio.dim() == 3:
                audio = audio.squeeze(0)
            
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
    
    def batch_generate(
        self,
        texts: List[str],
        speakers: List[int],
        output_dir: str,
        context: Optional[List[AudioSegment]] = None
    ) -> List[str]:
        """
        Generate speech for multiple texts in batch
        
        Args:
            texts: List of texts to convert
            speakers: List of speaker IDs for each text
            output_dir: Directory to save audio files
            context: Shared context for all generations
        
        Returns:
            List of output file paths
        """
        if len(texts) != len(speakers):
            raise ValueError("Number of texts must match number of speakers")
        
        output_paths = []
        
        for i, (text, speaker) in enumerate(zip(texts, speakers)):
            try:
                # Generate audio
                audio = self.generate_speech(text, speaker, context)
                
                # Create output path
                output_path = os.path.join(output_dir, f"segment_{i:04d}.wav")
                
                # Save audio
                self.save_audio(audio, output_path)
                output_paths.append(output_path)
                
                logger.info(f"Generated segment {i+1}/{len(texts)}: {output_path}")
                
            except Exception as e:
                logger.error(f"Failed to generate segment {i+1}: {str(e)}")
                # Continue with other segments
                continue
        
        return output_paths
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        info = {
            'model_name': self.model_name,
            'device': self.device,
            'sample_rate': self.sample_rate,
            'is_loaded': self.is_loaded,
            'precision': self.precision
        }
        
        if self.is_loaded and self.model:
            try:
                # Get model size info
                param_count = sum(p.numel() for p in self.model.parameters())
                info['parameters'] = param_count
                info['memory_usage_mb'] = param_count * 4 / (1024 * 1024)  # Rough estimate
            except:
                info['parameters'] = 'unknown'
                info['memory_usage_mb'] = 'unknown'
        
        return info
    
    def unload_model(self) -> None:
        """Unload the model to free memory"""
        if self.is_loaded:
            del self.model
            del self.processor
            self.model = None
            self.processor = None
            self.is_loaded = False
            
            # Clear GPU cache if using CUDA
            if self.device == 'cuda':
                torch.cuda.empty_cache()
            
            logger.info("Model unloaded successfully")
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        if hasattr(self, 'is_loaded') and self.is_loaded:
            self.unload_model()