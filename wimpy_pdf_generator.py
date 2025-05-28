#!/usr/bin/env python3
"""
Wimpy Kid Style PDF Generator - Complete Rewrite
Creates PDFs with handwritten-style text using actual notebook paper backgrounds and custom fonts.
"""

import os
import re
import random
import argparse
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
from PIL import Image, ImageDraw, ImageFont
import textwrap

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
except ImportError:
    print("Error: reportlab library is required. Install with: pip install reportlab")
    exit(1)

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow library is required. Install with: pip install Pillow")
    exit(1)


@dataclass
class TextStyle:
    """Configuration for text styling"""
    font_path: Optional[str] = None
    font_size: int = 12
    color: Tuple[int, int, int] = (0, 0, 0)  # RGB
    line_spacing: float = 1.2
    x_jitter: float = 1.0
    y_jitter: float = 0.5
    rotation_jitter: float = 0.2


@dataclass
class PageStyle:
    """Configuration for page styling"""
    background_image: Optional[str] = None
    width: int = 612  # letter size in points
    height: int = 792
    margins: Tuple[int, int, int, int] = (72, 72, 72, 72)  # left, top, right, bottom
    text_area_padding: int = 10


class ResourceManager:
    """Manages fonts, images, and other resources"""
    
    def __init__(self, resources_dir: str = "resources"):
        self.resources_dir = Path(resources_dir)
        self.fonts = {}
        self.images = {}
        self.wimpy_fonts = {}  # Special mapping for Wimpy Kid fonts
        self.load_resources()
    
    def load_resources(self):
        """Load all available resources"""
        if not self.resources_dir.exists():
            print(f"Warning: Resources directory '{self.resources_dir}' not found")
            return
        
        # Load fonts (prioritize TTF over OTF due to ReportLab limitations)
        font_extensions = {'.ttf': 1, '.otf': 2}  # Priority order
        font_candidates = []
        
        for font_file in self.resources_dir.rglob('*'):
            if font_file.suffix.lower() in font_extensions:
                priority = font_extensions[font_file.suffix.lower()]
                font_candidates.append((priority, font_file))
        
        # Sort by priority (TTF first)
        font_candidates.sort(key=lambda x: x[0])
        
        for priority, font_file in font_candidates:
            font_name = font_file.stem.lower()
            if font_name not in self.fonts:  # Don't overwrite TTF with OTF
                self.fonts[font_name] = str(font_file)
                self._map_wimpy_fonts(font_file.stem, str(font_file))
                print(f"Loaded font: {font_name} from {font_file}")
        
        # Load background images
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp'}
        for img_file in self.resources_dir.rglob('*'):
            if img_file.suffix.lower() in image_extensions:
                img_name = img_file.stem.lower().replace(' ', '_')
                self.images[img_name] = str(img_file)
                print(f"Loaded image: {img_name} from {img_file}")
    
    def _map_wimpy_fonts(self, font_name: str, font_path: str):
        """Map Wimpy Kid fonts to their specific purposes"""
        font_name_lower = font_name.lower()
        
        # Skip OTF files that cause problems
        if font_path.lower().endswith('.otf'):
            print(f"Skipping OTF font {font_name} (ReportLab compatibility)")
            return
        
        # Map based on font names - prioritize TTF files
        if 'dialogue' in font_name_lower and font_path.lower().endswith('.ttf'):
            self.wimpy_fonts['dialogue'] = font_path
            print(f"Mapped dialogue font: {font_name}")
        elif 'cover' in font_name_lower and font_path.lower().endswith('.ttf'):
            self.wimpy_fonts['title'] = font_path
            self.wimpy_fonts['cover'] = font_path
            print(f"Mapped title/cover font: {font_name}")
        elif 'rowley' in font_name_lower and font_path.lower().endswith('.ttf'):
            self.wimpy_fonts['rowley'] = font_path
            print(f"Mapped rowley font: {font_name}")
        elif 'kongtext' in font_name_lower and font_path.lower().endswith('.ttf'):
            self.wimpy_fonts['kongtext'] = font_path
            print(f"Mapped kongtext font: {font_name}")
        elif 'wimpykid' in font_name_lower and not any(x in font_name_lower for x in ['dialogue', 'cover', 'cursed']) and font_path.lower().endswith('.ttf'):
            # This is the main Wimpy Kid font
            self.wimpy_fonts['main'] = font_path
            self.wimpy_fonts['body'] = font_path  # Use as default body font
            print(f"Mapped main/body font: {font_name}")
    
    def get_font(self, name: str, size: int = 12) -> Optional[str]:
        """Get font path by name"""
        name = name.lower()
        
        # First check Wimpy Kid specific fonts
        if name in self.wimpy_fonts:
            return self.wimpy_fonts[name]
        
        # Then check regular fonts
        if name in self.fonts:
            return self.fonts[name]
        
        # Try partial matches (prefer TTF)
        for font_name, font_path in self.fonts.items():
            if (name in font_name or font_name in name) and font_path.lower().endswith('.ttf'):
                return font_path
        
        # Fallback to any match
        for font_name, font_path in self.fonts.items():
            if name in font_name or font_name in name:
                return font_path
        
        return None
    
    def get_image(self, name: str) -> Optional[str]:
        """Get image path by name"""
        name = name.lower().replace(' ', '_')
        if name in self.images:
            return self.images[name]
        
        # Try partial matches
        for img_name, img_path in self.images.items():
            if name in img_name or img_name in name:
                return img_path
        
        return None
    
    def list_fonts(self) -> List[str]:
        """List all available fonts"""
        return list(self.fonts.keys())
    
    def list_wimpy_fonts(self) -> Dict[str, str]:
        """List all mapped Wimpy Kid fonts"""
        return self.wimpy_fonts.copy()
    
    def list_images(self) -> List[str]:
        """List all available background images"""
        return list(self.images.keys())


