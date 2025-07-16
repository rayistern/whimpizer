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
import pandas as pd
import random

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BulkHTMLDownloader:
    def __init__(self, input_file='urls.csv', output_dir='downloaded_content', delay=1):
        self.input_file = input_file
        self.output_dir = output_dir
        self.delay = delay  # Delay between requests to be respectful
        self.session = requests.Session()
        
        # Rotate between different realistic User-Agent strings
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
        ]
        
        # Set realistic headers
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })
        
        # Target CSS selectors
        self.title_selector = '.article-header__title.js-article-title.js-page-title'
        self.body_selector = '.co_body.article-body.cf'
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
    def read_csv_urls(self):
        """Read URLs from CSV file with columns: line, value, group1, group2"""
        try:
            df = pd.read_csv(self.input_file)
            
            # Filter out rows where 'value' (URL) is empty or NaN
            df = df.dropna(subset=['value'])
            df = df[df['value'].str.strip() != '']
            
            # Convert to list of dictionaries
            url_data = []
            for _, row in df.iterrows():
                url_data.append({
                    'line': row['line'],
                    'url': row['value'].strip(),
                    'group1': row['group1'],
                    'group2': row['group2']
                })
            
            logger.info(f"Loaded {len(url_data)} URLs from {self.input_file}")
            return url_data
        except FileNotFoundError:
            logger.error(f"Input file {self.input_file} not found")
            return []
        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            return []
    
    def download_html(self, url, retries=3):
        """Download HTML content from URL with retry logic"""
        for attempt in range(retries):
            try:
                # Rotate User-Agent for each request
                self.session.headers.update({
                    'User-Agent': random.choice(self.user_agents),
                    'Referer': 'https://www.google.com/',  # Add referer to look more natural
                })
                
                # Add some randomness to delay to look more human
                if attempt > 0:
                    delay = self.delay + random.uniform(0.5, 2.0)
                    logger.info(f"Retrying in {delay:.1f} seconds...")
                    time.sleep(delay)
                
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                logger.info(f"Successfully downloaded: {url}")
                return response.text
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 403:
                    logger.warning(f"403 Forbidden (attempt {attempt + 1}/{retries}): {url}")
                    if attempt < retries - 1:
                        # Exponential backoff for 403 errors
                        delay = (2 ** attempt) * self.delay + random.uniform(1, 3)
                        logger.info(f"Waiting {delay:.1f} seconds before retry...")
                        time.sleep(delay)
                    continue
                else:
                    logger.error(f"HTTP Error {e.response.status_code} for {url}: {e}")
                    break
            except requests.RequestException as e:
                logger.error(f"Request failed (attempt {attempt + 1}/{retries}) for {url}: {e}")
                if attempt < retries - 1:
                    time.sleep(self.delay + random.uniform(0.5, 1.5))
                    
        logger.error(f"Failed to download after {retries} attempts: {url}")
        return None
    
    def extract_content(self, html, url_data):
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
                'line': url_data['line'],
                'url': url_data['url'],
                'group1': url_data['group1'],
                'group2': url_data['group2'],
                'title': title,
                'body': body,
                'status': 'success'
            }
        except Exception as e:
            logger.error(f"Error extracting content from {url_data['url']}: {e}")
            return {
                'line': url_data['line'],
                'url': url_data['url'],
                'group1': url_data['group1'],
                'group2': url_data['group2'],
                'title': "Error extracting title",
                'body': "Error extracting body",
                'status': 'error',
                'error': str(e)
            }
    
    def create_filename(self, content_data, extension='txt'):
        """Create filename using pattern: group1-group2-line.extension"""
        group1 = str(content_data['group1']).replace('/', '_').replace('\\', '_')
        group2 = str(content_data['group2']).replace('/', '_').replace('\\', '_')
        line = str(content_data['line'])
        
        filename = f"{group1}-{group2}-{line}.{extension}"
        # Sanitize filename
        filename = "".join(c for c in filename if c.isalnum() or c in '._-')
        return filename
    
    def save_content(self, content_data, format='json'):
        """Save extracted content to files"""
        if format == 'json':
            self.save_as_json(content_data)
        elif format == 'csv':
            self.save_as_csv(content_data)
        elif format == 'txt':
            self.save_as_individual_txt(content_data)
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
            writer.writerow(['Line', 'Group1', 'Group2', 'URL', 'Title', 'Body', 'Status', 'Error'])
            for item in content_data:
                writer.writerow([
                    item['line'],
                    item['group1'],
                    item['group2'],
                    item['url'],
                    item['title'],
                    item['body'][:1000] + '...' if len(item['body']) > 1000 else item['body'],  # Truncate long body text
                    item['status'],
                    item.get('error', '')
                ])
        logger.info(f"Content saved as CSV: {output_file}")
    
    def save_as_individual_txt(self, content_data):
        """Save content as separate text files with custom naming"""
        successful_count = 0
        for item in content_data:
            if item['status'] == 'success':
                filename = self.create_filename(item, 'txt')
                output_file = os.path.join(self.output_dir, filename)
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(f"Line: {item['line']}\n")
                    f.write(f"Group1: {item['group1']}\n")
                    f.write(f"Group2: {item['group2']}\n")
                    f.write(f"URL: {item['url']}\n")
                    f.write(f"Title: {item['title']}\n")
                    f.write("-" * 50 + "\n")
                    f.write(item['body'])
                
                logger.info(f"Saved: {filename}")
                successful_count += 1
        
        logger.info(f"Content saved as {successful_count} individual text files in: {self.output_dir}")
    
    def run(self, output_format='txt'):
        """Main execution method"""
        logger.info("Starting bulk HTML download and extraction")
        
        url_data_list = self.read_csv_urls()
        if not url_data_list:
            logger.error("No URLs to process")
            return
        
        extracted_data = []
        
        for i, url_data in enumerate(url_data_list, 1):
            logger.info(f"Processing {i}/{len(url_data_list)} (Line {url_data['line']}): {url_data['url']}")
            
            # Download HTML
            html_content = self.download_html(url_data['url'])
            if html_content:
                # Extract content
                content = self.extract_content(html_content, url_data)
                extracted_data.append(content)
                
                logger.info(f"Extracted: {content['title'][:50]}...")
            else:
                extracted_data.append({
                    'line': url_data['line'],
                    'url': url_data['url'],
                    'group1': url_data['group1'],
                    'group2': url_data['group2'],
                    'title': "Failed to download",
                    'body': "Failed to download",
                    'status': 'download_failed'
                })
            
            # Be respectful with delays (with some randomness)
            if i < len(url_data_list):
                delay = self.delay + random.uniform(0.2, 0.8)
                logger.info(f"Waiting {delay:.1f} seconds...")
                time.sleep(delay)
        
        # Save extracted content
        self.save_content(extracted_data, output_format)
        
        # Print summary
        successful = sum(1 for item in extracted_data if item['status'] == 'success')
        failed = sum(1 for item in extracted_data if item['status'] == 'download_failed')
        errors = sum(1 for item in extracted_data if item['status'] == 'error')
        
        logger.info(f"Extraction complete: {successful}/{len(url_data_list)} successful, {failed} download failed, {errors} extraction errors")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Bulk HTML downloader and content extractor')
    parser.add_argument('--input', '-i', default='urls.csv', help='Input CSV file with URLs (default: urls.csv)')
    parser.add_argument('--output-dir', '-o', default='downloaded_content', help='Output directory (default: downloaded_content)')
    parser.add_argument('--format', '-f', choices=['json', 'csv', 'txt'], default='txt', help='Output format (default: txt)')
    parser.add_argument('--delay', '-d', type=float, default=2.0, help='Base delay between requests in seconds (default: 2.0)')
    
    args = parser.parse_args()
    
    downloader = BulkHTMLDownloader(
        input_file=args.input,
        output_dir=args.output_dir,
        delay=args.delay
    )
    
    downloader.run(output_format=args.format)

if __name__ == "__main__":
    main() 