#!/usr/bin/env python3
"""
Test script to verify HTML content extraction
"""

from bs4 import BeautifulSoup

# Sample HTML content from user
sample_html = '''
<h1 class="article-header__title js-article-title js-page-title">Living Under Communism</h1>

<div class="co_body article-body cf">
<p>When reminiscing about the past,
most people will
only recall a few vague memories from early childhood. Not so those who grew up
under the shadow of Soviet rule. Our
parents' uncompromising battle to provide an authentically Jewish education for us, and their struggle to prevent us from being
exposed to the heretical communist ideology, embedded a profound impression on
us as children that affects us to this day.</p>
</div>
'''

def test_extraction():
    soup = BeautifulSoup(sample_html, 'html.parser')
    
    # Extract title
    title_selector = '.article-header__title.js-article-title.js-page-title'
    title_element = soup.select_one(title_selector)
    title = title_element.get_text(strip=True) if title_element else "No title found"
    
    # Extract body content
    body_selector = '.co_body.article-body.cf'
    body_element = soup.select_one(body_selector)
    body = body_element.get_text(strip=True) if body_element else "No body content found"
    
    print("Extraction Test Results:")
    print("=" * 50)
    print(f"Title: {title}")
    print(f"Body: {body[:100]}..." if len(body) > 100 else f"Body: {body}")
    print("=" * 50)
    
    return title != "No title found" and body != "No body content found"

if __name__ == "__main__":
    success = test_extraction()
    if success:
        print("✅ Extraction test passed!")
    else:
        print("❌ Extraction test failed!") 