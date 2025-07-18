# Whimperizer - Complete Content Pipeline

A comprehensive Python toolkit for downloading web content, transforming it with AI into children's stories, and generating beautiful PDFs with handwritten-style text and Wimpy Kid aesthetics.

## 📁 Project Overview

This project contains several interconnected tools:
- **Content Downloaders** - Extract content from web pages (basic & Selenium)
- **Whimperizer AI** - Transform content using OpenAI/Claude/Gemini APIs
- **PDF Generator** - Create handwritten-style PDFs with Wimpy Kid resources
- **Resource Manager** - Handle fonts, images, and character templates

## 🚀 Quick Start

1. Set up your configuration:
   ```bash
   cp config.yaml.example config.yaml
   # Edit config.yaml with your API keys and preferred models
   ```

2. Prepare your URLs:
   ```bash
   # Create a CSV file with your URLs
   echo "url,group1,group2,line" > urls.csv
   echo "https://example.com/story1,zaltz,1a,1" >> urls.csv
   ```

3. Run the complete pipeline:
   ```bash
   python pipeline.py --urls urls.csv --groups zaltz-1a --provider anthropic
   ```

## Pipeline Usage

The pipeline orchestrates the complete process: Download → AI Transform → PDF Generation.

### Basic Commands

```bash
# Basic pipeline (uses selenium by default for better success rate)
python pipeline.py --urls urls.csv --groups zaltz-1a

# Specify AI model by editing config.yaml first, then:
python pipeline.py --urls urls.csv --provider openai --groups zaltz-1a

# Full pipeline with recommended settings
python pipeline.py --urls urls.csv --provider anthropic --groups zaltz-1a --headless --download-delay 3.0 --pdf-style notebook --verbose
```

### Handling Download Issues

If downloads are blocked (403 errors), try these approaches:

```bash
# Increase delay and use headless mode
python pipeline.py --urls urls.csv --groups zaltz-1a --download-delay 5.0 --headless

# Try basic downloader with CSV format
python pipeline.py --urls urls.csv --groups zaltz-1a --downloader basic --download-format csv

# Skip download if you already have content
python pipeline.py --skip-download --provider anthropic --groups zaltz-1a
```

### Processing Control

```bash
# Skip steps if you have existing content
python pipeline.py --skip-download --provider anthropic --groups zaltz-1a
python pipeline.py --skip-download --skip-whimperize --groups zaltz-1a  # PDFs only

# Process multiple groups
python pipeline.py --urls urls.csv --groups zaltz-1a zaltz-1b --provider openai

# Custom directories
python pipeline.py --urls urls.csv --groups zaltz-1a --download-dir content --whimper-dir stories --pdf-dir books
```

### AI Model Selection

Edit `config.yaml` to specify your preferred model:

```yaml
providers:
  openai:
    model: "gpt-4o"  # or gpt-4-turbo, o1-preview, o1-mini
  anthropic:
    model: "claude-3-sonnet-20240229"  # or claude-3-opus-20240229
  google:
    model: "gemini-pro"
```

Then run with your preferred provider:
```bash
python pipeline.py --urls urls.csv --provider openai --groups zaltz-1a
```

### Pipeline Options

| Option | Description | Default |
|--------|-------------|---------|
| `--urls` | Input URLs file (CSV/TXT) | `urls.txt` |
| `--groups` | Specific groups to process | All available |
| `--provider` | AI provider (openai/anthropic/google) | From config |
| `--downloader` | Downloader type (selenium/basic) | `selenium` |
| `--download-delay` | Delay between downloads (seconds) | `1.0` |
| `--headless` | Run browser in headless mode | `False` |
| `--pdf-style` | PDF style (notebook/blank) | `notebook` |
| `--verbose` | Detailed output | `False` |
| `--dry-run` | Show commands without executing | `False` |

## Manual Usage

### Installation
```bash
# Basic dependencies
pip install -r requirements.txt

# AI transformation features
pip install -r whimperizer_requirements.txt

# Selenium-based downloading (optional)
pip install -r selenium_requirements.txt
```

### Environment Setup
Create `.env` file:
```
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_claude_key_here  # Optional
GOOGLE_API_KEY=your_gemini_key_here     # Optional
```

