#!/bin/bash
# Install script for CSM Audio Generation Dependencies
# This script sets up the required dependencies for audiobook generation

echo "🎵 Installing CSM Audio Generation Dependencies"
echo "=============================================="

# Check Python version
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Python version: $python_version"

if [[ "$python_version" > "3.12" ]]; then
    echo "⚠️  Warning: Python $python_version detected. CSM works best with Python 3.10-3.12"
    echo "   Consider using pyenv or a virtual environment with Python 3.12"
fi

# Check if we're in a virtual environment
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  Warning: Not in a virtual environment"
    echo "   Creating virtual environment for audio dependencies..."
    
    # Try to create virtual environment
    if command -v python3.12 &> /dev/null; then
        python3.12 -m venv audio_env
        echo "✅ Created virtual environment with Python 3.12"
        source audio_env/bin/activate
    elif command -v python3.11 &> /dev/null; then
        python3.11 -m venv audio_env
        echo "✅ Created virtual environment with Python 3.11"
        source audio_env/bin/activate
    elif command -v python3.10 &> /dev/null; then
        python3.10 -m venv audio_env
        echo "✅ Created virtual environment with Python 3.10"
        source audio_env/bin/activate
    else
        echo "❌ No suitable Python version found (3.10-3.12 recommended)"
        echo "   Proceeding with system Python..."
    fi
fi

# Install system dependencies (if needed)
echo "📦 Installing system dependencies..."

# Check for ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️  ffmpeg not found. Installing..."
    if command -v apt &> /dev/null; then
        sudo apt update && sudo apt install -y ffmpeg
    elif command -v brew &> /dev/null; then
        brew install ffmpeg
    else
        echo "❌ Please install ffmpeg manually"
        exit 1
    fi
else
    echo "✅ ffmpeg found"
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."

# Basic dependencies first
echo "Installing basic dependencies..."
pip install --upgrade pip

# Install PyTorch CPU version (smaller and faster for our use case)
echo "Installing PyTorch (CPU version)..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install transformers and Hugging Face
echo "Installing Transformers and Hugging Face..."
pip install transformers>=4.49.0 tokenizers>=0.21.0 huggingface_hub>=0.28.1

# Install audio processing libraries
echo "Installing audio processing libraries..."
pip install soundfile librosa resampy pydub

# Install other dependencies
echo "Installing additional dependencies..."
pip install -r config/csm_requirements.txt 2>/dev/null || {
    echo "⚠️  CSM requirements file not found, installing individual packages..."
    pip install numpy scipy tqdm matplotlib pyyaml psutil
}

# Test the installation
echo "🧪 Testing installation..."
python3 -c "
import torch
import torchaudio
print(f'✅ PyTorch version: {torch.__version__}')
print(f'✅ TorchAudio version: {torchaudio.__version__}')

try:
    import transformers
    print(f'✅ Transformers version: {transformers.__version__}')
except ImportError:
    print('❌ Transformers not available')

try:
    import soundfile
    print('✅ SoundFile available')
except ImportError:
    print('❌ SoundFile not available')

try:
    from transformers import AutoProcessor, CsmForConditionalGeneration
    print('✅ CSM models available in transformers')
except ImportError:
    print('⚠️  CSM models not available - transformers version may be too old')
"

echo ""
echo "🎉 Installation completed!"
echo ""
echo "Next steps:"
echo "1. Enable audio generation in config/audio_config.yaml (set enabled: true)"
echo "2. Test with: python src/test_audio_generation.py"
echo "3. Run full pipeline with audio: python src/pipeline.py --urls urls.csv --groups your-group"
echo ""

if [[ -n "$VIRTUAL_ENV" ]] && [[ "$VIRTUAL_ENV" == *"audio_env"* ]]; then
    echo "💡 To use the audio environment in the future:"
    echo "   source audio_env/bin/activate"
    echo ""
fi

echo "📝 Note: First model download will take ~3GB of space"
echo "🔧 For GPU acceleration, install CUDA version of PyTorch"