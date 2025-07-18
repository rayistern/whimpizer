# Whimperizer - Content to Wimpy Kid PDF Pipeline

Transform web content into children's stories with handwritten Wimpy Kid aesthetics.

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r config/requirements.txt
pip install -r config/whimperizer_requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your API keys

# Run complete pipeline
python src/pipeline.py --urls data/urls.csv --verbose
```

## 📁 Project Structure

```
whimperizer/
├── src/                     # Source code
│   ├── pipeline.py          # Main orchestrator
│   ├── whimperizer.py       # AI transformation
│   ├── wimpy_pdf_generator.py # PDF generation
│   ├── bulk_downloader.py   # HTTP downloader
│   └── selenium_downloader.py # Browser automation
├── docs/                    # Documentation
│   ├── README.md            # Original detailed docs
│   ├── DOCUMENTATION.md     # Complete technical reference
│   ├── QUICK_REFERENCE.md   # Command cheat sheet
│   └── COMMIT_SUMMARY.md    # Recent improvements
├── config/                  # Configuration files
│   ├── config.yaml          # Main configuration
│   ├── requirements.txt     # Core dependencies
│   ├── whimperizer_requirements.txt # AI dependencies
│   ├── selenium_requirements.txt    # Browser automation
│   └── whimperizer_prompt.txt       # AI prompts
├── data/                    # Input data
│   ├── urls.csv             # URLs to process
│   ├── urls.txt             # Alternative URL format
│   └── input.md             # Sample input
├── tests/                   # Test files
│   └── test_extractor.py    # Content extraction tests
├── output/                  # Generated content (gitignored)
│   ├── downloaded_content/  # Raw web content
│   ├── whimperized_content/ # AI-transformed stories
│   ├── pdfs/                # Final PDFs
│   └── old/                 # Archive
├── logs/                    # Log files (gitignored)
└── resources/               # Fonts, images, templates
    ├── font/                # TTF font files
    └── backgrounds/         # Notebook paper templates
```

## 📖 Documentation

- **[📚 Complete Documentation](docs/DOCUMENTATION.md)** - Full technical reference
- **[⚡ Quick Reference](docs/QUICK_REFERENCE.md)** - Common commands
- **[📋 Original README](docs/README.md)** - Detailed usage guide

## 🎯 Essential Commands

### Complete Pipeline
```bash
# Basic usage
python src/pipeline.py --urls data/urls.csv --verbose

# With specific AI provider
python src/pipeline.py --urls data/urls.csv --provider anthropic --groups zaltz-1a

# Skip download, use existing content
python src/pipeline.py --skip-download --groups zaltz-1a --verbose
```

### Step-by-Step
```bash
# 1. Download content
python src/bulk_downloader.py --input data/urls.csv --output-dir output/downloaded_content

# 2. Transform with AI  
python src/whimperizer.py --config config/config.yaml --groups zaltz-1a --verbose

# 3. Generate PDF
python src/wimpy_pdf_generator.py --input output/whimperized_content/zaltz-1a-*.md --output output/zaltz-1a.pdf
```

## ⚙️ Configuration

### Environment Setup
```bash
# Copy example environment file
cp .env.example .env

# Edit with your API keys
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_claude_key
GOOGLE_API_KEY=your_gemini_key
```

### Main Configuration
Edit `config/config.yaml` to change AI providers, models, and processing options.

## 🔧 Recent Improvements

✅ **Character Handling** - Unicode characters automatically replaced  
✅ **Smart Typography** - Orphan header prevention, clean page breaks  
✅ **Hebrew Month Support** - Universal calendar system  
✅ **Organized Codebase** - Clean folder structure with proper gitignore  

## 🎨 Features

- **Multi-Provider AI**: OpenAI GPT-4, Claude 3, Gemini Pro
- **Advanced Web Scraping**: HTTP + Selenium browser automation  
- **Handwritten PDFs**: Realistic handwriting effects with notebook backgrounds
- **Smart Typography**: Professional page layout and spacing
- **Batch Processing**: Handle multiple documents simultaneously

## 🛠️ Development

```bash
# Run tests
python -m pytest tests/ -v

# Debug mode
python src/pipeline.py --verbose --dry-run

# View logs
tail -f logs/*.log
```

## 📄 License

Educational/personal use. Wimpy Kid assets © Jeff Kinney.

---

**Happy Whimperizing!** 🎉