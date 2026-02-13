"""High-level orchestrator: PDF → Markdown + images directory."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF

from .builder import build_markdown
from .extractor import PageContent, collect_font_stats, extract_page_content
from .ocr import is_available as ocr_is_available, ocr_image


class PDFToMarkdownConverter:
    """Convert a PDF file into a Markdown document with extracted images.

    Parameters
    ----------
    pdf_path:
        Path to the source PDF.
    output_dir:
        Parent directory for output.  A sub-directory named after the PDF
        (without extension) is created inside this directory.
    ocr:
        If ``True``, run Tesseract OCR on extracted images and include the
        text in collapsible ``<details>`` blocks.
    markdown_filename:
        Name of the generated Markdown file (default ``"document.md"``).
    min_image_dim:
        Ignore images whose width **or** height is below this value (px).
    """

    def __init__(
        self,
        pdf_path: str | Path,
        output_dir: str | Path = "out",
        *,
        ocr: bool = False,
        markdown_filename: str = "document.md",
        min_image_dim: int = 40,
    ) -> None:
        self.pdf_path = Path(pdf_path).resolve()
        if not self.pdf_path.is_file():
            raise FileNotFoundError(f"PDF not found: {self.pdf_path}")

        self.output_dir = Path(output_dir).resolve()
        self.ocr = ocr
        self.markdown_filename = markdown_filename
        self.min_image_dim = min_image_dim

        # Derived paths
        self.doc_name = self.pdf_path.stem  # e.g. "BriefCASE Tutorial"
        self.doc_dir = self.output_dir / self.doc_name
        self.images_dir = self.doc_dir / "images"
        self.md_path = self.doc_dir / self.markdown_filename

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def convert(self) -> Path:
        """Run the full conversion pipeline.

        Returns the path to the generated Markdown file.
        """
        t0 = time.perf_counter()

        self._prepare_dirs()
        print(f"[pdf-to-markdown] Converting: {self.pdf_path.name}")
        print(f"[pdf-to-markdown] Output dir: {self.doc_dir}")

        doc = fitz.open(str(self.pdf_path))
        try:
            pages = self._extract_all(doc)
        finally:
            doc.close()

        font_stats = collect_font_stats(pages)
        print(f"[pdf-to-markdown] Body font size: {font_stats['body']:.1f}pt")

        ocr_func = self._make_ocr_func()
        md_text = build_markdown(
            pages,
            title=self.doc_name,
            font_stats=font_stats,
            ocr_func=ocr_func,
        )

        self.md_path.write_text(md_text, encoding="utf-8")
        elapsed = time.perf_counter() - t0

        img_count = sum(
            1 for pg in pages for b in pg.blocks if b.block_type == "image"
        )
        print(
            f"[pdf-to-markdown] Done in {elapsed:.1f}s — "
            f"{len(pages)} pages, {img_count} images → {self.md_path}"
        )
        return self.md_path

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _prepare_dirs(self) -> None:
        self.doc_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(parents=True, exist_ok=True)

    def _extract_all(self, doc: fitz.Document) -> list[PageContent]:
        """Extract content from every page."""
        pages: list[PageContent] = []
        total = len(doc)

        for idx in range(total):
            page = doc.load_page(idx)
            page_num = idx + 1
            print(f"  Extracting page {page_num}/{total} …", end="\r")
            pc = extract_page_content(doc, page, page_num, self.images_dir)
            pages.append(pc)

        print()  # clear the \r line
        return pages

    def _make_ocr_func(self):
        """Return an OCR callable or *None*."""
        if not self.ocr:
            return None

        if not ocr_is_available():
            print(
                "[pdf-to-markdown] WARNING: OCR requested but tesseract/pytesseract "
                "not found — skipping OCR."
            )
            return None

        print("[pdf-to-markdown] Running OCR on extracted images …")
        _cache: dict[str, str] = {}

        def _cached_ocr(path: str) -> str:
            if path not in _cache:
                _cache[path] = ocr_image(path)
            return _cache[path]

        return _cached_ocr
