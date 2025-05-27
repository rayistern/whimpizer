# Wimpy Kid Style PDF Generator

Transform your text into a "Diary of a Wimpy Kid" style PDF! This Python script creates PDFs that mimic the handwritten diary format of the popular book series.

## 📚 Features

- **Two Style Options**: Choose between simple formatting or advanced ruled-line notebook style
- **Interactive Input**: Enter your own text or use the provided sample diary entry
- **Authentic Styling**: Mimics the casual, handwritten diary format of Greg Heffley's journal
- **Customizable Output**: Easy to modify fonts, spacing, and layout

## 🚀 Quick Start

### Prerequisites

Make sure you have Python installed on your system, then install the required dependency:

```bash
pip install reportlab
```

### Installation

1. Clone or download the script
2. Save it as `wimpy_pdf_generator.py` (or any name you prefer)
3. Make it executable (optional):
   ```bash
   chmod +x wimpy_pdf_generator.py
   ```

### Usage

Run the script:

```bash
python wimpy_pdf_generator.py
```

Follow the interactive prompts:
1. Enter your text (press Enter twice when finished)
2. Choose your preferred style:
   - **Option 1**: Simple Wimpy Style - Clean, formatted text
   - **Option 2**: Advanced with Ruled Lines - Notebook-style with ruled lines

## 📖 Example Output

The script generates PDFs with:
- Diary-style title headers
- Handwritten-font appearance
- Proper paragraph spacing
- Optional ruled notebook lines
- Left-aligned text for natural diary flow

## 🎨 Styling Options

### Simple Style
- Clean paragraph formatting
- Wimpy Kid-inspired fonts
- Proper margins and spacing
- Title header

### Advanced Style
- All simple style features
- Ruled notebook lines (blue)
- Handwritten positioning variations
- Multi-page support with consistent formatting

## 📝 Sample Text

If you don't provide input, the script uses a sample diary entry:

```
Dear Diary,

Today was totally crazy! I woke up late because my alarm clock didn't go off...
```

## 🛠️ Customization

You can easily modify the script to:
- Change fonts (line 45-65)
- Adjust colors (import `colors` from `reportlab.lib.colors`)
- Modify spacing and margins
- Add drawings or doodles
- Change page size

### Font Customization Example

```python
# In the wimpy_style definition
fontName='Comic Sans MS',  # If available on your system
fontSize=11,
textColor=blue,
```

### Adding Doodles

```python
# In the advanced canvas class
def add_doodle(self, x, y):
    self.canvas.circle(x, y, 10)  # Simple circle doodle
```

## 📁 Output Files

- **Default filename**: `wimpy_style_output.pdf` (simple) or `advanced_wimpy_style.pdf` (advanced)
- **Location**: Same directory as the script
- **Format**: Standard PDF, compatible with all PDF readers

## 🐛 Troubleshooting

### Common Issues

**ImportError: No module named 'reportlab'**
```bash
pip install reportlab
```

**Permission Error when saving PDF**
- Make sure the output directory is writable
- Close any open PDF files with the same name

**Text appears cut off**
- The script automatically wraps long lines
- For very long text, consider breaking into multiple paragraphs

## 🔧 Advanced Usage

### Programmatic Usage

You can also use the functions directly in your own code:

```python
from wimpy_pdf_generator import create_wimpy_style_pdf

text = "Your diary entry here..."
create_wimpy_style_pdf(text, "my_diary.pdf")
```

### Batch Processing

Create multiple PDFs from a list of texts:

```python
texts = ["Entry 1...", "Entry 2...", "Entry 3..."]
for i, text in enumerate(texts):
    create_wimpy_style_pdf(text, f"diary_entry_{i+1}.pdf")
```

## 📋 Requirements

- Python 3.6+
- reportlab library
- Operating System: Windows, macOS, or Linux

## 🤝 Contributing

Feel free to fork this project and submit pull requests for:
- Additional font options
- New styling features
- Drawing/doodle capabilities
- Better handwriting simulation
- Mobile-friendly versions

## 📄 License

This project is open source. Feel free to use, modify, and distribute as needed.

## 🎯 Future Enhancements

Planned features:
- [ ] Multiple font options for different handwriting styles
- [ ] Drawing tools for simple doodles and sketches
- [ ] Template system for different diary layouts
- [ ] Image insertion capabilities
- [ ] Comic-style speech bubbles
- [ ] Margin notes and annotations

## 💡 Tips

- Keep paragraphs reasonably short for the best diary-like appearance
- Use casual, conversational language
- Consider adding dates to your entries
- Experiment with both styles to see which you prefer

---

**Happy diary writing!** 📔✏️