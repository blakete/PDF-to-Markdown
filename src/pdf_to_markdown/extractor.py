"""PDF content extraction: text blocks and embedded images via PyMuPDF."""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class ContentBlock:
    """A single text or image block extracted from a PDF page."""

    block_type: str          # "text" | "image"
    y_pos: float             # vertical position (top of bbox) — for reading order
    x_pos: float             # horizontal position (left of bbox)

    # --- text fields ---
    text: str = ""
    font_size: float = 0.0
    is_bold: bool = False

    # --- image fields ---
    image_rel_path: str = ""   # path relative to the markdown file (e.g. images/p003_img01.png)
    image_abs_path: str = ""   # absolute path on disk (needed for OCR)
    image_width: int = 0
    image_height: int = 0


@dataclass
class PageContent:
    """Extracted content for one PDF page, blocks in reading order."""

    page_num: int                                      # 1-indexed
    width: float = 0.0
    height: float = 0.0
    blocks: list[ContentBlock] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MIN_IMAGE_DIM = 40   # skip images smaller than this in either dimension (px)


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def extract_page_content(
    doc: fitz.Document,
    page: fitz.Page,
    page_num: int,
    images_dir: Path,
) -> PageContent:
    """Extract all text blocks and images from *page*, save images to *images_dir*.

    Returns a :class:`PageContent` with blocks sorted top→bottom, left→right.
    """
    result = PageContent(
        page_num=page_num,
        width=page.rect.width,
        height=page.rect.height,
    )

    _extract_text_blocks(page, result)
    _extract_images(doc, page, page_num, images_dir, result)

    # Sort into reading order
    result.blocks.sort(key=lambda b: (round(b.y_pos, 1), b.x_pos))
    return result


def collect_font_stats(pages: list[PageContent]) -> dict[str, float]:
    """Determine body-text font size and heading thresholds across all pages.

    Returns a dict with keys ``body``, ``h2_min``, ``h3_min``.
    """
    from collections import Counter

    size_counter: Counter[float] = Counter()
    for pg in pages:
        for blk in pg.blocks:
            if blk.block_type == "text" and blk.font_size > 0:
                rounded = round(blk.font_size, 1)
                size_counter[rounded] += len(blk.text)

    if not size_counter:
        return {"body": 11.0, "h2_min": 16.0, "h3_min": 13.0}

    body_size = size_counter.most_common(1)[0][0]
    return {
        "body": body_size,
        "h2_min": body_size * 1.55,
        "h3_min": body_size * 1.20,
    }


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------

def _extract_text_blocks(page: fitz.Page, result: PageContent) -> None:
    """Parse text blocks from page via ``get_text("dict")``."""
    page_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)

    for block in page_dict.get("blocks", []):
        if block.get("type") != 0:          # 0 == text
            continue

        lines_text: list[str] = []
        font_sizes: list[float] = []
        bold_spans = 0
        total_spans = 0

        for line in block.get("lines", []):
            span_texts: list[str] = []
            for span in line.get("spans", []):
                span_texts.append(span.get("text", ""))
                font_sizes.append(span.get("size", 0.0))
                total_spans += 1
                flags = span.get("flags", 0)
                font_name = span.get("font", "").lower()
                if (flags & 16) or "bold" in font_name:
                    bold_spans += 1

            joined = "".join(span_texts).rstrip()
            if joined:
                lines_text.append(joined)

        text = "\n".join(lines_text)
        if not text.strip():
            continue

        bbox = block.get("bbox", (0, 0, 0, 0))
        avg_size = sum(font_sizes) / len(font_sizes) if font_sizes else 0.0
        is_bold = (bold_spans > total_spans / 2) if total_spans else False

        result.blocks.append(ContentBlock(
            block_type="text",
            y_pos=bbox[1],
            x_pos=bbox[0],
            text=text,
            font_size=avg_size,
            is_bold=is_bold,
        ))


def _extract_images(
    doc: fitz.Document,
    page: fitz.Page,
    page_num: int,
    images_dir: Path,
    result: PageContent,
) -> None:
    """Extract embedded images from *page* and save them into *images_dir*."""
    img_counter = 0
    page_xrefs: set[int] = set()

    for img_tuple in page.get_images(full=True):
        xref = img_tuple[0]
        smask_xref = img_tuple[1]

        if xref in page_xrefs:
            continue
        page_xrefs.add(xref)

        try:
            img_data = doc.extract_image(xref)
            if not img_data or not img_data.get("image"):
                continue

            w = img_data.get("width", 0)
            h = img_data.get("height", 0)
            if w < MIN_IMAGE_DIM or h < MIN_IMAGE_DIM:
                continue

            # --- determine extension ---
            ext = img_data.get("ext", "png")
            if ext in ("jpeg", "jpx"):
                ext = "jpg"
            elif ext not in ("png", "jpg", "bmp", "tiff"):
                ext = "png"

            # --- position on page ---
            try:
                rects = page.get_image_rects(xref)
            except Exception:
                rects = []

            if rects:
                rect = rects[0]
                y_pos, x_pos = rect.y0, rect.x0
            else:
                y_pos = max((b.y_pos for b in result.blocks), default=0) + 1
                x_pos = 0.0

            # --- save ---
            img_counter += 1
            filename = f"p{page_num:03d}_img{img_counter:02d}.{ext}"
            abs_path = images_dir / filename
            image_bytes: bytes = img_data["image"]

            if smask_xref and smask_xref > 0:
                _save_with_alpha(doc, image_bytes, smask_xref, abs_path)
                # alpha → always png
                if ext != "png":
                    ext = "png"
                    filename = f"p{page_num:03d}_img{img_counter:02d}.png"
                    abs_path = images_dir / filename
                    _save_with_alpha(doc, image_bytes, smask_xref, abs_path)
            else:
                _save_image_bytes(image_bytes, ext, abs_path)

            result.blocks.append(ContentBlock(
                block_type="image",
                y_pos=y_pos,
                x_pos=x_pos,
                image_rel_path=f"images/{filename}",
                image_abs_path=str(abs_path),
                image_width=w,
                image_height=h,
            ))

        except Exception as exc:
            print(f"  [warn] page {page_num}: could not extract image xref={xref}: {exc}")


def _save_with_alpha(
    doc: fitz.Document,
    image_bytes: bytes,
    smask_xref: int,
    dest: Path,
) -> None:
    """Composite base image with its soft-mask (alpha) and save as PNG."""
    try:
        base = Image.open(io.BytesIO(image_bytes))
        mask_data = doc.extract_image(smask_xref)
        if mask_data and mask_data.get("image"):
            mask = Image.open(io.BytesIO(mask_data["image"])).convert("L")
            if base.size == mask.size:
                base = base.convert("RGBA")
                base.putalpha(mask)
        base.save(str(dest), "PNG")
    except Exception:
        dest.write_bytes(image_bytes)


def _save_image_bytes(image_bytes: bytes, ext: str, dest: Path) -> None:
    """Save raw image bytes, converting via PIL if the format needs it."""
    try:
        # Quick check: can PIL open it?
        img = Image.open(io.BytesIO(image_bytes))
        fmt_map = {"jpg": "JPEG", "png": "PNG", "bmp": "BMP", "tiff": "TIFF"}
        pil_fmt = fmt_map.get(ext, "PNG")
        # Convert CMYK/P → RGB before saving as JPEG
        if pil_fmt == "JPEG" and img.mode in ("RGBA", "P", "CMYK", "LA"):
            img = img.convert("RGB")
        img.save(str(dest), pil_fmt)
    except Exception:
        # Fallback: write raw bytes
        dest.write_bytes(image_bytes)