class HandwritingRenderer:
    """Renders text with handwriting-like effects"""
    
    def __init__(self, canvas_obj: canvas.Canvas, resource_manager: ResourceManager):
        self.canvas = canvas_obj
        self.resources = resource_manager
        self.current_font = None
        self.current_size = 12
        self._registered_fonts = set()
        self._font_cache = {}  # Cache successful font registrations
    
    def set_font(self, font_name: str, size: int):
        """Set the font for rendering"""
        # Check cache first
        cache_key = f"{font_name}_{size}"
        if cache_key in self._font_cache:
            self.current_font = self._font_cache[cache_key]
            self.current_size = size
            self.canvas.setFont(self.current_font, size)
            return
        
        font_path = self.resources.get_font(font_name)
        if font_path and font_path.lower().endswith('.ttf'):
            try:
                # For ReportLab, we need to register the font first
                from reportlab.pdfbase import pdfutils
                from reportlab.pdfbase.ttfonts import TTFont
                
                # Create a unique font key
                font_key = f"wimpy_{font_name}_{size}"
                
                if font_key not in self._registered_fonts:
                    try:
                        font_obj = TTFont(font_key, font_path)
                        from reportlab.pdfbase import pdfmetrics
                        pdfmetrics.registerFont(font_obj)
                        self._registered_fonts.add(font_key)
                        print(f"Successfully registered: {font_key} from {font_path}")
                    except Exception as e:
                        print(f"Failed to register font {font_name}: {e}")
                        # Try without size in name
                        fallback_key = f"wimpy_{font_name}"
                        if fallback_key not in self._registered_fonts:
                            try:
                                font_obj = TTFont(fallback_key, font_path)
                                pdfmetrics.registerFont(font_obj)
                                self._registered_fonts.add(fallback_key)
                                font_key = fallback_key
                                print(f"Registered with fallback key: {fallback_key}")
                            except Exception as e2:
                                print(f"Complete font registration failure: {e2}")
                                font_key = None
                
                if font_key and font_key in self._registered_fonts:
                    self.current_font = font_key
                    self._font_cache[cache_key] = font_key
                    self.current_size = size
                    self.canvas.setFont(self.current_font, size)
                    return
                    
            except Exception as e:
                print(f"Font loading error for {font_name}: {e}")
        
        # Fallback logic - try to use system fonts that look handwritten
        print(f"Using fallback font for {font_name}")
        handwriting_fonts = ["Comic Sans MS", "Marker Felt", "Chalkboard SE", "Bradley Hand", "Helvetica"]
        for font in handwriting_fonts:
            try:
                self.canvas.setFont(font, size)
                self.current_font = font
                self._font_cache[cache_key] = font
                self.current_size = size
                print(f"Fallback successful: {font}")
                return
            except:
                continue
        
        # Final fallback
        self.current_font = "Helvetica"
        self._font_cache[cache_key] = "Helvetica"
        self.current_size = size
        self.canvas.setFont("Helvetica", size)
        print(f"Using final fallback: Helvetica")

    def draw_text_with_effects(self, text: str, x: float, y: float, style: TextStyle):
        """Draw text with handwriting effects"""
        if not text.strip():
            return
        
        # Ensure font is set
        if not self.current_font:
            self.set_font('body', style.font_size)
        
        # Apply jitter for handwriting effect
        jitter_x = random.uniform(-style.x_jitter, style.x_jitter)
        jitter_y = random.uniform(-style.y_jitter, style.y_jitter)
        
        final_x = x + jitter_x
        final_y = y + jitter_y
        
        # Set text color
        if len(style.color) == 3:  # RGB
            r, g, b = [c/255.0 for c in style.color]
            self.canvas.setFillColorRGB(r, g, b)
        
        # Save state for rotation
        self.canvas.saveState()
        
        # Apply slight rotation for handwriting effect
        if style.rotation_jitter > 0:
            rotation = random.uniform(-style.rotation_jitter, style.rotation_jitter)
            self.canvas.rotate(rotation)
        
        # Draw the text
        self.canvas.drawString(final_x, final_y, text)
        
        # Restore state
        self.canvas.restoreState()


