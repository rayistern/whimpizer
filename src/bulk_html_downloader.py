#!/usr/bin/env python3
"""
Bulk HTML Downloader and Content Extractor
Downloads HTML files from URLs and extracts specific content fields.
"""

import requests
from bs4 import BeautifulSoup
import time
import os
import json
import csv
from urllib.parse import urlparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BulkHTMLDownloader:
    def __init__(self, input_file='../data/urls.csv', output_dir='../output/downloaded_content', delay=1):
        self.input_file = input_file
        self.output_dir = output_dir
        self.delay = delay  # Delay between requests to be respectful
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Target CSS selectors
        self.title_selector = '.article-header__title.js-article-title.js-page-title'
        self.body_selector = '.co_body.article-body.cf'
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
    def read_urls(self):
        """Read URLs from input file"""
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            logger.info(f"Loaded {len(urls)} URLs from {self.input_file}")
            return urls
        except FileNotFoundError:
            logger.error(f"Input file {self.input_file} not found")
            return []
    
    def download_html(self, url):
        """Download HTML content from URL"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Failed to download {url}: {e}")
            return None
    
    def extract_content(self, html, url):
        """Extract title and body content from HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract title
            title_element = soup.select_one(self.title_selector)
            title = title_element.get_text(strip=True) if title_element else "No title found"
            
            # Extract body content
            body_element = soup.select_one(self.body_selector)
            body = body_element.get_text(strip=True) if body_element else "No body content found"
            
            return {
                'url': url,
                'title': title,
                'body': body,
                'status': 'success'
            }
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return {
                'url': url,
                'title': "Error extracting title",
                'body': "Error extracting body",
                'status': 'error',
                'error': str(e)
            }
    
    def save_content(self, content_data, format='json'):
        """Save extracted content to files"""
        if format == 'json':
            self.save_as_json(content_data)
        elif format == 'csv':
            self.save_as_csv(content_data)
        elif format == 'txt':
            self.save_as_txt(content_data)
        else:
            logger.error(f"Unsupported format: {format}")
    
    def save_as_json(self, content_data):
        """Save content as JSON file"""
        output_file = os.path.join(self.output_dir, 'extracted_content.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(content_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Content saved as JSON: {output_file}")
    
    def save_as_csv(self, content_data):
        """Save content as CSV file"""
        output_file = os.path.join(self.output_dir, 'extracted_content.csv')
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['URL', 'Title', 'Body', 'Status', 'Error'])
            for item in content_data:
                writer.writerow([
                    item['url'],
                    item['title'],
                    item['body'][:1000] + '...' if len(item['body']) > 1000 else item['body'],  # Truncate long body text
                    item['status'],
                    item.get('error', '')
                ])
        logger.info(f"Content saved as CSV: {output_file}")
    
    def save_as_txt(self, content_data):
        """Save content as separate text files"""
        for i, item in enumerate(content_data, 1):
            if item['status'] == 'success':
                # Create safe filename from URL
                parsed_url = urlparse(item['url'])
                filename = f"{i:03d}_{parsed_url.netloc}_{parsed_url.path.replace('/', '_')}.txt"
                filename = "".join(c for c in filename if c.isalnum() or c in '._-')[:100]  # Sanitize filename
                
                output_file = os.path.join(self.output_dir, filename)
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(f"URL: {item['url']}\n")
                    f.write(f"Title: {item['title']}\n")
                    f.write("-" * 50 + "\n")
                    f.write(item['body'])
        logger.info(f"Content saved as individual text files in: {self.output_dir}")
    
    def run(self, output_format='json'):
        """Main execution method"""
        logger.info("Starting bulk HTML download and extraction")
        
        urls = self.read_urls()
        if not urls:
            logger.error("No URLs to process")
            return
        
        extracted_data = []
        
        for i, url in enumerate(urls, 1):
            logger.info(f"Processing {i}/{len(urls)}: {url}")
            
            # Download HTML
            html_content = self.download_html(url)
            if html_content:
                # Extract content
                content = self.extract_content(html_content, url)
                extracted_data.append(content)
                
                logger.info(f"Extracted: {content['title'][:50]}...")
            else:
                extracted_data.append({
                    'url': url,
                    'title': "Failed to download",
                    'body': "Failed to download",
                    'status': 'download_failed'
                })
            
            # Be respectful with delays
            if i < len(urls):
                time.sleep(self.delay)
        
        # Save extracted content
        self.save_content(extracted_data, output_format)
        
        # Print summary
        successful = sum(1 for item in extracted_data if item['status'] == 'success')
        logger.info(f"Extraction complete: {successful}/{len(urls)} successful")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Bulk HTML downloader and content extractor')
    parser.add_argument('--input', '-i', default='../data/urls.csv', help='Input file with URLs (default: ../data/urls.csv)')
    parser.add_argument('--output-dir', '-o', default='../output/downloaded_content', help='Output directory (default: ../output/downloaded_content)')
    parser.add_argument('--format', '-f', choices=['json', 'csv', 'txt'], default='json', help='Output format (default: json)')
    parser.add_argument('--delay', '-d', type=float, default=1.0, help='Delay between requests in seconds (default: 1.0)')
    
    args = parser.parse_args()
    
    downloader = BulkHTMLDownloader(
        input_file=args.input,
        output_dir=args.output_dir,
        delay=args.delay
    )
    
    downloader.run(output_format=args.format)

if __name__ == "__main__":
    main() 