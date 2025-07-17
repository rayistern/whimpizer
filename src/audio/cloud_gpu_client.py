"""
Cloud GPU Client for CSM Audio Generation

Offloads CSM processing to cloud GPU services for faster, more cost-effective generation.
Supports multiple providers: RunPod, Modal, Thunder Compute, etc.
"""

import os
import requests
import json
import time
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import base64
import io
import torch
import torchaudio

logger = logging.getLogger(__name__)


@dataclass
class CloudGPUConfig:
    """Configuration for cloud GPU providers"""
    provider: str  # "runpod", "modal", "thunder", "replicate"
    api_key: str
    endpoint_url: Optional[str] = None
    model_id: Optional[str] = None
    region: str = "us-east-1"
    timeout: int = 300  # 5 minutes default


class CloudGPUClient:
    """
    Client for offloading CSM audio generation to cloud GPU services
    
    Provides the same interface as local CSMGenerator but processes remotely
    for significant cost savings and GPU acceleration.
    """
    
    def __init__(self, config: CloudGPUConfig):
        """
        Initialize cloud GPU client
        
        Args:
            config: Cloud GPU configuration
        """
        self.config = config
        self.provider = config.provider.lower()
        self.session = requests.Session()
        
        # Set up authentication
        if config.api_key:
            if self.provider == "runpod":
                self.session.headers.update({"Authorization": f"Bearer {config.api_key}"})
            elif self.provider == "modal":
                self.session.headers.update({"Authorization": f"Bearer {config.api_key}"})
            elif self.provider == "replicate":
                self.session.headers.update({"Authorization": f"Token {config.api_key}"})
        
        logger.info(f"Initialized {self.provider} cloud GPU client")
    
    def generate_speech(
        self,
        text: str,
        speaker: int = 0,
        context: Optional[List] = None,
        max_length_ms: int = 10000,
        **kwargs
    ) -> torch.Tensor:
        """
        Generate speech using cloud GPU service
        
        Args:
            text: Text to convert to speech
            speaker: Speaker ID
            context: Previous conversation context
            max_length_ms: Maximum audio length
            **kwargs: Additional generation parameters
            
        Returns:
            torch.Tensor: Generated audio tensor
        """
        try:
            if self.provider == "runpod":
                return self._generate_runpod(text, speaker, context, max_length_ms, **kwargs)
            elif self.provider == "modal":
                return self._generate_modal(text, speaker, context, max_length_ms, **kwargs)
            elif self.provider == "replicate":
                return self._generate_replicate(text, speaker, context, max_length_ms, **kwargs)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
                
        except Exception as e:
            logger.error(f"Cloud GPU generation failed: {str(e)}")
            raise RuntimeError(f"Cloud generation failed: {str(e)}")
    
    def _generate_runpod(
        self,
        text: str,
        speaker: int,
        context: Optional[List],
        max_length_ms: int,
        **kwargs
    ) -> torch.Tensor:
        """Generate speech using RunPod serverless endpoint"""
        
        payload = {
            "input": {
                "text": text,
                "speaker": speaker,
                "context": self._serialize_context(context) if context else None,
                "max_length_ms": max_length_ms,
                **kwargs
            }
        }
        
        response = self.session.post(
            self.config.endpoint_url,
            json=payload,
            timeout=self.config.timeout
        )
        response.raise_for_status()
        
        result = response.json()
        
        # Handle async response
        if "id" in result:
            return self._poll_runpod_result(result["id"])
        else:
            return self._decode_audio_response(result["output"])
    
    def _generate_modal(
        self,
        text: str,
        speaker: int,
        context: Optional[List],
        max_length_ms: int,
        **kwargs
    ) -> torch.Tensor:
        """Generate speech using Modal serverless function"""
        
        payload = {
            "text": text,
            "speaker": speaker,
            "context": self._serialize_context(context) if context else None,
            "max_length_ms": max_length_ms,
            **kwargs
        }
        
        response = self.session.post(
            self.config.endpoint_url,
            json=payload,
            timeout=self.config.timeout
        )
        response.raise_for_status()
        
        result = response.json()
        return self._decode_audio_response(result)
    
    def _generate_replicate(
        self,
        text: str,
        speaker: int,
        context: Optional[List],
        max_length_ms: int,
        **kwargs
    ) -> torch.Tensor:
        """Generate speech using Replicate API"""
        
        payload = {
            "version": self.config.model_id,
            "input": {
                "text": text,
                "speaker": speaker,
                "context": self._serialize_context(context) if context else None,
                "max_length_ms": max_length_ms,
                **kwargs
            }
        }
        
        # Create prediction
        response = self.session.post(
            "https://api.replicate.com/v1/predictions",
            json=payload,
            timeout=self.config.timeout
        )
        response.raise_for_status()
        
        prediction = response.json()
        return self._poll_replicate_result(prediction["id"])
    
    def _poll_runpod_result(self, job_id: str) -> torch.Tensor:
        """Poll RunPod for job completion"""
        
        status_url = f"{self.config.endpoint_url.replace('/run', '/status')}/{job_id}"
        
        for _ in range(60):  # Poll for up to 5 minutes
            response = self.session.get(status_url)
            response.raise_for_status()
            
            result = response.json()
            status = result.get("status")
            
            if status == "COMPLETED":
                return self._decode_audio_response(result["output"])
            elif status == "FAILED":
                raise RuntimeError(f"RunPod job failed: {result.get('error', 'Unknown error')}")
            
            time.sleep(5)
        
        raise TimeoutError("RunPod job timed out")
    
    def _poll_replicate_result(self, prediction_id: str) -> torch.Tensor:
        """Poll Replicate for prediction completion"""
        
        status_url = f"https://api.replicate.com/v1/predictions/{prediction_id}"
        
        for _ in range(60):  # Poll for up to 5 minutes
            response = self.session.get(status_url)
            response.raise_for_status()
            
            result = response.json()
            status = result.get("status")
            
            if status == "succeeded":
                return self._decode_audio_response(result["output"])
            elif status == "failed":
                raise RuntimeError(f"Replicate prediction failed: {result.get('error', 'Unknown error')}")
            
            time.sleep(5)
        
        raise TimeoutError("Replicate prediction timed out")
    
    def _serialize_context(self, context: List) -> List[Dict]:
        """Serialize context for API transmission"""
        serialized = []
        for segment in context:
            item = {
                "text": segment.text,
                "speaker": segment.speaker,
                "speaker_name": getattr(segment, 'speaker_name', None)
            }
            # Note: Audio context not serialized for API calls
            serialized.append(item)
        return serialized
    
    def _decode_audio_response(self, response_data: Dict) -> torch.Tensor:
        """Decode audio response from API"""
        try:
            if "audio_base64" in response_data:
                # Base64 encoded audio
                audio_bytes = base64.b64decode(response_data["audio_base64"])
                audio_buffer = io.BytesIO(audio_bytes)
                audio, sample_rate = torchaudio.load(audio_buffer)
                return audio
            
            elif "audio_url" in response_data:
                # Download from URL
                audio_response = requests.get(response_data["audio_url"])
                audio_response.raise_for_status()
                
                audio_buffer = io.BytesIO(audio_response.content)
                audio, sample_rate = torchaudio.load(audio_buffer)
                return audio
            
            else:
                raise ValueError("No audio data found in response")
                
        except Exception as e:
            logger.error(f"Failed to decode audio response: {str(e)}")
            raise RuntimeError(f"Audio decoding failed: {str(e)}")
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the cloud provider"""
        return {
            "provider": self.provider,
            "endpoint_url": self.config.endpoint_url,
            "region": self.config.region,
            "model_id": self.config.model_id
        }
    
    def estimate_cost(
        self, 
        text_length: int, 
        estimated_generation_time_seconds: float
    ) -> Dict[str, float]:
        """
        Estimate cost for generation
        
        Args:
            text_length: Length of text to generate
            estimated_generation_time_seconds: Expected generation time
            
        Returns:
            Dict with cost estimates
        """
        # Rough cost estimates (update based on current pricing)
        cost_per_second = {
            "runpod": 1.19 / 3600,      # $1.19/hour for A100
            "modal": 2.50 / 3600,       # ~$2.50/hour estimated
            "thunder": 0.66 / 3600,     # $0.66/hour for A100
            "replicate": 0.0005,        # ~$0.0005 per prediction
        }
        
        base_cost = cost_per_second.get(self.provider, 0.001) * estimated_generation_time_seconds
        
        return {
            "estimated_cost_usd": base_cost,
            "cost_per_word": base_cost / max(len(text_length.split()), 1),
            "provider": self.provider,
            "estimated_time_seconds": estimated_generation_time_seconds
        }


class CloudGPUManager:
    """
    Manager for multiple cloud GPU providers with fallback support
    """
    
    def __init__(self, configs: List[CloudGPUConfig]):
        """
        Initialize with multiple provider configurations
        
        Args:
            configs: List of cloud GPU configurations in priority order
        """
        self.clients = [CloudGPUClient(config) for config in configs]
        self.current_client_index = 0
    
    def generate_speech(self, *args, **kwargs) -> torch.Tensor:
        """Generate speech with automatic fallback between providers"""
        
        for i, client in enumerate(self.clients):
            try:
                logger.info(f"Attempting generation with {client.provider}")
                result = client.generate_speech(*args, **kwargs)
                
                # Update successful client as primary
                if i != self.current_client_index:
                    self.current_client_index = i
                    logger.info(f"Switched primary provider to {client.provider}")
                
                return result
                
            except Exception as e:
                logger.warning(f"Provider {client.provider} failed: {str(e)}")
                if i == len(self.clients) - 1:
                    # All providers failed
                    raise RuntimeError("All cloud GPU providers failed")
                continue
    
    def get_current_provider(self) -> str:
        """Get currently active provider"""
        return self.clients[self.current_client_index].provider


# Configuration examples
def create_runpod_config(api_key: str, endpoint_url: str) -> CloudGPUConfig:
    """Create RunPod configuration"""
    return CloudGPUConfig(
        provider="runpod",
        api_key=api_key,
        endpoint_url=endpoint_url,
        region="us-east-1"
    )

def create_modal_config(api_key: str, function_url: str) -> CloudGPUConfig:
    """Create Modal configuration"""
    return CloudGPUConfig(
        provider="modal",
        api_key=api_key,
        endpoint_url=function_url
    )

def create_thunder_config(api_key: str, endpoint_url: str) -> CloudGPUConfig:
    """Create Thunder Compute configuration"""
    return CloudGPUConfig(
        provider="thunder",
        api_key=api_key,
        endpoint_url=endpoint_url
    )