class MarkdownParser:
    """Parse basic markdown elements"""
    
    @staticmethod
    def parse_line(line: str) -> Tuple[str, str, str]:
        """
        Parse a line and return (element_type, content, original_line)
        element_type can be: 'h1', 'h2', 'h3', 'list_item', 'paragraph', 'empty', 'dialogue'
        """
        line = line.rstrip()
        
        if not line.strip():
            return 'empty', '', line
        
        # Check for dialogue (quoted text)
        if line.strip().startswith('"') and line.strip().endswith('"'):
            return 'dialogue', line.strip(), line
        
        # Headers
        if line.startswith('# '):
            return 'h1', line[2:].strip(), line
        elif line.startswith('## '):
            return 'h2', line[3:].strip(), line
        elif line.startswith('### '):
            return 'h3', line[4:].strip(), line
        
        # Lists
        list_match = re.match(r'^(\s*)([-*+]|\d+\.)\s+(.+)$', line)
        if list_match:
            indent, marker, content = list_match.groups()
            return 'list_item', content.strip(), line
        
        # Regular paragraph
        return 'paragraph', line.strip(), line


class WimpyPDFGenerator:
    """Main PDF generator class"""
    
    def __init__(self, resources_dir: str = "resources"):
        self.resources = ResourceManager(resources_dir)
        self.page_style = None
        self.canvas = None
        self.text_styles = self._get_text_styles()
    
    def _get_text_styles(self) -> Dict[str, TextStyle]:
        """Get text styles for different elements"""
        wimpy_fonts = self.resources.list_wimpy_fonts()
        
        print(f"Available Wimpy fonts: {wimpy_fonts}")
        
        # Select fonts for different text types - with better fallbacks
        body_font = 'body'
        title_font = 'title' 
        dialogue_font = 'dialogue'
        
        # Provide fallbacks if specific fonts aren't available
        if 'body' not in wimpy_fonts and 'main' in wimpy_fonts:
            body_font = 'main'
        elif not wimpy_fonts:
            print("Warning: No Wimpy Kid fonts available, using system defaults")
            body_font = 'helvetica'
            title_font = 'helvetica'
            dialogue_font = 'helvetica'
        
        if 'title' not in wimpy_fonts and 'cover' in wimpy_fonts:
            title_font = 'cover'
        elif 'title' not in wimpy_fonts and 'main' in wimpy_fonts:
            title_font = 'main'
        
        if 'dialogue' not in wimpy_fonts:
            dialogue_font = body_font
        
        print(f"Font assignments: body={body_font}, title={title_font}, dialogue={dialogue_font}")
        
        return {
            'paragraph': TextStyle(
                font_path=body_font,
                font_size=12,
                color=(25, 25, 35),  # Slightly blue-black like ink
                line_spacing=1.2,
                x_jitter=1.2,
                y_jitter=0.6,
                rotation_jitter=0.15
            ),
            'h1': TextStyle(
                font_path=title_font,
                font_size=18,
                color=(15, 15, 25),
                line_spacing=1.3,
                x_jitter=1.5,
                y_jitter=0.8,
                rotation_jitter=0.2
            ),
            'h2': TextStyle(
                font_path=title_font,
                font_size=15,
                color=(15, 15, 25),
                line_spacing=1.25,
                x_jitter=1.3,
                y_jitter=0.7,
                rotation_jitter=0.18
            ),
            'h3': TextStyle(
                font_path=title_font,
                font_size=13,
                color=(20, 20, 30),
                line_spacing=1.2,
                x_jitter=1.1,
                y_jitter=0.6,
                rotation_jitter=0.15
            ),
            'list_item': TextStyle(
                font_path=body_font,
                font_size=11,
                color=(30, 30, 40),
                line_spacing=1.15,
                x_jitter=1.0,
                y_jitter=0.5,
                rotation_jitter=0.12
            ),
            'dialogue': TextStyle(
                font_path=dialogue_font,
                font_size=11,
                color=(40, 20, 60),  # Slightly purple for dialogue
                line_spacing=1.3,
                x_jitter=1.5,
                y_jitter=0.7,
                rotation_jitter=0.2
            )
        }
    
    def create_pdf(self, content: str, output_filename: str, style: str = "notebook"):
        """Create a PDF with the given content and style"""
        
        # Parse content
        parser = MarkdownParser()
        lines = content.split('\n')
        parsed_content = [parser.parse_line(line) for line in lines]
        
        # Setup page style
        if style == "notebook":
            bg_image = self.resources.get_image("single_page")
            if not bg_image:
                print("Warning: Using default notebook background (no single_page.png found)")
            self.page_style = PageStyle(
                background_image=bg_image,
                margins=(85, 78, 15, 60),  # Reduced top from 90→78, bottom from 72→60
                text_area_padding=5
            )
        else:
            self.page_style = PageStyle(
                margins=(72, 60, 15, 60),  # Reduced top from 72→60, bottom from 72→60
                text_area_padding=5
            )
        
        # Create canvas
        self.canvas = canvas.Canvas(output_filename, pagesize=(self.page_style.width, self.page_style.height))
        
        # Create renderer
        renderer = HandwritingRenderer(self.canvas, self.resources)
        
        # Pre-register all fonts we'll need
        print("Pre-registering fonts...")
        for style_name, text_style in self.text_styles.items():
            if text_style.font_path:
                renderer.set_font(text_style.font_path, text_style.font_size)
        
        # Render content
        self._render_content(parsed_content, renderer)
        
        # Save PDF
        self.canvas.save()
        print(f"PDF saved: {output_filename}")
    
    def _draw_page_background(self):
        """Draw the page background"""
        if self.page_style.background_image and os.path.exists(self.page_style.background_image):
            try:
                # Load and draw background image
                img = ImageReader(self.page_style.background_image)
                self.canvas.drawImage(img, 0, 0, 
                                    width=self.page_style.width, 
                                    height=self.page_style.height)
            except Exception as e:
                print(f"Warning: Could not load background image: {e}")
                self._draw_default_background()
        else:
            self._draw_default_background()
    
    def _draw_default_background(self):
        """Draw a default notebook-style background"""
        # White background
        self.canvas.setFillColorRGB(1, 1, 1)
        self.canvas.rect(0, 0, self.page_style.width, self.page_style.height, fill=1, stroke=0)
        
        # Ruled lines
        self.canvas.setStrokeColorRGB(0.7, 0.85, 0.95)
        self.canvas.setLineWidth(0.5)
        
        line_spacing = 24  # Slightly wider spacing for Wimpy Kid style
        y = self.page_style.height - self.page_style.margins[1]
        
        while y > self.page_style.margins[3]:
            self.canvas.line(
                self.page_style.margins[0], y,
                self.page_style.width - self.page_style.margins[2], y
            )
            y -= line_spacing
        
        # Margin line (red like in real notebooks)
        self.canvas.setStrokeColorRGB(1, 0.4, 0.4)
        self.canvas.setLineWidth(1.2)
        margin_x = self.page_style.margins[0] - 25
        self.canvas.line(
            margin_x, self.page_style.height - self.page_style.margins[1],
            margin_x, self.page_style.margins[3]
        )
        
        # Binder holes
        self.canvas.setFillColorRGB(0.92, 0.92, 0.92)
        self.canvas.setStrokeColorRGB(0.8, 0.8, 0.8)
        hole_x = 35
        hole_radius = 10
        hole_positions = [0.15, 0.5, 0.85]
        
        for pos in hole_positions:
            hole_y = self.page_style.height * pos
            self.canvas.circle(hole_x, hole_y, hole_radius, fill=1, stroke=1)
    
    def _render_content(self, parsed_content: List[Tuple[str, str, str]], renderer: HandwritingRenderer):
        """Render the parsed content to PDF"""
        
        # Start first page
        self._draw_page_background()
        
        # Calculate text area
        text_x = self.page_style.margins[0] + self.page_style.text_area_padding
        text_width = (self.page_style.width - self.page_style.margins[0] - 
                     self.page_style.margins[2] - self.page_style.text_area_padding)
        
        current_y = self.page_style.height - self.page_style.margins[1] - 15
        line_height_base = 24  # Match the ruled line spacing
        
        for element_type, content, original in parsed_content:
            if element_type == 'empty':
                current_y -= line_height_base * 0.5
                continue
            
            # Get style for this element
            style = self.text_styles.get(element_type, self.text_styles['paragraph'])
            
            # Set font
            font_name = style.font_path or 'body'
            renderer.set_font(font_name, style.font_size)
            
            # Calculate line height
            line_height = line_height_base * style.line_spacing
            
            # Handle different element types
            if element_type in ['h1', 'h2', 'h3']:
                current_y -= line_height * 0.4  # Extra space before headers
                
                # Check if we need a new page
                if current_y < self.page_style.margins[3] + line_height:
                    self.canvas.showPage()
                    self._draw_page_background()
                    # re-apply font after the page switch
                    renderer.set_font(font_name, style.font_size)
                    current_y = self.page_style.height - self.page_style.margins[1] - 15
                
                # Render header
                renderer.draw_text_with_effects(content, text_x, current_y, style)
                current_y -= line_height
                current_y -= line_height * 0.3  # Extra space after headers
                
            elif element_type == 'dialogue':
                # Special handling for dialogue
                # Check if we need a new page
                if current_y < self.page_style.margins[3] + line_height:
                    self.canvas.showPage()
                    self._draw_page_background()
                    # re-apply font after the page switch
                    renderer.set_font(font_name, style.font_size)
                    current_y = self.page_style.height - self.page_style.margins[1] - 15
                
                # Indent dialogue slightly
                dialogue_x = text_x + 20
                wrapped_lines = self._wrap_text(content, font_name, style.font_size, text_width - 40)
                for line in wrapped_lines:
                    if current_y < self.page_style.margins[3] + line_height:
                        self.canvas.showPage()
                        self._draw_page_background()
                        # re-apply font after the page switch
                        renderer.set_font(font_name, style.font_size)
                        current_y = self.page_style.height - self.page_style.margins[1] - 15
                    
                    renderer.draw_text_with_effects(line, dialogue_x, current_y, style)
                    current_y -= line_height
                
            elif element_type == 'list_item':
                # Check if we need a new page
                if current_y < self.page_style.margins[3] + line_height:
                    self.canvas.showPage()
                    self._draw_page_background()
                    # re-apply font after the page switch
                    renderer.set_font(font_name, style.font_size)
                    current_y = self.page_style.height - self.page_style.margins[1] - 15
                
                # Draw a tiny filled-circle bullet that doesn't depend on font glyphs
                bullet_radius = style.font_size * 0.15        # ~15 % of text height
                self.canvas.saveState()
                r, g, b = [c / 255.0 for c in style.color]     # use same ink colour
                self.canvas.setFillColorRGB(r, g, b)
                # Slight vertical tweak so the dot sits on the text baseline nicely
                self.canvas.circle(text_x - 10,
                                   current_y + style.font_size * 0.30,
                                   bullet_radius,
                                   stroke=0,
                                   fill=1)
                self.canvas.restoreState()
                
                # Wrap and render list item text
                wrapped_lines = self._wrap_text(content, font_name, style.font_size, text_width - 25)
                for i, line in enumerate(wrapped_lines):
                    if current_y < self.page_style.margins[3] + line_height:
                        self.canvas.showPage()
                        self._draw_page_background()
                        # re-apply font after the page switch
                        renderer.set_font(font_name, style.font_size)
                        current_y = self.page_style.height - self.page_style.margins[1] - 15
                    
                    x_offset = 25  # Indent list items
                    renderer.draw_text_with_effects(line, text_x + x_offset, current_y, style)
                    current_y -= line_height
                
            else:  # paragraph
                # Wrap and render paragraph text
                wrapped_lines = self._wrap_text(content, font_name, style.font_size, text_width)
                for line in wrapped_lines:
                    if current_y < self.page_style.margins[3] + line_height:
                        self.canvas.showPage()
                        self._draw_page_background()
                        # re-apply font after the page switch
                        renderer.set_font(font_name, style.font_size)
                        current_y = self.page_style.height - self.page_style.margins[1] - 15
                    
                    renderer.draw_text_with_effects(line, text_x, current_y, style)
                    current_y -= line_height
                
                # Extra space after paragraphs
                current_y -= line_height * 0.4
    
    def _wrap_text(self, text: str, font_name: str, font_size: int, max_width: float) -> List[str]:
        """Wrap text to fit within the specified width"""
        if not text.strip():
            return ['']
        
        # Estimate character width (Wimpy Kid fonts are actually narrower than estimated)
        avg_char_width = font_size * 0.5  # Reduced from 0.7 to 0.5
        chars_per_line = int(max_width / avg_char_width)
        
        # Use textwrap for basic wrapping, but be more aggressive
        wrapper = textwrap.TextWrapper(
            width=max(chars_per_line, 25),  # Increased minimum from 15 to 25
            break_long_words=True,
            break_on_hyphens=True,
            expand_tabs=True,
            replace_whitespace=True,
            drop_whitespace=True
        )
        
        wrapped = wrapper.wrap(text)
        
        # If we still get very short lines, try to be even more aggressive
        if wrapped and len(wrapped[0]) < 30 and len(text) > 40:
            # Try with even more characters per line
            chars_per_line = int(max_width / (font_size * 0.4))
            wrapper.width = max(chars_per_line, 35)
            wrapped = wrapper.wrap(text)
        
        return wrapped if wrapped else ['']


