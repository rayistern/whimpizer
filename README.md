# Wimpy Kid Style PDF Generator

Transform your text into a "Diary of a Wimpy Kid" style PDF!  
This Python script creates PDFs that mimic the handwritten diary format of the popular book series, using real Wimpy Kid fonts and notebook paper backgrounds.

---

## ✨ Features

- **Authentic Wimpy Kid Fonts**: Uses real TTF fonts from the series (WimpyKid, WimpyKidDialogue, WimpyKidCover, etc.)
- **Notebook Paper Backgrounds**: Supports actual notebook page images with ruled lines
- **Handwriting Effects**: Realistic text jitter, rotation, and positioning variations
- **Custom Bullet Points**: Hand-drawn circle bullets (no weird glyphs)
- **Markdown Parsing**: Headers, bullet/numbered lists, dialogue, and more
- **Smart Text Wrapping**: Automatically fits text to notebook lines, all the way to the edge
- **Multiple Page Support**: Seamless page breaks with consistent styling
- **Resource Management**: Loads fonts and images from a `resources/` folder
- **Flexible Input**: Supports text/markdown files or interactive input

---

## 🚀 Quick Start

### Prerequisites

- Python 3.7+
- [reportlab](https://pypi.org/project/reportlab/)
- [Pillow](https://pypi.org/project/Pillow/)

Install dependencies:
```bash
pip install reportlab pillow
```

### Setup

1. Clone or download this script.
2. Place your fonts and images in a `resources/` folder as shown below.

#### Example `resources/` Structure

```
resources/
├── font/
│   ├── WimpyKid (1).ttf
│   ├── WimpyKidDialogue (1).ttf
│   ├── Wimpycoverv2-Regular (1).ttf
│   ├── Rowley2.ttf
│   └── Kongtext (2).ttf
├── Blank Pages/
│   ├── Single Page.png
│   └── Double Page.png
├── Speech Bubbles/
│   └── BigRound1.png
├── Logos/
│   └── ...
└── Titles/
    └── ...
```

---

## 📝 Usage

### Command Line

```bash
python wimpy_pdf_generator.py -i input.md -o output.pdf -s notebook
```

- `-i, --input` : Input text/markdown file (optional, otherwise interactive)
- `-o, --output`: Output PDF filename (optional)
- `-s, --style` : PDF style (`notebook`, `plain`, `journal`, `grid`)
- `-r, --resources`: Path to resources directory (default: `resources`)
- `--list-resources`: List available fonts and images

#### Example: Interactive Mode

```bash
python wimpy_pdf_generator.py -s notebook
```
Type or paste your text, then press Ctrl+D (or Ctrl+Z on Windows) to finish.

#### Example: List Resources

```bash
python wimpy_pdf_generator.py --list-resources
```

---

## 📖 Input Format

Supports basic markdown:

```markdown
# My Secret School Life in Samarkand

## Sunday: The Weirdest Rules Ever

Okay, so my name is Hillel and I'm going to tell you about...

- Bullet points work!
- No weird glyphs for bullets

1. Numbered lists too
2. All in handwriting

"Dialogue is indented and uses a different font."
```

---

## 🎨 Styling & Fonts

- **Body text**: `WimpyKid (1).ttf`
- **Dialogue**: `WimpyKidDialogue (1).ttf`
- **Titles/Headers**: `Wimpycoverv2-Regular (1).ttf`
- **Bullets**: Drawn as filled circles (not a font glyph)
- **Text Effects**: Jitter, rotation, and ink-like color

**Text now extends all the way to the right edge of the lines** (minimal right margin).

---

## 🛠️ Customization

- Add your own TTF fonts to `resources/font/`
- Add or swap notebook backgrounds in `resources/Blank Pages/`
- Adjust margins and padding in the code for different layouts

---

## 🐛 Troubleshooting

- **Fonts not working?**  
  Make sure you have TTF (not OTF) fonts in `resources/font/`.  
  OTF fonts with PostScript outlines are not supported by ReportLab.

- **No background image?**  
  Place `Single Page.png` in `resources/Blank Pages/`.

- **Text doesn't reach the edge?**  
  The right margin is now minimal (15pt). Adjust in code if needed.

- **Weird bullet character?**  
  Fixed! Bullets are now drawn as circles, not font glyphs.

---

## 📋 Requirements

- Python 3.7+
- reportlab
- Pillow

---

## 🤝 Contributing

Pull requests welcome!  
Ideas for improvement:
- More markdown features
- More notebook backgrounds
- Doodle/drawing support
- Speech bubble overlays

---

## 📄 License

This project is for educational and personal use.  
Wimpy Kid fonts and artwork are property of their respective copyright holders.

---

**Happy diary writing!** 📔✏️