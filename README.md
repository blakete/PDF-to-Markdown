# PDF-to-Markdown

Convert PDF documents to Markdown with embedded image extraction and optional OCR.

Useful for more granular control of PDF document inputs to AI models.

## Features

- **Native text extraction** — high-fidelity page-by-page text via PyMuPDF
- **Image/figure export** — every embedded image saved losslessly to an `images/` directory
- **Heading detection** — promotes large/bold text to Markdown headings automatically
- **Figure-caption association** — detects "Figure N." labels and links them to nearby images
- **Optional OCR** — runs Tesseract on extracted images so screenshot text becomes searchable (collapsed in `<details>` blocks)

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

## Quick start

```bash
# Install dependencies
pip install -r requirements.txt

# Basic conversion (no OCR)
python convert.py "BriefCASE Tutorial.pdf"

# With OCR (requires tesseract + pytesseract)
python convert.py "BriefCASE Tutorial.pdf" --ocr

# Custom output directory
python convert.py "BriefCASE Tutorial.pdf" -o my_output --ocr
```

## Installation (optional)

For a proper install with the `pdf-to-markdown` CLI command:

```bash
pip install -e .            # core
pip install -e ".[ocr]"     # core + OCR support
```

Then use:

```bash
pdf-to-markdown "document.pdf" -o out --ocr
```

## CLI options

```
positional arguments:
  pdf                   Path to the source PDF file.

options:
  -o, --output-dir DIR  Parent directory for output (default: ./out)
  --ocr                 Run Tesseract OCR on extracted images
  --md-filename NAME    Name of the Markdown file (default: document.md)
  --min-image-dim N     Ignore images smaller than N px (default: 40)
```

## OCR setup

OCR is optional. To enable it:

1. Install Tesseract: `sudo apt install tesseract-ocr` (Linux) or `brew install tesseract` (macOS)
2. Install the Python binding: `pip install pytesseract`
3. Pass `--ocr` when running

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

## License

MIT
