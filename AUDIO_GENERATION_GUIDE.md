# Audio Generation Guide
## CSM Voice Mode Integration for Whimperizer

This guide covers the new audiobook generation capabilities added to the Whimperizer pipeline using Sesame's CSM (Conversational Speech Model).

## 🎯 Overview

The audio generation feature transforms your Wimpy Kid-style stories into immersive audiobooks with:
- **Multi-speaker voices** for different characters (Greg, Mom, Dad, Rodrick, etc.)
- **Intelligent voice assignment** based on dialogue detection
- **High-quality speech synthesis** using state-of-the-art AI models
- **Multiple output formats** (WAV, MP3)
- **Seamless pipeline integration** with existing PDF generation

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Run the automated installer
./install_audio_deps.sh

# Or install manually
pip install torch torchaudio transformers>=4.49.0 soundfile pydub
```

### 2. Enable Audio Generation

Edit `config/audio_config.yaml`:
```yaml
audio:
  enabled: true  # Set to true to enable
```

### 3. Generate Audiobooks

```bash
# Full pipeline with audio
python src/pipeline.py --urls urls.csv --groups your-group

# Audio only (skip PDF generation)
python src/pipeline.py --skip-download --skip-whimperize --groups your-group --audio-only

# Skip audio (PDF only)
python src/pipeline.py --urls urls.csv --groups your-group --skip-audio
```

## 📋 System Requirements

### Hardware
- **CPU**: Any modern multi-core processor
- **RAM**: 8GB+ recommended (4GB minimum)
- **Storage**: 5GB+ free space (3GB for model weights)
- **GPU**: Optional (CUDA-compatible for faster generation)

### Software
- **Python**: 3.10-3.12 (3.13+ not yet fully supported)
- **FFmpeg**: Required for audio processing
- **OS**: Linux, macOS, Windows (with WSL recommended)

## 🔧 Configuration

### Audio Settings (`config/audio_config.yaml`)

```yaml
audio:
  enabled: true
  
  model:
    name: "sesame/csm-1b"      # CSM model to use
    device: "cpu"              # "cpu" or "cuda"
    cache_dir: "./models/cache"
    
  output:
    formats: ["wav", "mp3"]    # Output formats
    sample_rate: 24000         # Audio quality
    channels: 1                # Mono audio
    
  voices:
    narrator: 0                # Voice IDs for characters
    greg: 1
    rodrick: 2
    mom: 3
    dad: 4
    friend: 5
    teacher: 6
    
  processing:
    max_chunk_length_ms: 10000 # Max audio chunk length
    silence_padding_ms: 500    # Silence between segments
    normalize_volume: true     # Volume normalization
    
text_processing:
  character_detection:
    enabled: true
    patterns:                  # Character detection patterns
      greg: ["I said", "I thought", "I was"]
      rodrick: ["Rodrick said", "Rodrick yelled"]
      mom: ["Mom said", "Mom told"]
      dad: ["Dad said", "Dad told"]
```

## 🎭 Voice Management

### Character Voice Assignment

The system automatically detects and assigns voices based on:

1. **Dialogue markers**: Quoted text with speaker attribution
2. **Character patterns**: Specific phrases associated with characters
3. **First-person narrative**: "I" statements typically assigned to Greg
4. **Context awareness**: Previous speaker context for consistency

### Voice Profiles

| Character | Voice ID | Description | Example Patterns |
|-----------|----------|-------------|------------------|
| Narrator  | 0        | Main story narrator | General narration text |
| Greg      | 1        | Main character | "I said", "I thought" |
| Rodrick   | 2        | Older brother | "Rodrick yelled" |
| Mom       | 3        | Mother figure | "Mom said", "Mom told" |
| Dad       | 4        | Father figure | "Dad said", "Dad asked" |
| Friend    | 5        | Peer characters | "Rowley", "friend" |
| Teacher   | 6        | Adult authorities | "teacher", "Mr./Mrs." |

## 🎵 Pipeline Integration

### Command Line Options

```bash
# Audio-specific options
--audio-dir DIRECTORY     # Output directory for audiobooks (default: audiobooks)
--skip-audio             # Skip audiobook generation
--audio-only             # Generate only audiobooks (skip PDFs)