### 🔥 **Complete Pipeline (Recommended)**
```bash
# One command does everything: Download → AI Transform → PDF
python pipeline.py --urls urls.txt --verbose

# With custom settings
python pipeline.py --urls urls.txt --provider anthropic --groups zaltz-1a --pdf-style notebook

# Skip steps (use existing content)
python pipeline.py --skip-download --groups zaltz-1a --verbose
```

### Manual Step-by-Step
```bash
# 1. Download content
python bulk_downloader.py --input urls.txt --format txt

# 2. Transform with AI
python whimperizer.py --groups zaltz-1a --verbose

# 3. Generate PDF
python wimpy_pdf_generator.py --input whimperized_content/zaltz-1a-whimperized-*.md --output zaltz-1a.pdf
```

## 🌐 Content Downloaders

### Basic HTML Downloader
```bash
python bulk_downloader.py [options]

Options:
  --input, -i FILE         URLs input file (default: urls.txt)
  --output-dir, -o DIR     Output directory (default: downloaded_content)
  --format, -f FORMAT      Output format: json, csv, txt (default: json)
  --delay, -d SECONDS      Delay between requests (default: 1.0)
  --help, -h              Show help message
```

**Target Elements:**
- Title: `.article-header__title`, `.js-article-title`
- Body: `.co_body`, `.article-body`

### Selenium Downloader
```bash
python selenium_downloader.py [options]

Options:
  --input, -i FILE         URLs input file (default: urls.txt)
  --output-dir, -o DIR     Output directory (default: downloaded_content)
  --format, -f FORMAT      Output format: json, csv, txt (default: json)
  --delay, -d SECONDS      Delay between requests (default: 1.0)
  --headless              Run browser in headless mode
  --help, -h              Show help message
```
Handles JavaScript-heavy sites with browser automation.

## 🤖 AI Transformation (Whimperizer)

Transform content into children's stories using multiple AI providers.

### Configuration (config.yaml)
```yaml
api:
  default_provider: "openai"
  providers:
    openai:
      model: "gpt-4"
      max_tokens: 4000
      temperature: 0.7
```

### Usage
```bash
# Use default provider (OpenAI)
python whimperizer.py

# Specify provider
python whimperizer.py --provider anthropic

# Process specific groups
python whimperizer.py --groups zaltz-1a
python whimperizer.py --groups zaltz-1a zaltz-1b  # Multiple groups

# List available groups first
python whimperizer.py --list-groups

# List available AI providers
python whimperizer.py --list-providers

# Debug/verbose output
python whimperizer.py --verbose
python whimperizer.py --log-level DEBUG

# Test with single document (workaround)
cp downloaded_content/zaltz-1a-1.0.txt downloaded_content/test-single-1.0.txt
python whimperizer.py --groups test-single --verbose
```

### All Whimperizer Options
```bash
python whimperizer.py [options]

Options:
  --config CONFIG           Configuration file (default: config.yaml)
  --groups GROUP [GROUP...] Process specific groups (e.g., zaltz-1a)
  --list-groups            List all available groups
  --provider {openai,anthropic,google}  Override AI provider
  --list-providers         Show available AI providers
  --log-level {DEBUG,INFO,WARNING,ERROR}  Set logging detail
  --verbose, -v            Enable debug logging
  --help, -h              Show help message
```

### File Organization & Groups

Files must be named: `{group1}-{group2}-{line}.txt`

**Example files:**
```
downloaded_content/
├── zaltz-1a-1.0.txt    # Group1: zaltz, Group2: 1a, Line: 1.0
├── zaltz-1a-2.0.txt    # Group1: zaltz, Group2: 1a, Line: 2.0
├── zaltz-1a-12.0.txt   # Group1: zaltz, Group2: 1a, Line: 12.0
├── zaltz-1b-1.0.txt    # Group1: zaltz, Group2: 1b, Line: 1.0
└── chabad-stories-1.txt # Group1: chabad, Group2: stories, Line: 1
```

**Group Processing:**
- Groups are specified as `{group1}-{group2}` (e.g., `zaltz-1a`)
- All files in a group are combined in line number order
- Each group produces one whimperized output file

