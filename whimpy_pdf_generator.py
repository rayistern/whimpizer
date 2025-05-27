#!/usr/bin/env python3
"""
Wimpy Kid Style PDF Generator (Refactored and Enhanced)
Creates PDFs with handwritten-style text similar to Diary of a Wimpy Kid books.
"""

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, BaseDocTemplate, Frame, PageTemplate
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import textwrap
import os
import argparse
import random
import re

# --- Constants ---
DEFAULT_TEXT_COLOR = colors.black
DEFAULT_LINE_HEIGHT = 20

# --- Helper Functions ---

def _get_handwriting_font(c, size=12):
    """
    Try a handful of handwriting-like fonts, fall back to Helvetica.
    `c` is a ReportLab canvas or has the same .setFont API.
    Returns the font name that could be activated.
    """
    candidates = [
        "Comic Sans MS", "Comic-Sans-MS", "ComicSansMS",
        "Marker Felt", "Chalkboard SE", "Bradley Hand", "Chalkduster",
        "Helvetica"  # Fallback
    ]
    for f_name in candidates:
        try:
            c.setFont(f_name, size)
            return f_name
        except Exception:
            continue
    c.setFont("Helvetica", size) # Ensure a font is set
    return "Helvetica"

def read_file_content(file_path):
    """
    Read content from a file (supports .md, .txt, and other text files)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        print(f"Successfully read content from: {file_path}")
        return content
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return None
    except Exception as e:
        print(f"Error reading file '{file_path}': {e}")
        return None

# --- Base Canvas for Ruled Styles ---
class BaseRuledCanvas:
    def __init__(self, filename, style_params, pagesize=letter):
        self.filename = filename
        self.style_params = style_params
        self.canvas = canvas.Canvas(filename, pagesize=pagesize)
        self.width, self.height = pagesize

        self.line_height = style_params.get("line_height", DEFAULT_LINE_HEIGHT)
        self.margin_left = style_params.get("margin_left", 72)
        self.margin_right = style_params.get("margin_right", 72)
        self.margin_top = style_params.get("margin_top", 72)
        self.margin_bottom = style_params.get("margin_bottom", 72)
        
        self.text_color = style_params.get("text_color", DEFAULT_TEXT_COLOR)
        self.canvas.setFillColor(self.text_color)

        # Get and store the base handwriting font
        base_font_size = self.style_params.get("base_font_size", 11)
        self._selected_base_font_name = _get_handwriting_font(self.canvas, base_font_size)
        self.style_params["_selected_base_font_name"] = self._selected_base_font_name


    def _get_font_details(self, style_type="body"):
        base_font_size = self.style_params["base_font_size"]
        font_name = self.style_params["_selected_base_font_name"]
        font_size = base_font_size
        
        if style_type == "h1":
            font_size = base_font_size + self.style_params.get("h1_font_size_increase", 4)
            bold_suffix = self.style_params.get("font_bold_suffix")
            if bold_suffix:
                try:
                    # Test if bold version exists by trying to set it
                    temp_canvas_for_font_test = canvas.Canvas("dummy_font_test.pdf")
                    temp_canvas_for_font_test.setFont(font_name + bold_suffix, font_size)
                    font_name += bold_suffix
                except:
                    pass # Use regular font_name
        elif style_type == "h2":
            font_size = base_font_size + self.style_params.get("h2_font_size_increase", 2)
        
        return font_name, font_size

    def _draw_common_background_elements(self):
        # Ruled lines
        self.canvas.setStrokeColor(self.style_params["ruled_line_color"])
        self.canvas.setLineWidth(self.style_params.get("ruled_line_width", 0.5))
        y = self.height - self.margin_top
        while y >= self.margin_bottom:
            self.canvas.line(self.margin_left, y, self.width - self.margin_right, y)
            y -= self.line_height
        
        # Margin line
        self.canvas.setStrokeColor(self.style_params["margin_line_color"])
        self.canvas.setLineWidth(self.style_params.get("margin_line_width", 0.8))
        margin_line_x = self.margin_left + self.style_params.get("margin_line_offset", -20)
        self.canvas.line(margin_line_x, self.height - self.margin_top, margin_line_x, self.margin_bottom)

        # Binder holes
        if self.style_params.get("draw_binder_holes", True):
            self.canvas.setFillColor(self.style_params["binder_hole_color"])
            hole_x = self.style_params.get("binder_hole_x", 30)
            hole_radius = self.style_params.get("binder_hole_radius", 5)
            hole_positions_factors = self.style_params.get("binder_hole_positions_factors", [0.2, 0.5, 0.8])
            for factor in hole_positions_factors:
                hole_y = self.height * factor
                self.canvas.circle(hole_x, hole_y, hole_radius, fill=1, stroke=self.style_params.get("binder_hole_stroke", 0))

    def _calculate_initial_y_pos(self, font_size_for_first_line):
        # This calculation aims to center the text somewhat on the first ruled line.
        # y_pos = self.height - self.margin_top - (self.line_height - font_size) / 2 - font_size + adjustment
        # Simplified: baseline of text relative to top margin.
        adjustment = self.style_params.get("text_on_line_adjust", 2) # Small vertical tweak
        # Position so baseline is 'font_size - adjustment' below the line, and line is 'line_height' from margin
        # Effectively, this means the text baseline is slightly above the ruled line.
        # The original formula: self.height - self.margin_top - (self.line_height - font_size_to_use) / 2 - font_size_to_use + 2
        # This places the baseline of the text.
        offset = (self.line_height - font_size_for_first_line) / 2 + font_size_for_first_line - adjustment
        return self.height - self.margin_top - offset


    def _handle_page_break(self, y_pos, font_size_for_next_line):
        if y_pos < self.margin_bottom + self.line_height: # Need space for at least one more line
            self.canvas.showPage()
            self.draw_page_background() # Implemented by subclasses
            self.canvas.setFillColor(self.text_color) # Reset text color
            return self._calculate_initial_y_pos(font_size_for_next_line)
        return y_pos

    def _wrap_text(self, text, font_name, font_size):
        max_text_width = self.width - self.margin_left - self.margin_right - self.style_params.get("text_area_padding", 15)
        words = text.split()
        wrapped_lines = []
        current_line_for_wrapping = []

        if not words:
            return []

        for word in words:
            test_line_content = current_line_for_wrapping + [word]
            test_line_str = ' '.join(test_line_content)
            text_width = self.canvas.stringWidth(test_line_str, font_name, font_size)

            if text_width <= max_text_width:
                current_line_for_wrapping.append(word)
            else:
                if current_line_for_wrapping: # Current line has content, so finalize it
                    wrapped_lines.append(' '.join(current_line_for_wrapping))
                    current_line_for_wrapping = [word] # Start new line with current word
                    # Check if the single word itself is too long
                    if self.canvas.stringWidth(word, font_name, font_size) > max_text_width:
                        wrapped_lines.append(word) # Add it anyway (will overflow)
                        current_line_for_wrapping = [] # Clear for next
                else: # Word itself is too long and current_line_for_wrapping is empty
                    wrapped_lines.append(word) # Add it (will overflow)
                    current_line_for_wrapping = [] # Clear for next
        
        if current_line_for_wrapping:
            wrapped_lines.append(' '.join(current_line_for_wrapping))
        
        if not wrapped_lines and text: # Original line wasn't wrapped but was not empty
             wrapped_lines.append(text)
             
        return wrapped_lines

    def _draw_text_line_with_effects(self, line_to_draw, x, y, font_name, font_size):
        self.canvas.setFont(font_name, font_size)
        x_variation = random.uniform(*self.style_params.get("x_jitter_range", (-1, 1)))
        y_variation = random.uniform(*self.style_params.get("y_jitter_range", (-0.5, 0.5)))
        self.canvas.drawString(x + x_variation, y + y_variation, line_to_draw)

    def add_text_content(self, text_content):
        _ , initial_font_size = self._get_font_details("body")
        y_pos = self._calculate_initial_y_pos(initial_font_size)
        x_pos = self.margin_left + self.style_params.get("text_x_offset", 5)

        input_lines = text_content.split('\n')

        for current_text_line in input_lines:
            style_type = "body"
            text_to_process = current_text_line # Keep original for non-matches
            is_list_item = False
            bullet_char = None
            list_indent_val = self.style_params.get("list_indent", 20)
            current_x_pos = x_pos

            # Markdownish parsing
            if current_text_line.startswith("# "):
                style_type = "h1"
                text_to_process = current_text_line[2:].strip()
            elif current_text_line.startswith("## "):
                style_type = "h2"
                text_to_process = current_text_line[3:].strip()
            else:
                list_match = re.match(r"^\s*([-*]|\d+\.)\s+", current_text_line)
                if list_match:
                    is_list_item = True
                    bullet_marker = list_match.group(1).strip()
                    if bullet_marker == '*' or bullet_marker == '-':
                        bullet_char = self.style_params.get("bullet_char_unordered", "\u2022") # •
                    else:
                        bullet_char = bullet_marker # e.g., "1."
                    text_to_process = current_text_line[list_match.end():].strip()
                else:
                    text_to_process = current_text_line.strip()


            font_name, font_size = self._get_font_details(style_type)
            self.canvas.setFont(font_name, font_size) # Set for wrapping and drawing

            extra_leading = self.style_params.get(f"extra_leading_{style_type}", 0)

            if not text_to_process.strip() and not is_list_item: # Handle empty lines as paragraph breaks
                y_pos -= self.line_height
                y_pos = self._handle_page_break(y_pos, font_size) # Use current font_size for next line context
                continue

            wrapped_lines = self._wrap_text(text_to_process, font_name, font_size)
            if not wrapped_lines and text_to_process: # if text exists but wrap returned empty (e.g. only spaces)
                wrapped_lines = [text_to_process] if text_to_process.strip() else []


            for i, line_to_draw in enumerate(wrapped_lines):
                y_pos = self._handle_page_break(y_pos, font_size)
                self.canvas.setFont(font_name, font_size) # Ensure font is set on new page

                current_x_pos_for_line = x_pos
                if is_list_item and i == 0 and bullet_char: # Draw bullet only for the first line of a list item
                    bullet_x = x_pos + self.style_params.get("bullet_x_offset", 0)
                    bullet_y = y_pos + self.style_params.get("bullet_y_offset", 0)
                    # Use body font for bullet
                    bullet_font_name, bullet_font_size = self._get_font_details("body")
                    self.canvas.setFont(bullet_font_name, bullet_font_size)
                    self.canvas.drawString(bullet_x, bullet_y, bullet_char)
                    current_x_pos_for_line = x_pos + list_indent_val
                    self.canvas.setFont(font_name, font_size) # Switch back to item text font

                elif is_list_item: # Subsequent lines of a list item are indented
                     current_x_pos_for_line = x_pos + list_indent_val


                self._draw_text_line_with_effects(line_to_draw, current_x_pos_for_line, y_pos, font_name, font_size)
                y_pos -= self.line_height
            
            if extra_leading > 0:
                y_pos -= extra_leading
                y_pos = self._handle_page_break(y_pos, font_size)


    def save(self):
        self.canvas.save()

    def draw_page_background(self):
        # To be implemented by subclasses
        # Should set page fill color and call _draw_common_background_elements
        raise NotImplementedError("Subclasses must implement draw_page_background")

# --- Specific Canvas Styles ---

class NotebookCanvas(BaseRuledCanvas):
    def __init__(self, filename, pagesize=letter):
        style_params = {
            "line_height": 20, "margin_left": 90, "margin_right": 50, 
            "margin_top": 60, "margin_bottom": 60,
            "ruled_line_color": colors.Color(0.68, 0.85, 0.90), "ruled_line_width": 0.5,
            "margin_line_color": colors.red, "margin_line_width": 0.8, "margin_line_offset": -20,
            "text_color": colors.black,
            "page_bg_color": colors.white,
            "draw_binder_holes": True,
            "binder_hole_color": colors.Color(1.0, 0.75, 0.80), "binder_hole_radius": 5,
            "binder_hole_x": 30, "binder_hole_positions_factors": [0.2, 0.5, 0.8], "binder_hole_stroke":0,
            "base_font_size": 11, "h1_font_size_increase": 4, "h2_font_size_increase": 2,
            "font_bold_suffix": "-Bold",
            "extra_leading_h1": 10, "extra_leading_h2": 5,
            "text_area_padding": 15, "text_x_offset": 5, "text_on_line_adjust": 2,
            "x_jitter_range": (-1, 1), "y_jitter_range": (-0.5, 0.5),
            "list_indent": 25, "bullet_char_unordered": "\u2022", "bullet_x_offset": -15, "bullet_y_offset": 0,
        }
        super().__init__(filename, style_params, pagesize)
        self.draw_page_background()

    def draw_page_background(self):
        self.canvas.setFillColor(self.style_params["page_bg_color"])
        self.canvas.rect(0, 0, self.width, self.height, fill=1, stroke=0)
        self._draw_common_background_elements()

class AdvancedNotebookCanvas(BaseRuledCanvas):
    def __init__(self, filename, pagesize=letter):
        style_params = {
            "line_height": 22, "margin_left": 95, "margin_right": 45,
            "margin_top": 55, "margin_bottom": 55,
            "ruled_line_color": colors.HexColor('#B8D4F0'), "ruled_line_width": 0.4,
            "margin_line_color": colors.HexColor('#FF6B6B'), "margin_line_width": 1.0, "margin_line_offset": -25,
            "text_color": colors.HexColor('#1A1A1A'), # Softer black
            "page_bg_color": colors.HexColor('#FEFDF6'), # Cream/off-white
            "draw_binder_holes": True,
            "binder_hole_color": colors.HexColor('#F0F0F0'), "binder_hole_radius": 6,
            "binder_hole_x": 25, "binder_hole_positions_factors": [0.15, 0.5, 0.85], "binder_hole_stroke":1,
            "binder_hole_inner_shadow_color": colors.HexColor('#E0E0E0'),
            "base_font_size": 12, "h1_font_size_increase": 4, "h2_font_size_increase": 2,
            "font_bold_suffix": None, # Or specify if a bold variant is preferred and available
            "extra_leading_h1": 11, "extra_leading_h2": 5.5, # 0.5 * line_height, 0.25 * line_height
            "text_area_padding": 30, "text_x_offset": 8, "text_on_line_adjust": 0, # Advanced uses different y_pos logic slightly
            "x_jitter_range": (-1.5, 1.5), "y_jitter_range": (-0.8, 0.8),
            "angle_jitter_range": (-0.3, 0.3),
            "list_indent": 25, "bullet_char_unordered": "\u2022", "bullet_x_offset": -15, "bullet_y_offset": 0,
        }
        super().__init__(filename, style_params, pagesize)
        # Override initial y_pos for advanced style's specific needs if different from base calc
        self.style_params["text_on_line_adjust"] = self.style_params.get("adv_text_on_line_adjust", 8) # from original: y_pos = self.height - self.margin_top - 8
        self.draw_page_background()

    def _calculate_initial_y_pos(self, font_size_for_first_line): # Override for advanced
         return self.height - self.margin_top - self.style_params.get("text_on_line_adjust", 8)


    def draw_page_background(self):
        self.canvas.setFillColor(self.style_params["page_bg_color"])
        self.canvas.rect(0, 0, self.width, self.height, fill=1, stroke=0)
        self._draw_common_background_elements()
        # Add inner shadow for holes if specified
        if self.style_params.get("binder_hole_inner_shadow_color"):
            hole_x = self.style_params["binder_hole_x"]
            hole_radius = self.style_params["binder_hole_radius"]
            hole_positions_factors = self.style_params["binder_hole_positions_factors"]
            self.canvas.setFillColor(self.style_params["binder_hole_inner_shadow_color"])
            for factor in hole_positions_factors:
                hole_y = self.height * factor
                self.canvas.circle(hole_x, hole_y, hole_radius - 1, fill=1, stroke=0)


    def _draw_text_line_with_effects(self, line_to_draw, x, y, font_name, font_size):
        self.canvas.setFont(font_name, font_size)
        x_var = random.uniform(*self.style_params["x_jitter_range"])
        y_var = random.uniform(*self.style_params["y_jitter_range"])
        angle_var = random.uniform(*self.style_params["angle_jitter_range"])
        
        self.canvas.saveState()
        self.canvas.translate(x + x_var, y + y_var)
        self.canvas.rotate(angle_var)
        self.canvas.drawString(0, 0, line_to_draw)
        self.canvas.restoreState()

# --- PDF Creation Functions (Wrappers for Canvases) ---
def create_notebook_style_pdf(text, output_filename):
    pdf_canvas = NotebookCanvas(output_filename)
    pdf_canvas.add_text_content(text)
    pdf_canvas.save()
    print(f"Notebook style PDF created: {output_filename}")

def create_advanced_style_pdf(text, output_filename):
    pdf_canvas = AdvancedNotebookCanvas(output_filename)
    pdf_canvas.add_text_content(text)
    pdf_canvas.save()
    print(f"Advanced notebook style PDF created: {output_filename}")

# --- Platypus-based Plain Style (largely from original) ---
def create_plain_style_pdf(text: str, output_filename="wimpy_plain_style.pdf"):
    PAGE_WIDTH, PAGE_HEIGHT = letter
    margin = 1 * inch

    _dummy_canvas = canvas.Canvas("dummy_for_plain_font.pdf")
    handwriting_font = _get_handwriting_font(_dummy_canvas, 12)

    styles = getSampleStyleSheet()
    diary_style = ParagraphStyle(
        name="DiaryBody",
        parent=styles["Normal"],
        fontName=handwriting_font,
        fontSize=12,
        leading=16, # Space between lines
        spaceAfter=12, # Space after paragraph
        textColor=colors.black,
        alignment=0 # 0=left, 1=center, 2=right, 4=justify
    )
    h1_style = ParagraphStyle(
        name="DiaryH1", parent=diary_style, fontSize=16, leading=20, spaceBefore=12, spaceAfter=6)
    h2_style = ParagraphStyle(
        name="DiaryH2", parent=diary_style, fontSize=14, leading=18, spaceBefore=10, spaceAfter=5)
    list_style = ParagraphStyle(
        name="DiaryList", parent=diary_style, leftIndent=18, spaceAfter=2)

    def _on_page_platypus(canv, doc):
        page_no = canv.getPageNumber()
        font = _get_handwriting_font(canv, 10) # Use the helper for consistency
        canv.setFont(font, 10)
        y = 0.55 * inch
        if page_no % 2 == 0: # even page -> left
            canv.drawString(margin, y, str(page_no))
        else: # odd page -> right
            canv.drawRightString(PAGE_WIDTH - margin, y, str(page_no))

    story = []
    # Split by double newline for paragraphs, then process each line within for markdown
    raw_paragraphs = text.strip().split("\n\n")

    for para_text in raw_paragraphs:
        if not para_text.strip():
            continue
        
        lines_in_para = para_text.split('\n')
        is_first_line_in_para = True
        for line_text in lines_in_para:
            stripped_line = line_text.strip()
            if not stripped_line:
                if not is_first_line_in_para : # Add spacer for intentional empty lines within a "paragraph" block
                     story.append(Spacer(1, diary_style.leading / 2))
                continue

            is_first_line_in_para = False
            
            if stripped_line.startswith("# "):
                story.append(Paragraph(stripped_line[2:].strip(), h1_style))
            elif stripped_line.startswith("## "):
                story.append(Paragraph(stripped_line[3:].strip(), h2_style))
            elif re.match(r"^\s*([-*]|\d+\.)\s+", stripped_line):
                # Remove bullet for Platypus, it handles list indentation
                actual_item_text = re.sub(r"^\s*([-*]|\d+\.)\s*", "", stripped_line)
                story.append(Paragraph(actual_item_text, list_style))
            else:
                story.append(Paragraph(stripped_line, diary_style))
        # Add a bit more space after a block that was treated as a paragraph,
        # unless it was just a header or a single list item that already has spaceAfter.
        if not (stripped_line.startswith("#") or re.match(r"^\s*([-*]|\d+\.)\s+", stripped_line)):
             if diary_style.spaceAfter == 0 : # If default paragraph doesn't have spaceAfter
                  story.append(Spacer(1,6))


    doc = BaseDocTemplate(
        output_filename,
        pagesize=letter,
        leftMargin=margin, rightMargin=margin,
        topMargin=margin, bottomMargin=margin
    )

    frame = Frame(
        margin, margin,
        PAGE_WIDTH - 2 * margin, PAGE_HEIGHT - 2 * margin,
        id="normal_frame"
    )
    template = PageTemplate(id="plain_wimpy_template", frames=[frame], onPage=_on_page_platypus)
    doc.addPageTemplates([template])
    
    try:
        doc.build(story)
        print(f"Plain Wimpy-Kid style PDF created: {output_filename}")
    except Exception as e:
        print(f"Error building plain PDF: {e}")
        print("Story content that caused error:")
        for i, item in enumerate(story):
            if hasattr(item, 'text'):
                 print(f"  {i}: Paragraph: {item.text[:100]}...")
            else:
                 print(f"  {i}: {type(item)}")


# --- Main Application Logic ---
def main():
    parser = argparse.ArgumentParser(
        description="Generate Wimpy Kid style PDFs from text or markdown files"
    )
    parser.add_argument('-i', '--input', type=str, help='Input file path (.md, .txt)')
    parser.add_argument('-o', '--output', type=str, help='Output PDF file path')
    parser.add_argument(
        '-s', '--style', type=str, choices=['plain', 'notebook', 'advanced'],
        default='plain', help='PDF style: plain | notebook | advanced (default: plain)'
    )
    args = parser.parse_args()

    print("=== Wimpy Kid Style PDF Generator ===\n")

    input_text = None
    output_filename = args.output
    style_choice = args.style

    if args.input:
        input_text = read_file_content(args.input)
        if input_text is None: return
        if not output_filename:
            base_name = os.path.splitext(os.path.basename(args.input))[0]
            output_filename = f"{base_name}_{style_choice}_style.pdf"
    else: # Interactive mode
        print("Choose input method:")
        print("1. Type text manually")
        print("2. Read from file")
        input_method = input("Enter choice (1 or 2): ").strip()

        if input_method == "2":
            file_path = input("Enter file path: ").strip()
            input_text = read_file_content(file_path)
            if input_text is None: return
            if not output_filename:
                base_name = os.path.splitext(os.path.basename(file_path))[0]
                output_filename = f"{base_name}_{style_choice}_style.pdf"
        else:
            print("Enter your text (press Enter twice on empty lines when finished):")
            lines = []
            empty_line_count = 0
            while True:
                line = input()
                if line == "":
                    empty_line_count += 1
                    if empty_line_count >= 2: break
                    lines.append(line) # Keep single empty lines for paragraph breaks
                else:
                    empty_line_count = 0
                    lines.append(line)
            input_text = '\n'.join(lines)

    if not input_text or not input_text.strip():
        input_text = """Monday, October 15th