# Examples
python src/pipeline.py --urls urls.csv --groups group1 --audio-dir my_audiobooks
python src/pipeline.py --skip-download --audio-only --groups group1
```

### Pipeline Steps

1. **Download** → Web content extraction
2. **Transform** → AI-powered story conversion
3. **PDF Generation** → Visual book creation (optional with `--audio-only`)
4. **Audio Generation** → Audiobook creation (new!)

## 📊 Performance & Optimization

### Generation Speed

| Hardware | Speed Factor | Example (1000 words) |
|----------|--------------|----------------------|
| Modern CPU | 10-20x slower than real-time | 10-20 minutes |
| Mid-range GPU | 2-5x slower than real-time | 2-5 minutes |
| High-end GPU | Real-time or faster | 1-2 minutes |

### Memory Usage

- **Model Loading**: ~3GB (CSM-1B model)
- **Generation**: ~1-2GB additional during processing
- **Output Files**: ~1MB per minute of audio (WAV), ~200KB (MP3)

### Optimization Tips

1. **Use CPU quantization** for faster inference:
   ```yaml
   quality:
     quantization: true
   ```

2. **Enable streaming** for long content:
   ```yaml
   quality:
     enable_streaming: true
   ```

3. **Adjust chunk size** for memory optimization:
   ```yaml
   processing:
     max_chunk_length_ms: 5000  # Smaller chunks
   ```

## 🛠️ Troubleshooting

### Common Issues

#### 1. Import Errors
```
Error: No module named 'torch'
```
**Solution**: Install dependencies with `./install_audio_deps.sh`

#### 2. Model Download Fails
```
Error: Failed to download model
```
**Solutions**:
- Check internet connection
- Verify Hugging Face access
- Try manual download: `huggingface-cli download sesame/csm-1b`

#### 3. Out of Memory
```
Error: CUDA out of memory / RuntimeError: out of memory
```
**Solutions**:
- Switch to CPU: `device: "cpu"`
- Enable quantization: `quantization: true`
- Reduce chunk size: `max_chunk_length_ms: 5000`

#### 4. Audio Quality Issues
**Solutions**:
- Increase sample rate: `sample_rate: 24000`
- Enable volume normalization: `normalize_volume: true`
- Adjust generation parameters:
  ```yaml
  generation:
    temperature: 0.7    # Lower for more consistent speech
    top_k: 40          # Reduce for more focused generation
  ```

#### 5. Slow Generation
**Solutions**:
- Use GPU if available: `device: "cuda"`
- Enable model optimizations in code
- Process shorter chunks
- Use streaming generation

### Debug Mode

Run with verbose output for detailed logging:
```bash
python src/pipeline.py --urls urls.csv --groups your-group --verbose
```

Test individual components:
```bash
python src/test_audio_generation.py
```

## 📈 Advanced Usage

### Custom Voice Training

While the base CSM model provides general voices, you can:
1. Fine-tune on specific character voices
2. Use voice cloning techniques
3. Adjust generation parameters per character

### Batch Processing

For large content libraries:
```bash
# Process multiple groups
python src/pipeline.py --urls urls.csv --groups group1 group2 group3

# Process all content
python src/pipeline.py --urls all_urls.csv
```

### API Integration

The audio modules can be imported and used programmatically:

```python
from audio.audiobook_generator import AudiobookGenerator
import yaml

# Load configuration
with open('config/audio_config.yaml') as f:
    config = yaml.safe_load(f)

# Initialize generator
generator = AudiobookGenerator(config)

# Generate audiobook
result = generator.generate_audiobook(
    content="Your story content here...",
    title="My Wimpy Story"
)

print(f"Generated: {result}")
```

## 🔮 Future Enhancements

### Planned Features
- **Voice cloning** for custom character voices
- **Emotion detection** for expressive speech
- **Background music** integration
- **Chapter navigation** metadata
- **Real-time streaming** generation
- **Cloud GPU** acceleration options

### Contributing

To contribute to audio generation features:
1. Fork the repository
2. Create feature branch: `git checkout -b feature/audio-enhancement`
3. Test with: `python src/test_audio_generation.py`
4. Submit pull request

## 📚 Resources

### Documentation
- [CSM Model Documentation](https://huggingface.co/sesame/csm-1b)
- [Transformers Library](https://huggingface.co/docs/transformers)
- [PyTorch Audio](https://pytorch.org/audio/stable/)

### Model Information
- **CSM-1B**: 1 billion parameter conversational speech model
- **Training Data**: Diverse speech and text datasets
- **Languages**: Primarily English (some multilingual capability)
- **License**: Apache 2.0

### Support
- **Issues**: Report bugs on GitHub Issues
- **Discussions**: Join community discussions
- **Documentation**: Check the main README and docs/

---

*Happy audiobook generation! 🎧📚*