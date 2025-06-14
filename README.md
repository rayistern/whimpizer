# Whimperizer - Complete Content Pipeline

A comprehensive Python toolkit for downloading web content, transforming it with AI into children's stories, and generating beautiful PDFs with handwritten-style text and Wimpy Kid aesthetics.

## 📁 Project Overview

This project contains several interconnected tools:
- **Content Downloaders** - Extract content from web pages (basic & Selenium)
- **Whimperizer AI** - Transform content using OpenAI/Claude/Gemini APIs
- **PDF Generator** - Create handwritten-style PDFs with Wimpy Kid resources
- **Resource Manager** - Handle fonts, images, and character templates

## 🚀 Quick Start

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

### Basic Usage
```bash
# 1. Download content
python bulk_downloader.py --input urls.txt --format json

# 2. Transform with AI
python whimperizer.py

# 3. Generate PDF
python wimpy_pdf_generator.py --input whimperized_content/story.txt
```

## 🌐 Content Downloaders

### Basic HTML Downloader
```bash
python bulk_downloader.py [options]
```
- `--input` / `-i`: URLs file (default: urls.txt)
- `--output-dir` / `-o`: Output directory (default: downloaded_content)
- `--format` / `-f`: json, csv, or txt (default: json)
- `--delay` / `-d`: Delay between requests (default: 1.0s)

**Target Elements:**
- Title: `.article-header__title`, `.js-article-title`
- Body: `.co_body`, `.article-body`

### Selenium Downloader
```bash
python selenium_downloader.py [options]
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

### Advanced Options
```bash
python wimpy_pdf_generator.py \
  --input story.txt \
  --style notebook \
  --font "Wimpy Kid" \
  --background lined_paper \
  --resources ./resources
```

### Features
- **Handwritten Effects**: Text jitter, rotation, natural spacing
- **Wimpy Kid Fonts**: Auto-detection of character fonts
- **Background Templates**: Notebook paper, blank pages
- **Markdown Support**: Headers, bold, italic formatting

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

## 🔧 Command Line Tools

### Content Test
```bash
python test_extractor.py --url "https://example.com"
```

### Complete Pipeline
```bash
python bulk_downloader.py --input urls.txt
python whimperizer.py
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

### AI Prompts
Edit `whimperizer_prompt.txt` for custom transformations.

### PDF Styling
Modify text styles, fonts, and layouts in `wimpy_pdf_generator.py`.

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
python whimperizer.py --debug
python wimpy_pdf_generator.py --verbose
```

## 📈 Performance Tips

1. **Batch Processing**: Process multiple files together
2. **API Monitoring**: Check logs for usage tracking
3. **Memory Management**: Use smaller fonts for large docs
4. **Parallel Processing**: Run multiple instances for different groups

## 🤝 Contributing

1. Fork repository
2. Create feature branch
3. Submit pull request

## 📄 License

Educational/personal use. Wimpy Kid assets © Jeff Kinney.

---

**Happy Whimperizing!** 🎉
