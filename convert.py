#!/usr/bin/env python3
"""Example script — convert a PDF to Markdown.

Usage:
    python convert.py "BriefCASE Tutorial.pdf"
    python convert.py "BriefCASE Tutorial.pdf" --ocr
    python convert.py "BriefCASE Tutorial.pdf" -o out --ocr
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running without installing the package (adds src/ to the import path)
_src = Path(__file__).resolve().parent / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from pdf_to_markdown import PDFToMarkdownConverter  # noqa: E402
from pdf_to_markdown.cli import main                # noqa: E402

if __name__ == "__main__":
    # If invoked with no arguments, default to the tutorial PDF in this repo
    if len(sys.argv) == 1:
        default_pdf = Path(__file__).resolve().parent / "BriefCASE Tutorial.pdf"
        if default_pdf.exists():
            print(f"No arguments — using default: {default_pdf.name}\n")
            sys.argv = [sys.argv[0], str(default_pdf)]

    main()
