# PDF-to-Markdown

Convert PDF documents to Markdown with embedded image extraction and optional OCR.

Useful for more granular control of PDF document inputs to AI models.

## Features

- **Native text extraction** — high-fidelity page-by-page text via PyMuPDF
- **Image/figure export** — every embedded image saved losslessly to an `images/` directory
- **Heading detection** — promotes large/bold text to Markdown headings automatically
- **Figure-caption association** — detects "Figure N." labels and links them to nearby images
- **Optional OCR** — runs Tesseract on extracted images so screenshot text becomes searchable (collapsed in `<details>` blocks)

## Installation

Install directly from GitHub:

```bash
pip install git+https://github.com/blakete/PDF-to-Markdown.git
```

With OCR support (requires [Tesseract](https://github.com/tesseract-ocr/tesseract) installed on your system):

```bash
pip install "pdf-to-markdown[ocr] @ git+https://github.com/blakete/PDF-to-Markdown.git"
```

## Usage

```bash
# Basic conversion
pdf2markdown document.pdf

# Custom output directory
pdf2markdown document.pdf -o my_output

# With OCR (screenshot text becomes searchable)
pdf2markdown document.pdf --ocr

# Combine options
pdf2markdown document.pdf -o out --ocr --md-filename notes.md
```

## CLI options

```
positional arguments:
  pdf                   Path to the source PDF file.

options:
  -V, --version         Show version and exit.
  -o, --output-dir DIR  Parent directory for output (default: ./out)
  --ocr                 Run Tesseract OCR on extracted images
  --md-filename NAME    Name of the Markdown file (default: document.md)
  --min-image-dim N     Ignore images smaller than N px (default: 40)
```

## Output structure

```
out/
  My Document/
    document.md       # Markdown with text + image references
    images/           # All extracted figures/screenshots
      p001_img01.png
      p002_img01.jpg
      ...
```

## Python API

```python
from pdf_to_markdown import PDFToMarkdownConverter

converter = PDFToMarkdownConverter(
    pdf_path="document.pdf",
    output_dir="out",
    ocr=True,
)
md_path = converter.convert()
print(f"Output: {md_path}")
```

## OCR setup

OCR is optional. To enable it:

1. Install Tesseract: `sudo apt install tesseract-ocr` (Linux) or `brew install tesseract` (macOS)
2. Install the Python binding: `pip install pytesseract` (or use `pip install "pdf-to-markdown[ocr] @ git+..."`)
3. Pass `--ocr` when running

## Development

```bash
git clone https://github.com/blakete/PDF-to-Markdown.git
cd PDF-to-Markdown
python -m venv .venv && source .venv/bin/activate
pip install -e ".[ocr]"

# Or run the example script directly
pip install -r requirements.txt
python convert.py "BriefCASE Tutorial.pdf"
```

## License

MIT