def read_file_content(file_path: str) -> Optional[str]:
    """Read content from a text file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None


def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(description="Generate Wimpy Kid style PDFs")
    parser.add_argument('-i', '--input', help='Input text/markdown file')
    parser.add_argument('-o', '--output', help='Output PDF file')
    parser.add_argument('-s', '--style', choices=['notebook', 'plain', 'journal', 'grid'], 
                       default='notebook', help='PDF style')
    parser.add_argument('-r', '--resources', default='resources', help='Resources directory')
    parser.add_argument('--list-resources', action='store_true', help='List available resources')
    
    args = parser.parse_args()
    
    # Initialize generator
    generator = WimpyPDFGenerator(args.resources)
    
    # List resources if requested
    if args.list_resources:
        print("Available fonts:", generator.resources.list_fonts())
        print("Wimpy Kid fonts:", generator.resources.list_wimpy_fonts())
        print("Available background images:", generator.resources.list_images())
        return
    
    # Get input content
    if args.input:
        content = read_file_content(args.input)
        if not content:
            return
        
        # Generate output filename if not provided
        if not args.output:
            input_path = Path(args.input)
            args.output = f"{input_path.stem}_{args.style}.pdf"
    else:
        # Interactive input
        print("Enter your text (press Ctrl+D or Ctrl+Z when finished):")
        try:
            content = input().strip()
            while True:
                line = input()
                content += '\n' + line
        except EOFError:
            pass
        
        if not args.output:
            args.output = f"wimpy_{args.style}.pdf"
    
    # Use sample content if no input provided
    if not content or not content.strip():
        content = """# My Wimpy Day

## Monday, October 15th

So today was just TERRIBLE. I woke up late because my stupid alarm clock didn't go off, and Mom was already yelling at me to get ready for school.

"Greg! You're going to be late AGAIN!" she shouted from downstairs.

I rushed to get dressed and grab my backpack, but I couldn't find my math homework ANYWHERE.

- I spent like 20 minutes looking for it
- Found it under my bed with Rodrick's dirty socks
- GROSS!

At school, things got even worse. During lunch, I was carrying my tray and Tommy Miller stuck his foot out and BOOM!

1. I went flying
2. My chocolate milk went everywhere  
3. Everyone was laughing and pointing at me

But then something actually good happened. This new kid named Alex helped me clean up and shared his lunch with me. 

"Don't worry about those guys," he said. "They're just jerks."

Maybe today wasn't ALL bad.

Tomorrow better be different though. I can't handle another day like this.

### The End

- Greg"""
    
    # Generate PDF
    try:
        generator.create_pdf(content, args.output, args.style)
        print(f"Successfully generated: {args.output}")
    except Exception as e:
        print(f"Error generating PDF: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 