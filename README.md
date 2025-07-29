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

# Single run pipeline
python pipeline.py --groups zaltz-2a --verbose

# Multi-run pipeline with consolidation (NEW!)
python pipeline.py --runs 3 --groups zaltz-2a --verbose
```

## 🎯 What's New - Multi-Run System

**Generate multiple AI outputs and consolidate them into one best version:**

| Tool | What It Does | When To Use |
|------|-------------|-------------|
| `pipeline.py --runs N` | Original pipeline + auto-consolidation when N>1 | Quick multi-run with familiar interface |
| `multi_pipeline.py` | Same as above + `--consolidate-only` & `--skip-consolidate` | When you need those 2 extra options |
| `multi_runner.py` | Runs `whimperizer.py` N times with different models | Standalone multi-run (no consolidation/PDFs) |
| `consolidator.py` | AI combines multiple whimperized files | Standalone consolidation of existing files |

```bash
# Multi-run examples
python pipeline.py --runs 3 --groups zaltz-1a              # Easy multi-run
python consolidator.py --files file1.md file2.md          # Consolidate specific files
python multi_runner.py --runs 2 --groups zaltz-1a         # Multi-run only (no consolidation)
```

## 📁 Project Structure

```
whimperizer/
├── src/                     # Source code
│   ├── pipeline.py          # Main orchestrator (now with --runs support!)
│   ├── multi_pipeline.py    # Pipeline with consolidation options (NEW!)
│   ├── multi_runner.py      # Multi-run engine (NEW!)
│   ├── consolidator.py      # AI consolidation tool (NEW!)
│   ├── whimperizer.py       # AI transformation
│   ├── wimpy_pdf_generator.py # PDF generation
│   ├── bulk_downloader.py   # HTTP downloader
│   └── selenium_downloader.py # Browser automation
├── docs/                    # Documentation
│   ├── README.md            # Original detailed docs
│   ├── DOCUMENTATION.md     # Complete technical reference
│   ├── QUICK_REFERENCE.md   # Command cheat sheet
│   ├── MULTI_RUN_README.md  # Multi-run system guide (NEW!)
│   ├── MULTI_RUN_QUICK_REFERENCE.md # Multi-run commands (NEW!)
│   └── COMMIT_SUMMARY.md    # Recent improvements
├── config/                  # Configuration files
│   ├── config.yaml          # Main configuration (now with multi_run section!)
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
│   │   ├── *-normal-*.md    # Single-run outputs
│   │   ├── *-iterative-*.md # Multi-run outputs
│   │   └── *-consolidated-*.md # AI-consolidated best versions (NEW!)
│   ├── pdfs/                # Final PDFs
│   └── old/                 # Archive
├── logs/                    # Log files (gitignored)
└── resources/               # Fonts, images, templates
    ├── font/                # TTF font files
    └── backgrounds/         # Notebook paper templates
```

## 📖 Documentation

- **[🚀 Multi-Run System Guide](docs/MULTI_RUN_README.md)** - Complete multi-run documentation **(NEW!)**
- **[⚡ Multi-Run Quick Reference](docs/MULTI_RUN_QUICK_REFERENCE.md)** - Multi-run commands **(NEW!)**
- **[📚 Complete Documentation](docs/DOCUMENTATION.md)** - Full technical reference
- **[⚡ Quick Reference](docs/QUICK_REFERENCE.md)** - Common commands
- **[📋 Original README](docs/README.md)** - Detailed usage guide

## 🎯 Essential Commands

### Multi-Run Pipeline (Recommended!)
```bash
# First, change to src directory
cd src

# Multi-run with automatic consolidation (BEST RESULTS!)
python pipeline.py --runs 3 --groups zaltz-2a --verbose

# Multi-run with different models (configure in config.yaml)
python pipeline.py --runs 4 --groups zaltz-1a --provider openai

# Test with 2 runs first
python pipeline.py --runs 2 --groups zaltz-1a --dry-run
```

### Single-Run Pipeline (Classic)
```bash
# Change to src directory first
cd src

# Basic usage (uses default ../data/urls.csv)
python pipeline.py --groups zaltz-2a --verbose

# With specific AI provider
python pipeline.py --provider anthropic --groups zaltz-1a

# Skip download, use existing content
python pipeline.py --skip-download --groups zaltz-1a --verbose
```

### Consolidation Only
```bash
# Consolidate all files for a group (EASIEST METHOD!)
python consolidator.py --groups zaltz-1a

# Multiple groups at once
python consolidator.py --groups zaltz-1a zaltz-1b zaltz-2a

# All groups in directory
python consolidator.py --whimper-dir ../output/whimperized_content

# Consolidate specific files (full paths required)
python consolidator.py --files \
  "../output/whimperized_content/zaltz-1a-iterative-20250729_120000.md" \
  "../output/whimperized_content/zaltz-1a-iterative-20250729_130000.md"