**Output:**
```
whimperized_content/
├── zaltz-1a-whimperized.txt     # Combined content from all zaltz-1a-*.txt files
├── zaltz-1b-whimperized.txt     # Combined content from all zaltz-1b-*.txt files
└── chabad-stories-whimperized.txt
```

## 📄 PDF Generation

Create handwritten-style PDFs with Wimpy Kid aesthetics.

### Basic Usage
```bash
python wimpy_pdf_generator.py --input story.txt --output story.pdf
```

### All PDF Generator Options
```bash
python wimpy_pdf_generator.py [options]

Options:
  --input, -i FILE         Input text/markdown file
  --output, -o FILE        Output PDF file (default: output.pdf)
  --style STYLE           Page style: notebook, blank (default: notebook)
  --font FONT             Font name (auto-detects Wimpy Kid fonts)
  --background BG         Background template name
  --resources DIR         Resources directory (default: ./resources)
  --batch                 Process multiple input files
  --verbose               Enable verbose output
  --help, -h              Show help message
```

### Advanced Examples
```bash
# Custom styling
python wimpy_pdf_generator.py \
  --input story.txt \
  --style notebook \
  --font "Wimpy Kid" \
  --background lined_paper \
  --resources ./resources

# Batch process all whimperized files
python wimpy_pdf_generator.py \
    --input whimperized_content/*.txt \
    --batch \
    --verbose
```

### Features
- **Handwritten Effects**: Text jitter, rotation, natural spacing
- **Wimpy Kid Fonts**: Auto-detection of character fonts
- **Background Templates**: Notebook paper, blank pages
- **Markdown Support**: Headers, bold, italic formatting

## 🔥 Complete Pipeline Script

**New!** The `pipeline.py` script automates the entire process: Download → AI Transform → PDF Generation.

### Basic Usage
```bash
# Complete pipeline with defaults
python pipeline.py --urls urls.txt

# With verbose output
python pipeline.py --urls urls.txt --verbose

# Process specific groups only
python pipeline.py --urls urls.txt --groups zaltz-1a zaltz-1b

# Skip steps (use existing content)
python pipeline.py --skip-download --groups zaltz-1a --verbose
```

### All Pipeline Options
```bash
python pipeline.py [options]

Input/Output:
  --urls, -u FILE          URLs input file (default: urls.txt)
  --download-dir DIR       Downloaded content directory (default: downloaded_content)
  --whimper-dir DIR        Whimperized content directory (default: whimperized_content)
  --pdf-dir DIR            PDF output directory (default: pdfs)

Pipeline Control:
  --skip-download          Skip download step (use existing content)
  --skip-whimperize        Skip AI transformation step
  --skip-pdf               Skip PDF generation step
  --list-groups            List available groups and exit
  --dry-run                Show what would be done without executing

Download Options:
  --downloader {basic,selenium}  Downloader type (default: basic)
  --download-format {json,csv,txt}  Output format (default: txt)
  --download-delay SECONDS  Delay between downloads (default: 1.0)
  --headless               Run selenium in headless mode

AI/Whimperizer Options:
  --provider {openai,anthropic,google}  AI provider
  --groups GROUP [GROUP...]  Process specific groups (e.g., zaltz-1a)
  --config FILE            Configuration file (default: config.yaml)

PDF Generation Options:
  --pdf-style {notebook,blank}  Page style (default: notebook)
  --pdf-font FONT          Font name (auto-detects Wimpy Kid fonts)
  --pdf-background BG      Background template
  --resources-dir DIR      Resources directory (default: resources)

General Options:
  --verbose, -v            Verbose output
  --log-level {DEBUG,INFO,WARNING,ERROR}  Logging level
  --help, -h               Show help message
```

