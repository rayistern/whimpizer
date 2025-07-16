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
from typing import List, Tuple, Optional, Dict, Any, Set
from dataclasses import dataclass
from PIL import Image, ImageDraw, ImageFont
import textwrap

# ==== Global Wimpy Style Settings ====
# Update these dicts to tweak the overall appearance in a single place
FONT_SIZES = {
    'paragraph': 18,
    'h2': 18,
    'list_item': 18,
    'dialogue': 18,
}

LINE_SPACING = {
    'paragraph': 1.52,
    'h2': 1.1,
    'list_item': 1.52,
    'dialogue': 1.52,
}

JITTER = {
    'paragraph': {'x': 1.0, 'y': 0.4, 'rot': 0.05},
    'h2':        {'x': 1.0, 'y': 0.4, 'rot': 0.05},
    'list_item': {'x': 1.0, 'y': 0.4, 'rot': 0.12},
    'dialogue':  {'x': 1.5, 'y': 0.7, 'rot': 0.2},
}

PAGE_MARGINS = {
    'notebook': (50, 50, 15, 50),
    #left, top, right, bottom
    'plain':    (72, 60, 15, 60),
}

TEXT_AREA_PADDING = 5

# --- Ruled line layout control ---
# One ruled line height in points (for US letter notebook backgrounds it is ~24pt).
RULE_LINE_HEIGHT = 21.163
# How many ruled lines an explicit blank line should consume
EMPTY_LINE_MULTIPLIER = 1.40  # 1 = skip one ruled line
# Extra blank space after paragraphs expressed in ruled lines
PARAGRAPH_EXTRA_MULTIPLIER = 0.0  # 0 = none (align next paragraph directly beneath)

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
    font_size: int = 18
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
    """Parse basic markdown elements with extra Wimpy-style tweaks"""
    
    @staticmethod
    def _apply_inline_formatting(text: str) -> str:
        """Convert **bold**, *italic*, and 'quoted' segments to UPPERCASE plain text"""
        # Clean up text: remove --- and __, replace em dashes
        text = text.replace('---', '')
        text = text.replace('__', '')
        text = text.replace('—', '-')  # em dash to regular hyphen
        
        # **bold** -> BOLD (remove asterisks, uppercase)
        def bold_repl(match):
            return match.group(1).upper()
        text = re.sub(r"\*\*([^*]+?)\*\*", bold_repl, text)

        # *italic* -> ITALIC (single asterisk)
        text = re.sub(r"\*([^*]+?)\*", lambda m: m.group(1).upper(), text)
        return text

    @staticmethod
    def parse_line(line: str) -> Tuple[str, str, str]:
        """
        Parse a line and return (element_type, content, original_line)
        element_type can be: 'h1', 'h2', 'h3', 'list_item', 'paragraph', 'empty', 'dialogue'
        Additional rules:
        • Lines starting with '>' are treated as dialogue after stripping the '>'.
        • #### headers are downgraded to 'h3'.
        • Inline **bold**, *italic*, and 'quoted' phrases are capitalised and markers removed.
        """
        original_line = line.rstrip("\n")
        line = original_line.rstrip()

        if not line.strip():
            return 'empty', '', original_line

        # Handle blockquote / dialogue indicator
        is_blockquote = False
        if line.lstrip().startswith('>'):
            is_blockquote = True
            # remove leading '>' and following spaces
            line = re.sub(r"^\s*>\s*", '', line.lstrip())

        # After stripping '>', treat as dialogue if the line began with blockquote
        if is_blockquote:
            content = MarkdownParser._apply_inline_formatting(line.strip())
            return 'dialogue', content, original_line

        # Check for explicit dialogue beginning with quotes
        if line.strip().startswith(("\"", '“')):
            content = MarkdownParser._apply_inline_formatting(line.strip())
            return 'dialogue', content, original_line

        # Headers
        if line.startswith('# '):
            return 'h1', MarkdownParser._apply_inline_formatting(line[2:].strip()), original_line
        elif line.startswith('## '):
            # Process date-like headers
            h2_content = line[3:].strip()
            processed = MarkdownParser._apply_inline_formatting(h2_content)
            weekdays = [
                'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'
            ]
            first_word = processed.split()[0].lower() if processed.split() else ''
            # Remove punctuation from first word to match weekday
            first_word_clean = ''.join(c for c in first_word if c.isalpha())
            if first_word_clean in weekdays:
                # Keep only the weekday word (capitalize first letter)
                weekday_clean = first_word_clean.capitalize()
                # Return as h2 (date header)
                return 'h2', weekday_clean, original_line
            else:
                # Skip non-weekday h2 lines entirely
                return 'skip', '', original_line
        elif line.startswith('### '):
            # Check if h3 is a weekday too (same logic as h2)
            h3_content = line[4:].strip()
            processed = MarkdownParser._apply_inline_formatting(h3_content)
            weekdays = [
                'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'
            ]
            first_word = processed.split()[0].lower() if processed.split() else ''
            # Remove punctuation from first word to match weekday
            first_word_clean = ''.join(c for c in first_word if c.isalpha())
            if first_word_clean in weekdays:
                # Keep only the weekday word (capitalize first letter)
                weekday_clean = first_word_clean.capitalize()
                # Return as h2 (convert h3 weekdays to h2 for consistency)
                return 'h2', weekday_clean, original_line
            else:
                # Non-weekday h3s get skipped
                return 'skip', '', original_line
        elif line.startswith('#### '):  # treat 4-hash as h3/bold header
            return 'h3', MarkdownParser._apply_inline_formatting(line[5:].strip()), original_line

        # Lists
        list_match = re.match(r'^(\s*)([-*+]|\d+\.)\s+(.+)$', line)
        if list_match:
            _, _, content = list_match.groups()
            return 'list_item', MarkdownParser._apply_inline_formatting(content.strip()), original_line

        # Regular paragraph
        return 'paragraph', MarkdownParser._apply_inline_formatting(line.strip()), original_line


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
                font_size=FONT_SIZES['paragraph'],
                color=(25, 25, 35),  # Slightly blue-black like ink
                line_spacing=LINE_SPACING['paragraph'],
                x_jitter=JITTER['paragraph']['x'],
                y_jitter=JITTER['paragraph']['y'],
                rotation_jitter=JITTER['paragraph']['rot']
            ),
            'h1': TextStyle(
                font_path=title_font,
                font_size=27,  # Kept for compatibility though h1 is skipped
                color=(15, 15, 25),
                line_spacing=1.19,
                x_jitter=1.5,
                y_jitter=0.8,
                rotation_jitter=0.2
            ),
            'h2': TextStyle(
                font_path=body_font,  # Use regular body font for h2
                font_size=FONT_SIZES['h2'],
                color=(25, 25, 35),  # Same ink colour as paragraph
                line_spacing=LINE_SPACING['h2'],
                x_jitter=JITTER['h2']['x'],
                y_jitter=JITTER['h2']['y'],
                rotation_jitter=JITTER['h2']['rot']
            ),
            'h3': TextStyle(
                font_path=title_font,
                font_size=18,  # Kept for compatibility though h3 is skipped
                color=(20, 20, 30),
                line_spacing=0.95,
                x_jitter=1.1,
                y_jitter=0.6,
                rotation_jitter=0.15
            ),
            'list_item': TextStyle(
                font_path=body_font,
                font_size=FONT_SIZES['list_item'],
                color=(30, 30, 40),
                line_spacing=LINE_SPACING['list_item'],
                x_jitter=JITTER['list_item']['x'],
                y_jitter=JITTER['list_item']['y'],
                rotation_jitter=JITTER['list_item']['rot']
            ),
            'dialogue': TextStyle(
                font_path=dialogue_font,
                font_size=FONT_SIZES['dialogue'],
                color=(40, 20, 60),  # Slightly purple for dialogue
                line_spacing=LINE_SPACING['dialogue'],
                x_jitter=JITTER['dialogue']['x'],
                y_jitter=JITTER['dialogue']['y'],
                rotation_jitter=JITTER['dialogue']['rot']
            ),
            'month': TextStyle(
                font_path=title_font,
                font_size=FONT_SIZES.get('month', 20),
                color=(15, 15, 25),
                line_spacing=1.0,
                x_jitter=0.0,
                y_jitter=0.0,
                rotation_jitter=0.0
            )
        }
    
    def create_pdf(self, content: str, output_filename: str, style: str = "notebook"):
        """Create a PDF with the given content and style"""
        
        # Parse content while preserving line breaks
        parser = MarkdownParser()
        lines = content.split('\n')
        parsed_content = []
        
        for i, line in enumerate(lines):
            parsed_line = parser.parse_line(line)
            parsed_content.append(parsed_line)
            
            # Add empty line elements to preserve spacing between content
            # except after the last line or before an existing empty line
            if (i < len(lines) - 1 and 
                parsed_line[0] != 'empty' and 
                i + 1 < len(lines) and 
                lines[i + 1].strip() != ''):
                # Check if next line will be an empty element
                next_parsed = parser.parse_line(lines[i + 1])
                if next_parsed[0] != 'empty':
                    parsed_content.append(('empty', '', ''))
        
        # Filter out 'skip', 'h1', and 'h3' elements
        parsed_content = [item for item in parsed_content if item[0] not in ['skip', 'h1', 'h3']]
        
        # Setup page style
        if style == "notebook":
            bg_image = self.resources.get_image("single_page")
            if not bg_image:
                print("Warning: Using default notebook background (no single_page.png found)")
            self.page_style = PageStyle(
                background_image=bg_image,
                margins=PAGE_MARGINS['notebook'],
                text_area_padding=TEXT_AREA_PADDING
            )
        else:
            self.page_style = PageStyle(
                margins=PAGE_MARGINS['plain'],
                text_area_padding=TEXT_AREA_PADDING
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
    
    def _add_page_number(self, page_num: int, renderer: 'HandwritingRenderer', font_size: int = 14):
        """Add page number to the current page"""
        # Use Wimpy body font for page numbers
        body_font = self.text_styles['paragraph'].font_path or 'body'
        renderer.set_font(body_font, font_size)
        font_name = renderer.current_font
        self.canvas.setFont(font_name, font_size)
        self.canvas.setFillColorRGB(0.4, 0.4, 0.4)  # Gray color
 
        # Position at bottom center
        page_text = str(page_num)
        text_width = self.canvas.stringWidth(page_text, font_name, font_size)
        x = (self.page_style.width - text_width) / 2
        y = 20  # 20 points from bottom
 
        self.canvas.drawString(x, y, page_text)

    def _check_header_orphan(self, content_items: List[Tuple[str, str, str]], start_index: int, 
                            current_y: float, line_height_base: float, text_width: float, 
                            renderer: HandwritingRenderer) -> bool:
        """
        Check if a header at start_index would be orphaned (at bottom of page with little content).
        Returns True if the header should be moved to next page.
        """
        if start_index >= len(content_items):
            return False
            
        element_type, content, _ = content_items[start_index]
        
        # Only check headers
        if element_type != 'h2':
            return False
        
        # Calculate space needed for header itself
        style = self.text_styles.get(element_type, self.text_styles['paragraph'])
        font_logical = style.font_path or 'body'
        renderer.set_font(font_logical, style.font_size)
        font_name = renderer.current_font
        
        header_lines = self._wrap_text(content, font_name, style.font_size, text_width)
        header_height = len(header_lines) * line_height_base * style.line_spacing
        header_height += line_height_base * 0.3  # Extra space after header
        
        # Look ahead to see what content follows the header
        content_following_height = 0
        meaningful_content_lines = 0
        
        # Check the next few elements after the header
        for i in range(start_index + 1, min(start_index + 5, len(content_items))):
            following_type, following_content, _ = content_items[i]
            
            if following_type == 'empty':
                content_following_height += line_height_base * EMPTY_LINE_MULTIPLIER
                continue
            elif following_type in ['h2', 'h1', 'h3']:
                # Another header - stop looking
                break
            elif following_type in ['paragraph', 'list_item', 'dialogue']:
                # This is meaningful content
                following_style = self.text_styles.get(following_type, self.text_styles['paragraph'])
                following_font = following_style.font_path or 'body'
                renderer.set_font(following_font, following_style.font_size)
                following_font_name = renderer.current_font
                
                following_lines = self._wrap_text(following_content, following_font_name, 
                                                following_style.font_size, text_width)
                meaningful_content_lines += len(following_lines)
                content_following_height += len(following_lines) * line_height_base * following_style.line_spacing
                
                # If we have enough content, no need to look further
                if meaningful_content_lines >= 3:  # At least 3 lines of content
                    break
        
        # Calculate if header + content would fit reasonably on current page
        total_height_needed = header_height + content_following_height
        space_available = current_y - self.page_style.margins[3]
        
        # Criteria for orphan header:
        # 1. Header would fit on current page but with very little space for content
        # 2. Less than 3 lines of meaningful content following
        # 3. Less than 25% of page height available for content after header
        
        min_content_space = self.page_style.height * 0.25  # 25% of page height
        
        if (header_height < space_available and  # Header fits
            meaningful_content_lines < 3 and     # But little content follows
            (space_available - header_height) < min_content_space):  # And not much space left
            return True  # This is an orphan header
        
        return False

    def _render_content(self, parsed_content: List[Tuple[str, str, str]], renderer: HandwritingRenderer):
        """Render the parsed content to PDF"""
        
        # Start first page
        page_num = 1
        self._draw_page_background()
        self._add_page_number(page_num, renderer)
        
        # Calculate text area
        text_x = self.page_style.margins[0] + self.page_style.text_area_padding
        text_width = (self.page_style.width - self.page_style.margins[0] - 
                     self.page_style.margins[2] - self.page_style.text_area_padding)
        
        current_y = self.page_style.height - self.page_style.margins[1] - 15
        line_height_base = RULE_LINE_HEIGHT  # Match the ruled line spacing
        
        # Track when we're at the start of a page to skip leading blank lines
        at_page_start = True
        
        months_seen: Set[str] = set()
        month_names = [
            'january','february','march','april','may','june',
            'july','august','september','october','november','december'
        ]

        i = 0
        while i < len(parsed_content):
            element_type, content, original = parsed_content[i]
            i += 1  # advance index immediately to avoid infinite loops

            # Inject month header if needed (look at original line for month name)
            if element_type == 'h2':
                # find month in original string
                lower_line = original.lower()
                found_month = None
                for mn in month_names:
                    if mn in lower_line:
                        found_month = mn.capitalize()
                        break
                if found_month and found_month not in months_seen:
                    months_seen.add(found_month)
                    # Render centered month header
                    style_month = self.text_styles['month']
                    renderer.set_font(style_month.font_path or 'body', style_month.font_size)
                    month_text_width = self.canvas.stringWidth(found_month, renderer.current_font, style_month.font_size)
                    center_x = (self.page_style.width - month_text_width)/2
                    # Ensure page break
                    line_height_month = line_height_base * style_month.line_spacing
                    if current_y < self.page_style.margins[3] + line_height_month:
                        self.canvas.showPage()
                        at_page_start = True
                        page_num += 1
                        self._draw_page_background()
                        self._add_page_number(page_num, renderer)
                        current_y = self.page_style.height - self.page_style.margins[1] - 15
                    renderer.draw_text_with_effects(found_month, center_x, current_y, style_month)
                    current_y -= line_height_month
                    current_y -= line_height_base * 0.3  # small gap

            # process element normally

            # reuse variables
            element_type_local = element_type
            content_local = content
            original_local = original

            # existing processing now use element_type, content, original to let original loop body run.
            # to avoid massive rewrite we will set element_type, content, original to these and let original loop body run.

            element_type = element_type_local
            content = content_local
            original = original_local

            # The rest of code is unchanged; we can copy processing code or restructure but easier: replicate old logic inside this while loop (need big change). To minimize diff, kept previous for loop logic; but we replaced for with while. We'll simply process via same body by copying earlier operations. This is large to insert.

            if element_type == 'empty':
                # Skip blank lines at the start of pages
                if at_page_start:
                    print(f"Skipping blank line at page start")
                    continue
                    
                # Move down by a fixed number of ruled lines for blank lines
                current_y -= line_height_base * EMPTY_LINE_MULTIPLIER
                continue

            # h1 and h3 elements are now filtered out during preprocessing

            # Get style for this element (h2 now shares paragraph style settings)
            style = self.text_styles.get(element_type, self.text_styles['paragraph'])
            
            # Set font
            font_logical = style.font_path or 'body'
            renderer.set_font(font_logical, style.font_size)
            font_name = renderer.current_font  # use the registered font identifier
            
            # Calculate line height
            line_height = line_height_base * style.line_spacing
            
            # Mark that we're no longer at page start (we're about to render content)
            at_page_start = False
            
            # Handle different element types
            if element_type == 'h2':
                # Check for orphan header before proceeding
                if self._check_header_orphan(parsed_content, i-1, current_y, line_height_base, text_width, renderer):
                    print(f"Preventing orphan header: '{content[:50]}...'")
                    # Force page break to avoid orphan header
                    self.canvas.showPage()
                    at_page_start = True
                    page_num += 1
                    self._draw_page_background()
                    self._add_page_number(page_num, renderer)
                    renderer.set_font(font_logical, style.font_size)
                    current_y = self.page_style.height - self.page_style.margins[1] - 15
                
                # Treat h2 as paragraph but underline the text
                # Check for new page (normal page break logic)
                if current_y < self.page_style.margins[3] + line_height:
                    self.canvas.showPage()
                    at_page_start = True
                    page_num += 1
                    self._draw_page_background()
                    self._add_page_number(page_num, renderer)
                    renderer.set_font(font_logical, style.font_size)
                    current_y = self.page_style.height - self.page_style.margins[1] - 15

                wrapped_lines = self._wrap_text(content, font_name, style.font_size, text_width)
                for line in wrapped_lines:
                    if current_y < self.page_style.margins[3] + line_height:
                        self.canvas.showPage()
                        at_page_start = True
                        page_num += 1
                        self._draw_page_background()
                        self._add_page_number(page_num, renderer)
                        renderer.set_font(font_logical, style.font_size)
                        current_y = self.page_style.height - self.page_style.margins[1] - 15

                    # Draw the text
                    renderer.draw_text_with_effects(line, text_x, current_y, style)

                    # Underline: approximate width of text
                    line_width = self.canvas.stringWidth(line, renderer.current_font, style.font_size)
                    underline_y = current_y - (style.font_size * 0.15)
                    self.canvas.saveState()
                    r, g, b = [c/255.0 for c in style.color]
                    self.canvas.setStrokeColorRGB(r, g, b)
                    self.canvas.setLineWidth(1)
                    self.canvas.line(text_x, underline_y, text_x + line_width, underline_y)
                    self.canvas.restoreState()

                    current_y -= line_height

                # Extra space after header-like underline
                current_y -= line_height * 0.3
                
            elif element_type == 'dialogue':
                # Special handling for dialogue
                # Check if we need a new page
                if current_y < self.page_style.margins[3] + line_height:
                    self.canvas.showPage()
                    at_page_start = True
                    page_num += 1
                    self._draw_page_background()
                    self._add_page_number(page_num, renderer)
                    # re-apply font after the page switch
                    renderer.set_font(font_logical, style.font_size)
                    current_y = self.page_style.height - self.page_style.margins[1] - 15
                
                # Indent dialogue slightly
                dialogue_x = text_x + 20
                wrapped_lines = self._wrap_text(content, font_name, style.font_size, text_width - 40)
                for line in wrapped_lines:
                    if current_y < self.page_style.margins[3] + line_height:
                        self.canvas.showPage()
                        at_page_start = True
                        page_num += 1
                        self._draw_page_background()
                        self._add_page_number(page_num, renderer)
                        # re-apply font after the page switch
                        renderer.set_font(font_logical, style.font_size)
                        current_y = self.page_style.height - self.page_style.margins[1] - 15
                    
                    renderer.draw_text_with_effects(line, dialogue_x, current_y, style)
                    current_y -= line_height
                
            elif element_type == 'list_item':
                # Check if we need a new page
                if current_y < self.page_style.margins[3] + line_height:
                    self.canvas.showPage()
                    at_page_start = True
                    page_num += 1
                    self._draw_page_background()
                    self._add_page_number(page_num, renderer)
                    # re-apply font after the page switch
                    renderer.set_font(font_logical, style.font_size)
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
                for line_idx, line in enumerate(wrapped_lines):
                    if current_y < self.page_style.margins[3] + line_height:
                        self.canvas.showPage()
                        at_page_start = True
                        page_num += 1
                        self._draw_page_background()
                        self._add_page_number(page_num, renderer)
                        # re-apply font after the page switch
                        renderer.set_font(font_logical, style.font_size)
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
                        at_page_start = True
                        page_num += 1
                        self._draw_page_background()
                        self._add_page_number(page_num, renderer)
                        # re-apply font after the page switch
                        renderer.set_font(font_logical, style.font_size)
                        current_y = self.page_style.height - self.page_style.margins[1] - 15
                    
                    renderer.draw_text_with_effects(line, text_x, current_y, style)
                    current_y -= line_height
                
                # Extra space after paragraphs (optional multiple of ruled lines)
                current_y -= line_height_base * PARAGRAPH_EXTRA_MULTIPLIER

    def _wrap_text(self, text: str, font_name: str, font_size: int, max_width: float) -> List[str]:
        """Word-wrap using actual font metrics so all lines stay inside margins"""
        if not text.strip():
            return ['']

        words = text.strip().split()
        lines: List[str] = []
        current_line = ""

        for word in words:
            test_line = (current_line + " " + word).strip() if current_line else word
            line_width = self.canvas.stringWidth(test_line, font_name, font_size)

            if line_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                # Handle very long words that exceed max width alone
                if self.canvas.stringWidth(word, font_name, font_size) > max_width:
                    split_word = word
                    while self.canvas.stringWidth(split_word, font_name, font_size) > max_width and len(split_word) > 1:
                        # progressively shorten until it fits, add hyphen
                        part = split_word[:max(1, int(max_width // (font_size * 0.6)))]
                        # ensure at least one char
                        while self.canvas.stringWidth(part + '-', font_name, font_size) > max_width and len(part) > 1:
                            part = part[:-1]
                        lines.append(part + '-')
                        split_word = split_word[len(part):]
                    current_line = split_word
                else:
                    current_line = word

        if current_line:
            lines.append(current_line)

        return lines


def read_file_content(file_path: str) -> Optional[str]:
    """Read content from a text file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            # Replace problematic characters that fonts might not support
            content = content.replace(chr(0x2014), '--')  # Em-dash to double hyphen
            content = content.replace(chr(0x201C), '"')   # Left curly quote to straight quote
            content = content.replace(chr(0x201D), '"')   # Right curly quote to straight quote
            content = content.replace(chr(0x2018), "'")   # Left curly apostrophe to straight apostrophe
            content = content.replace(chr(0x2019), "'")   # Right curly apostrophe to straight apostrophe
            content = content.replace(chr(0x2026), '...') # Ellipsis to three dots
            content = content.replace(chr(0x2013), '-')   # En-dash to hyphen
            content = content.replace(chr(0x2010), '-')   # Non-breaking hyphen to regular hyphen
            content = content.replace(chr(0x2022), '*')   # Bullet point to asterisk
            content = content.replace(chr(0x00A0), ' ')   # Non-breaking space to regular space
            content = content.replace(chr(0x2011), '-')   # Non-breaking hyphen (variant) to hyphen
            content = content.replace(chr(0x2012), '-')   # Figure dash to hyphen
            content = content.replace(chr(0x2015), '--')  # Horizontal bar to double hyphen
            # Additional apostrophe variants that might cause issues
            content = content.replace('`', "'")   # Grave accent to apostrophe
            content = content.replace('´', "'")   # Acute accent to apostrophe
            # Additional bullet variants
            content = content.replace(chr(0x2023), '*')   # Triangular bullet to asterisk
            content = content.replace(chr(0x2043), '*')   # Hyphen bullet to asterisk
            content = content.replace(chr(0x25E6), '*')   # White bullet to asterisk
            content = content.replace(chr(0x2219), '*')   # Bullet operator to asterisk
            
            # Remove unwanted formatting elements
            content = content.replace('---', '')          # Remove triple dashes
            content = content.replace('_', '')            # Remove underscores
            
            # Fix multiple consecutive line breaks (replace with single)
            import re
            content = re.sub(r'\n{2,}', '\n', content)    # 2+ consecutive newlines to single newline
            
            return content
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