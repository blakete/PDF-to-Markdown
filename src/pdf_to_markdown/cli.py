"""Command-line interface for pdf-to-markdown."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="pdf-to-markdown",
        description="Convert a PDF document to Markdown with extracted images.",
    )
    parser.add_argument(
        "pdf",
        type=Path,
        help="Path to the source PDF file.",
    )
    parser.add_argument(
        "-o", "--output-dir",
        type=Path,
        default=Path("out"),
        help="Parent directory for output (default: ./out). A sub-directory "
             "named after the PDF is created inside.",
    )
    parser.add_argument(
        "--ocr",
        action="store_true",
        default=False,
        help="Run Tesseract OCR on extracted images and include the text "
             "in collapsible <details> blocks in the Markdown.",
    )
    parser.add_argument(
        "--md-filename",
        default="document.md",
        help="Name of the generated Markdown file (default: document.md).",
    )
    parser.add_argument(
        "--min-image-dim",
        type=int,
        default=40,
        help="Ignore images smaller than this in either dimension (px, default: 40).",
    )

    args = parser.parse_args(argv)

    # Lazy import so --help is fast
    from .converter import PDFToMarkdownConverter

    converter = PDFToMarkdownConverter(
        pdf_path=args.pdf,
        output_dir=args.output_dir,
        ocr=args.ocr,
        markdown_filename=args.md_filename,
        min_image_dim=args.min_image_dim,
    )

    try:
        md_path = converter.convert()
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"\nMarkdown written to: {md_path}")


if __name__ == "__main__":
    main()
