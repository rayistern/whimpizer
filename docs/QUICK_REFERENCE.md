# Whimperizer Quick Reference

## Essential Commands

### Complete Pipeline (Recommended)
```bash
# Basic usage
python src/pipeline.py --urls data/urls.csv --verbose

# With specific AI provider
python src/pipeline.py --urls data/urls.csv --provider anthropic --groups zaltz-1a

# Skip download, use existing content
python src/pipeline.py --skip-download --groups zaltz-1a --verbose
```

### Manual Step-by-Step
```bash
# 1. Download content
python src/bulk_downloader.py --input data/urls.csv --format txt

# 2. Transform with AI
python src/whimperizer.py --groups zaltz-1a --verbose

# 3. Generate PDF
python src/wimpy_pdf_generator.py --input output/whimperized_content/zaltz-1a-*.md --output output/zaltz-1a.pdf
```

## File Formats

### URLs CSV
```csv
url,group1,group2,line
https://example.com/story1,zaltz,1a,1
https://example.com/story2,zaltz,1a,2
```

### Environment Variables
```bash
# .env file (in project root)
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_claude_key
GOOGLE_API_KEY=your_gemini_key
```

## Configuration Quick Settings

### config/config.yaml - AI Models
```yaml
api:
  default_provider: "openai"  # openai | anthropic | google
  providers:
    openai:
      model: "o3"           # o3 | gpt-4o | gpt-4-turbo
    anthropic:
      model: "claude-3-sonnet-20240229"
    google:
      model: "gemini-pro"
```

### PDF Settings (in src/wimpy_pdf_generator.py)
```python
FONT_SIZES = {
    'paragraph': 18,    # Main text size
    'h2': 18,          # Header size
    'dialogue': 18,    # Speech size
}

LINE_SPACING = {
    'paragraph': 1.52,  # Line spacing multiplier
    'h2': 1.1,
    'dialogue': 1.52,
}
```

## Common Options

### Pipeline Options
| Flag | Purpose | Example |
|------|---------|---------|
| `--urls` | Input URLs file | `--urls input.csv` |
| `--groups` | Specific groups | `--groups zaltz-1a zaltz-1b` |
| `--provider` | AI provider | `--provider anthropic` |
| `--skip-download` | Use existing content | `--skip-download` |
| `--verbose` | Detailed output | `--verbose` |

### Downloader Options
| Flag | Purpose | Example |
|------|---------|---------|
| `--input` | URLs file | `--input urls.csv` |
| `--format` | Output format | `--format txt` |
| `--delay` | Request delay | `--delay 2.0` |
| `--headless` | Selenium headless | `--headless` |

## File Organization

```
project/
├── src/                     # Source code
├── config/                  # Configuration files
│   └── config.yaml
├── data/                    # Input data
│   └── urls.csv
├── output/                  # Generated content
│   ├── downloaded_content/
│   │   └── group1-group2-line.txt
│   ├── whimperized_content/
│   │   └── group1-group2-whimperized-timestamp.md
│   └── pdfs/
│       └── group1-group2-timestamp.pdf
├── logs/                    # Log files
└── .env                     # Environment variables
```

## Troubleshooting Quick Fixes

### Font Issues
```bash
# Add TTF fonts to resources/font/
# Avoid OTF files - use TTF instead
```

### API Key Issues
```bash
# Create .env file with API keys
echo "OPENAI_API_KEY=your_key" > .env
```

### Character Rendering
```bash
# Recent versions handle automatically
# Unicode characters replaced: • → *, ‐ → -, — → --
```

### Selenium Issues
```bash
# Use headless mode
python selenium_downloader.py --headless

# Or install ChromeDriver manually
```

## Testing Commands

```bash
# Test single document
cp output/downloaded_content/large-file.txt output/downloaded_content/test-single-1.0.txt
python src/pipeline.py --groups test-single --verbose

# Test PDF generation only
python src/wimpy_pdf_generator.py --input data/input.md --output output/test.pdf --verbose

# Debug AI transformation
python src/whimperizer.py --groups test-single --verbose --log-level DEBUG
```

## Resource Structure

```
resources/
├── font/                    # TTF fonts only
│   ├── WimpyKid-Regular.ttf
│   └── WimpyKid-Dialogue.ttf
├── backgrounds/             # PNG/JPG backgrounds
│   └── single_page.png     # Notebook paper
└── characters/              # Character images
```

## Performance Tips

1. **Use pipeline.py** - Most efficient approach
2. **Process smaller groups** - Better for testing
3. **Use --skip-download** - When iterating on AI/PDF
4. **Choose faster models** - gpt-4o > claude > o3 for speed
5. **Cache downloads** - Avoid re-downloading content

## Recent Improvements (Latest Version)

✅ **Character replacement** - No more Unicode rendering issues  
✅ **Orphan header prevention** - Professional page breaks  
✅ **Smart line spacing** - Proper paragraph and list formatting  
✅ **Hebrew month support** - Universal calendar system  
✅ **Clean page starts** - No blank lines at page tops  

## Common Patterns

### Process Multiple Groups
```bash
python src/pipeline.py --urls data/urls.csv --groups zaltz-1a zaltz-1b zaltz-1c
```

### Custom Directories
```bash
python src/pipeline.py --download-dir content --whimper-dir stories --pdf-dir books
```

### Selenium with Custom Settings
```bash
python src/pipeline.py --downloader selenium --headless --download-delay 3.0
```

### Debug Mode
```bash
python src/pipeline.py --verbose --dry-run  # Show commands without executing
```