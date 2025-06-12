# Bulk HTML Downloader

A Python script to download HTML files in bulk from a list of URLs and extract specific content fields.

## Features

- Downloads HTML content from multiple URLs
- Extracts article titles and body content using CSS selectors
- Supports multiple output formats (JSON, CSV, text files)
- Respectful delays between requests
- Error handling and logging
- Resume capability

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a URLs file (default: `urls.txt`) with one URL per line:
```
https://example.com/article1
https://example.com/article2
# Comments start with #
```

## Usage

### Basic usage:
```bash
python bulk_downloader.py
```

### Advanced options:
```bash
python bulk_downloader.py --input my_urls.txt --output-dir results --format csv --delay 2.0
```

### Command line options:
- `--input` / `-i`: Input file with URLs (default: urls.txt)
- `--output-dir` / `-o`: Output directory (default: downloaded_content)
- `--format` / `-f`: Output format - json, csv, or txt (default: json)
- `--delay` / `-d`: Delay between requests in seconds (default: 1.0)

## Target Fields

The script extracts these specific fields from HTML:
- **Title**: Elements with classes `article-header__title js-article-title js-page-title`
- **Body**: Elements with classes `co_body article-body cf`

## Output Formats

### JSON
Single file with all extracted content:
```json
[
  {
    "url": "https://example.com/article1",
    "title": "Article Title",
    "body": "Article content...",
    "status": "success"
  }
]
```

### CSV  
Spreadsheet format with columns: URL, Title, Body, Status, Error

### TXT
Individual text files for each successful extraction

## Example

1. Add URLs to `urls.txt`:
```
https://www.chabad.org/library/article_cdo/aid/2828044/jewish/Living-Under-Communism.htm
https://www.chabad.org/library/article_cdo/aid/2828045/jewish/First-Mission-Hide-the-Children-From-the-Neighbors.htm
```

2. Run the script:
```bash
python bulk_downloader.py --format json
```

3. Check the `downloaded_content/` directory for results.

## Notes

- The script includes a 1-second delay between requests by default to be respectful to servers
- Failed downloads are logged and included in output with error status
- Large body content is truncated in CSV format for readability
- The script uses a standard User-Agent string to avoid blocking