# Test consolidation first
python consolidator.py --groups zaltz-1a --dry-run --verbose
```

### Step-by-Step
```bash
# Change to src directory first
cd src

# 1. Download content (defaults to ../data/urls.csv)
python selenium_downloader.py --groups zaltz-1a

# 2a. Single AI transformation
python whimperizer.py --groups zaltz-1a --verbose

# 2b. Multi-run AI transformation (better results!)
python multi_runner.py --runs 3 --groups zaltz-1a --verbose

# 2c. Consolidate multiple outputs
python consolidator.py --groups zaltz-1a --verbose

# 3. Generate PDF (automatically picks best available file)
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

### Multi-Run Configuration (NEW!)
Edit `config/config.yaml` to configure different models for each run:

```yaml
# Multi-run configuration for generating multiple AI outputs
multi_run:
  # Models for multiple runs - if more runs requested than specified, uses default model
  run_models:
    run_2_model:
      provider: "openai"
      model: "gpt-4o-mini"
      temperature: 0.8
    run_3_model:
      provider: "anthropic"
      model: "claude-3-sonnet-20240229"
      temperature: 0.7
    run_4_model:
      provider: "openai"
      model: "gpt-4.1-mini"
      temperature: 0.6
  
  # Consolidation settings
  consolidation:
    provider: "openai"
    model: "gpt-4.1-mini"
    temperature: 0.7
    max_tokens: 8000
```

### Main Configuration
Edit `config/config.yaml` to change AI providers, models, and processing options.

## 🏆 File Priority System

The system automatically picks the best available file for PDF generation:

1. **🥇 consolidated** files (from consolidator) - *AI-combined best parts*
2. **🥈 iterative** files (from multi-run) - *Multiple model outputs*  
3. **🥉 normal** files (from single run) - *Single model output*

**Within each type:** Newest timestamp wins (e.g., `20250729_153000` beats `20250729_120000`)

## 🔧 Recent Improvements

✅ **Multi-Run System** - Generate multiple AI outputs and consolidate the best parts  
✅ **Smart File Selection** - Automatically picks best file by type and timestamp  
✅ **Standalone Consolidation** - Combine any existing whimperized files  
✅ **Preserved Compatibility** - All single-run workflows still work exactly the same  
✅ **Character Handling** - Unicode characters automatically replaced  
✅ **Smart Typography** - Orphan header prevention, clean page breaks  
✅ **Hebrew Month Support** - Universal calendar system  
✅ **Organized Codebase** - Clean folder structure with proper gitignore  

## 🎨 Features

- **🔄 Multi-Run Pipeline**: Generate multiple outputs, automatically consolidate best parts
- **🤖 Multi-Provider AI**: OpenAI GPT-4, Claude 3, Gemini Pro with per-run configuration
- **🎯 Smart Consolidation**: AI picks best elements from multiple runs
- **📁 Intelligent File Selection**: Consolidated > Iterative > Normal, newest timestamp wins
- **🕸️ Advanced Web Scraping**: HTTP + Selenium browser automation  
- **📝 Handwritten PDFs**: Realistic handwriting effects with notebook backgrounds
- **✨ Smart Typography**: Professional page layout and spacing
- **⚡ Batch Processing**: Handle multiple documents simultaneously
- **🔧 Standalone Tools**: Each component can run independently

## 🚀 Multi-Run Workflows

```bash
# Quick multi-run test (2 runs, fast)
python pipeline.py --runs 2 --groups zaltz-1a

# Full multi-run production (4 different models)
python pipeline.py --runs 4 --groups zaltz-1a --verbose

# Multi-run but keep individual outputs (no consolidation)
python multi_pipeline.py --runs 3 --skip-consolidate --groups zaltz-1a

# Consolidate existing files from different times
python consolidator.py --files \
    zaltz-1a-whimperized-iterative-20250724_120000.md \
    zaltz-1a-whimperized-iterative-20250724_130000.md \
    zaltz-1a-whimperized-iterative-20250724_140000.md

# Just run multiple whimperizer instances (no consolidation, no PDFs)
python multi_runner.py --runs 3 --groups zaltz-1a --verbose

# Only run consolidation on existing files
python consolidator.py --groups zaltz-1a --verbose
```

## 🛠️ Development

```bash
# Run tests
python -m pytest tests/ -v

# Debug mode (from src/ directory)
python pipeline.py --verbose --dry-run

# Test multi-run without executing
python pipeline.py --runs 3 --groups zaltz-1a --dry-run

# View logs
tail -f logs/*.log
```

## 📄 License

Educational/personal use. Wimpy Kid assets © Jeff Kinney.

---

**Happy Whimperizing!** 🎉

*Now with multi-run AI consolidation for even better results!*