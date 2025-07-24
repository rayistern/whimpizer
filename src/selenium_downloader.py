#!/usr/bin/env python3
"""
Bulk HTML Downloader using Selenium WebDriver
Uses a real browser to bypass anti-bot protection.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup
import time
import os
import json
import csv
import logging
import pandas as pd
import random

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BulkHTMLDownloaderSelenium:
    def __init__(self, input_file='../data/urls.csv', output_dir='../output/downloaded_content', delay=3, headless=False):
        self.input_file = input_file
        self.output_dir = output_dir
        self.delay = delay
        self.headless = headless
        self.driver = None
        
        # Target CSS selectors
        self.title_selector = '.article-header__title.js-article-title.js-page-title'
        self.body_selector = '.co_body.article-body.cf'
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
    def setup_driver(self):
        """Setup Chrome WebDriver with anti-detection options"""
        try:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument("--headless")
            
            # Anti-detection options
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            
            # Set a realistic window size
            chrome_options.add_argument("--window-size=1920,1080")
            
            # User agent
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            
            # Execute script to remove webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("Chrome WebDriver initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup WebDriver: {e}")
            logger.error("Make sure you have Chrome and ChromeDriver installed")
            return False
    
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
    
    def download_html(self, url, timeout=30):
        """Download HTML content using Selenium"""
        try:
            logger.info(f"Loading: {url}")
            self.driver.get(url)
            
            # Wait for the page to load and check for the title element
            try:
                WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, self.title_selector))
                )
                logger.info("Page loaded successfully")
            except TimeoutException:
                logger.warning("Title element not found, but continuing with page source")
            
            # Get the page source
            html_content = self.driver.page_source
            
            # Check if we got blocked (common blocking indicators)
            if "403" in self.driver.title or "Forbidden" in self.driver.title:
                logger.error("Detected 403 Forbidden page")
                return None
            
            if len(html_content) < 1000:  # Suspiciously small page
                logger.warning("Received suspiciously small page content")
                return None
                
            return html_content
            
        except WebDriverException as e:
            logger.error(f"WebDriver error for {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error for {url}: {e}")
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
    
    def run(self):
        """Main execution method"""
        logger.info("Starting bulk HTML download with Selenium")
        
        # Setup WebDriver
        if not self.setup_driver():
            logger.error("Failed to initialize WebDriver. Exiting.")
            return
        
        try:
            url_data_list = self.read_csv_urls()
            if not url_data_list:
                logger.error("No URLs to process")
                return
            
            extracted_data = []
            
            for i, url_data in enumerate(url_data_list, 1):
                logger.info(f"Processing {i}/{len(url_data_list)} (Line {url_data['line']})")
                
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
                
                # Be respectful with delays
                if i < len(url_data_list):
                    delay = self.delay + random.uniform(0.5, 1.5)
                    logger.info(f"Waiting {delay:.1f} seconds...")
                    time.sleep(delay)
            
            # Save extracted content
            self.save_as_individual_txt(extracted_data)
            
            # Print summary
            successful = sum(1 for item in extracted_data if item['status'] == 'success')
            failed = sum(1 for item in extracted_data if item['status'] == 'download_failed')
            errors = sum(1 for item in extracted_data if item['status'] == 'error')
            
            logger.info(f"Extraction complete: {successful}/{len(url_data_list)} successful, {failed} download failed, {errors} extraction errors")
            
        finally:
            # Always clean up the driver
            if self.driver:
                self.driver.quit()
                logger.info("WebDriver closed")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Bulk HTML downloader using Selenium WebDriver')
    parser.add_argument('--input', '-i', default='../data/urls.csv', help='Input CSV file with URLs (default: ../data/urls.csv)')
    parser.add_argument('--output-dir', '-o', default='../output/downloaded_content', help='Output directory (default: ../output/downloaded_content)')
    parser.add_argument('--delay', '-d', type=float, default=3.0, help='Base delay between requests in seconds (default: 3.0)')
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode (default: False)')
    
    args = parser.parse_args()
    
    downloader = BulkHTMLDownloaderSelenium(
        input_file=args.input,
        output_dir=args.output_dir,
        delay=args.delay,
        headless=args.headless
    )
    
    downloader.run()

if __name__ == "__main__":
    main() 