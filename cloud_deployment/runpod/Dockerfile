# RunPod CSM Deployment
# Dockerfile for running CSM (Conversational Speech Model) on RunPod serverless GPUs

FROM runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    sox \
    libsndfile1 \
    git \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install CSM-specific dependencies
RUN pip install --no-cache-dir \
    torch>=2.4.0 \
    torchaudio>=2.4.0 \
    transformers>=4.49.0 \
    tokenizers>=0.21.0 \
    huggingface_hub>=0.28.1 \
    soundfile>=0.12.1 \
    pydub>=0.25.1 \
    numpy>=1.24.0 \
    scipy>=1.11.0

# Copy application code
COPY csm_handler.py .
COPY audio_utils.py .

# Set environment variables
ENV PYTHONPATH=/app
ENV HF_HOME=/tmp/huggingface
ENV TORCH_HOME=/tmp/torch
ENV NO_TORCH_COMPILE=1

# Create cache directories
RUN mkdir -p /tmp/huggingface /tmp/torch

# Pre-download the CSM model (optional, for faster cold starts)
# RUN python -c "from transformers import AutoProcessor, CsmForConditionalGeneration; AutoProcessor.from_pretrained('sesame/csm-1b'); CsmForConditionalGeneration.from_pretrained('sesame/csm-1b')"

# Expose the handler function
CMD ["python", "-u", "csm_handler.py"]