### Pipeline Examples
```bash
# Basic pipeline
python pipeline.py --urls urls.txt

# Custom AI provider and specific groups
python pipeline.py --urls urls.txt --provider anthropic --groups zaltz-1a --verbose

# Use selenium downloader with custom settings
python pipeline.py --urls urls.txt --downloader selenium --headless --download-delay 2.0

# Custom output directories
python pipeline.py --urls urls.txt --download-dir content --whimper-dir stories --pdf-dir books

# Skip download, process existing content
python pipeline.py --skip-download --groups zaltz-1a --pdf-style notebook

# Generate PDFs only (skip download and whimperize)
python pipeline.py --skip-download --skip-whimperize --pdf-dir final_pdfs

# Test run (show commands without executing)
python pipeline.py --urls urls.txt --dry-run
```

## 📚 Resources Directory

```
resources/
├── font/                    # TTF/OTF font files
├── Blank Pages/             # Background templates
├── Character Expressions/   # Wimpy Kid character art
├── Speech Bubbles/          # Comic-style bubbles
├── Greg Templates/          # Main character assets
├── Rodrick Templates/       # Brother character assets
└── Logos/                  # Branding elements
```

## 🧪 Testing & Development

### Test Single Document
```bash
# Copy one file to create test group
cp downloaded_content/zaltz-1a-1.0.txt downloaded_content/test-single-1.0.txt

# Process test group with verbose output
python whimperizer.py --groups test-single --verbose

# Check output
cat whimperized_content/test-single-whimperized-*.md
```

### Test Content Extraction
```bash
python test_extractor.py --url "https://example.com"
```

### Complete Pipeline Scripts
```bash
# 🔥 NEW: Complete automated pipeline
python pipeline.py --urls urls.txt --verbose

# Manual step-by-step
python bulk_downloader.py --input urls.txt
python whimperizer.py --list-groups
python whimperizer.py --groups test-single --verbose
python wimpy_pdf_generator.py --input whimperized_content/*.txt --batch
```

## 📊 Output Formats

### JSON (bulk_downloader.py)
```json
[{
  "url": "https://example.com/article",
  "title": "Article Title",
  "body": "Content...",
  "status": "success"
}]
```

### CSV
```csv
URL,Title,Body,Status,Error
https://example.com,Title,Content,success,
```

## 🎨 Customization

### AI Prompts (`whimperizer_prompt.txt`)
This file contains the full conversation history that controls AI transformations:

```bash
# View current prompts
cat whimperizer_prompt.txt

# Edit prompts (JSON format)
# Each message has "role" (user/assistant) and "content"
```

**Key sections to modify:**
- **Style instructions**: "Diary of a Wimpy Kid" format requirements
- **Cultural guidelines**: Chabad-specific vocabulary and references  
- **Examples**: Good/bad transformation samples
- **Target audience**: Age-appropriate language and topics

**Example modifications:**
```json
{
  "role": "user", 
  "content": "Always include more physical comedy and mishaps in every entry"
}
```

### PDF Styling
Modify text styles, fonts, and layouts in `wimpy_pdf_generator.py`:
- **Handwriting effects**: Text jitter, rotation, spacing
- **Font selection**: Auto-detection of Wimpy Kid fonts
- **Background templates**: Notebook paper, blank pages

## 🚨 Troubleshooting

### Common Issues

**Missing API Keys**
```
Error: OPENAI_API_KEY not set
```
→ Create `.env` file with API key

**Font Issues**
```
Warning: No suitable fonts found
```
→ Add TTF files to `resources/font/`

**Selenium Issues**
```
WebDriverException
```
→ Install ChromeDriver or use `--headless`

### Debug Mode
```bash
# Individual tools
python whimperizer.py --debug
python wimpy_pdf_generator.py --verbose

# Pipeline debug
python pipeline.py --urls urls.txt --verbose --dry-run
```

## 📈 Performance Tips

1. **Use Pipeline Script**: `pipeline.py` is optimized for efficiency
2. **Batch Processing**: Process multiple files together
3. **API Monitoring**: Check logs for usage tracking
4. **Memory Management**: Use smaller fonts for large docs
5. **Parallel Processing**: Run multiple instances for different groups
6. **Skip Steps**: Use `--skip-download` or `--skip-whimperize` to save time

## 🤝 Contributing

1. Fork repository
2. Create feature branch
3. Submit pull request

## 📄 License

Educational/personal use. Wimpy Kid assets © Jeff Kinney.

---

**Happy Whimperizing!** 🎉