## My Not-So-Great Day

So today was just TERRIBLE. I woke up late because my stupid alarm clock didn't go off, and Mom was already yelling at me to get ready for school.

I rushed to get dressed and grab my backpack, but I couldn't find my math homework ANYWHERE. 
- I spent like 20 minutes looking for it.
- Found it under my bed with Rodrick's dirty socks. GROSS.

At school, things got even worse. During lunch, I was carrying my tray and Tommy Miller stuck his foot out and BOOM!
1. I went flying.
2. My chocolate milk went everywhere.
Everyone was laughing and pointing at me.

But then something actually good happened. This new kid named Alex helped me clean up and shared his lunch with me. Maybe today wasn't ALL bad.

Tomorrow better be different though. I can't handle another day like this.

- Greg"""
        print("Using default sample text...")

    if not output_filename:
        output_filename = f"wimpy_{style_choice}_output.pdf"
    
    # Ensure output filename has .pdf extension
    if not output_filename.lower().endswith(".pdf"):
        output_filename += ".pdf"

    # If style was not given via CLI and we are in interactive input mode for text
    if not args.input and not args.style: # Re-check if style needs to be prompted
        print("\nChoose PDF style:")
        print("1. Plain Wimpy-Kid Book Style (No lines, like published books)")
        print("2. Simple Notebook Style (Ruled lines, basic handwritten feel)")
        print("3. Advanced Premium Notebook Style (Enhanced notebook look and feel)")
        
        choice_map = {"1": "plain", "2": "notebook", "3": "advanced"}
        style_input = input("Enter choice (1, 2, or 3): ").strip()
        style_choice = choice_map.get(style_input, "plain")
        if style_input not in choice_map:
            print("Invalid choice, defaulting to plain.")
        # Update output_filename if it was based on default style
        if output_filename == f"wimpy_plain_output.pdf" or output_filename == f"wimpy_style_output.pdf":
             output_filename = f"wimpy_{style_choice}_output.pdf"


    print(f"\nGenerating {style_choice} style PDF: {output_filename}")

    if style_choice == "advanced":
        create_advanced_style_pdf(input_text, output_filename)
    elif style_choice == "notebook":
        create_notebook_style_pdf(input_text, output_filename)
    else:  # "plain"
        create_plain_style_pdf(input_text, output_filename)

if __name__ == "__main__":
    try:
        import reportlab
    except ImportError:
        print("Error: reportlab library is required.")
        print("Install it with: pip install reportlab")
        exit(1)
    main()