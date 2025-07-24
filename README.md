# Whimperizer - Content to Wimpy Kid PDF Pipeline

Transform web content into children's stories with handwritten Wimpy Kid aesthetics.

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r config/requirements.txt
pip install -r config/whimperizer_requirements.txt
pip install -r config/selenium_requirements.txt  # For web scraping

# Set up environment
cp .env.example .env
# Edit .env with your API keys

# Change to src directory (IMPORTANT!)
cd src

# Run complete pipeline
python pipeline.py --groups zaltz-2a --verbose
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
# First, change to src directory
cd src

# Basic usage (uses default ../data/urls.csv)
python pipeline.py --groups zaltz-2a --verbose

# With specific AI provider
python pipeline.py --provider anthropic --groups zaltz-1a

# Skip download, use existing content
python pipeline.py --skip-download --groups zaltz-1a --verbose
```

### Step-by-Step
```bash
# Change to src directory first
cd src

# 1. Download content (defaults to ../data/urls.csv)
python selenium_downloader.py --groups zaltz-1a

# 2. Transform with AI (defaults to ../config/config.yaml)
python whimperizer.py --groups zaltz-1a --verbose

# 3. Generate PDF
python wimpy_pdf_generator.py --input ../output/whimperized_content/zaltz-1a-*.md --output ../output/zaltz-1a.pdf
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

# Debug mode (from src/ directory)
python pipeline.py --verbose --dry-run

# View logs
tail -f logs/*.log
```

## 📄 License

Educational/personal use. Wimpy Kid assets © Jeff Kinney.

---

**Happy Whimperizing!** 🎉