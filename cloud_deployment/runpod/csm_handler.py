"""
RunPod Handler for CSM Audio Generation

Serverless function handler for running CSM (Conversational Speech Model) 
on RunPod GPU infrastructure.
"""

import runpod
import torch
import torchaudio
import base64
import io
import logging
import time
from typing import Dict, Any, Optional, List
from transformers import AutoProcessor, CsmForConditionalGeneration

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global model variables (loaded once for efficiency)
model = None
processor = None
device = None

def load_model():
    """Load CSM model and processor (called once on cold start)"""
    global model, processor, device
    
    if model is not None:
        return  # Already loaded
    
    logger.info("Loading CSM model...")
    start_time = time.time()
    
    # Determine device
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Using device: {device}")
    
    try:
        # Load processor
        processor = AutoProcessor.from_pretrained("sesame/csm-1b")
        
        # Load model
        model = CsmForConditionalGeneration.from_pretrained(
            "sesame/csm-1b",
            device_map=device,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32
        )
        
        # Set to evaluation mode
        model.eval()
        
        # Disable gradients for inference
        for param in model.parameters():
            param.requires_grad = False
        
        load_time = time.time() - start_time
        logger.info(f"Model loaded successfully in {load_time:.2f} seconds")
        
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        raise

def generate_speech(
    text: str,
    speaker: int = 0,
    context: Optional[List[Dict]] = None,
    max_length_ms: int = 10000,
    temperature: float = 0.8,
    top_k: int = 50,
    top_p: float = 0.9,
    **kwargs
) -> torch.Tensor:
    """
    Generate speech using CSM model
    
    Args:
        text: Text to convert to speech
        speaker: Speaker ID for voice selection
        context: Previous conversation context
        max_length_ms: Maximum audio length in milliseconds
        temperature: Sampling temperature
        top_k: Top-k sampling parameter
        top_p: Top-p sampling parameter
        **kwargs: Additional generation parameters
        
    Returns:
        torch.Tensor: Generated audio tensor
    """
    global model, processor, device
    
    try:
        # Prepare conversation
        conversation = []
        
        # Add context if provided
        if context:
            for ctx in context:
                conversation.append({
                    "role": str(ctx.get("speaker", 0)),
                    "content": [{"type": "text", "text": ctx.get("text", "")}]
                })
        
        # Add current text to generate
        conversation.append({
            "role": str(speaker),
            "content": [{"type": "text", "text": text}]
        })
        
        # Process inputs
        inputs = processor.apply_chat_template(
            conversation,
            tokenize=True,
            return_dict=True,
        ).to(device)
        
        # Generation parameters
        gen_config = {
            'temperature': temperature,
            'top_k': top_k,
            'top_p': top_p,
            'do_sample': True,
            'max_new_tokens': 1000,
            'output_audio': True,
            **kwargs
        }
        
        # Generate audio
        logger.info(f"Generating speech for: '{text[:50]}...'")
        generation_start = time.time()
        
        with torch.no_grad():
            audio_output = model.generate(**inputs, **gen_config)
        
        generation_time = time.time() - generation_start
        logger.info(f"Generation completed in {generation_time:.2f} seconds")
        
        # Extract audio tensor
        if isinstance(audio_output, tuple):
            audio = audio_output[0]
        else:
            audio = audio_output
        
        # Ensure audio is on CPU for serialization
        if hasattr(audio, 'cpu'):
            audio = audio.cpu()
        
        return audio
        
    except Exception as e:
        logger.error(f"Speech generation failed: {str(e)}")
        raise

def audio_to_base64(audio: torch.Tensor, sample_rate: int = 24000) -> str:
    """Convert audio tensor to base64 encoded WAV"""
    try:
        # Ensure audio is 2D (channels, samples)
        if audio.dim() == 1:
            audio = audio.unsqueeze(0)
        elif audio.dim() == 3:
            audio = audio.squeeze(0)
        
        # Create in-memory buffer
        buffer = io.BytesIO()
        
        # Save as WAV to buffer
        torchaudio.save(buffer, audio, sample_rate, format="wav")
        
        # Get bytes and encode as base64
        buffer.seek(0)
        audio_bytes = buffer.getvalue()
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        return audio_base64
        
    except Exception as e:
        logger.error(f"Audio encoding failed: {str(e)}")
        raise

def handler(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    RunPod serverless handler function
    
    Args:
        event: Input event with generation parameters
        
    Returns:
        Dict with generated audio and metadata
    """
    try:
        # Load model on first call
        load_model()
        
        # Extract input parameters
        input_data = event.get("input", {})
        text = input_data.get("text", "")
        speaker = input_data.get("speaker", 0)
        context = input_data.get("context", None)
        max_length_ms = input_data.get("max_length_ms", 10000)
        
        # Generation parameters
        temperature = input_data.get("temperature", 0.8)
        top_k = input_data.get("top_k", 50)
        top_p = input_data.get("top_p", 0.9)
        
        # Validate inputs
        if not text or not text.strip():
            return {
                "error": "No text provided for generation"
            }
        
        if len(text) > 5000:  # Limit text length
            return {
                "error": "Text too long (max 5000 characters)"
            }
        
        logger.info(f"Processing request - Text length: {len(text)}, Speaker: {speaker}")
        
        # Generate speech
        start_time = time.time()
        audio = generate_speech(
            text=text,
            speaker=speaker,
            context=context,
            max_length_ms=max_length_ms,
            temperature=temperature,
            top_k=top_k,
            top_p=top_p
        )
        
        # Convert to base64
        audio_base64 = audio_to_base64(audio)
        
        total_time = time.time() - start_time
        
        # Calculate audio duration
        audio_duration = audio.shape[-1] / 24000  # Assuming 24kHz sample rate
        
        # Return result
        return {
            "audio_base64": audio_base64,
            "metadata": {
                "text_length": len(text),
                "speaker_id": speaker,
                "audio_duration_seconds": round(audio_duration, 2),
                "generation_time_seconds": round(total_time, 2),
                "sample_rate": 24000,
                "audio_shape": list(audio.shape),
                "device": device
            }
        }
        
    except Exception as e:
        logger.error(f"Handler error: {str(e)}")
        return {
            "error": str(e)
        }

# RunPod serverless entrypoint
if __name__ == "__main__":
    logger.info("Starting CSM RunPod handler...")
    runpod.serverless.start({"handler": handler})