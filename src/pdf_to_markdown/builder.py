"""Assemble extracted page content into a Markdown document."""

from __future__ import annotations

import re
from typing import Callable

from .extractor import ContentBlock, PageContent

# Pattern that matches "Figure 1.", "Figure 10:", "Figure 2 -", etc.
_FIGURE_RE = re.compile(
    r"(Figure\s+(\d+)\s*[.:\-–—])",
    re.IGNORECASE,
)


def build_markdown(
    pages: list[PageContent],
    title: str,
    font_stats: dict[str, float],
    *,
    ocr_func: Callable[[str], str] | None = None,
) -> str:
    """Build a complete Markdown string from extracted page content.

    Parameters
    ----------
    pages:
        Extracted content for every page (in order).
    title:
        Document title (used as ``# title``).
    font_stats:
        Dict with keys ``body``, ``h2_min``, ``h3_min`` from
        :func:`~pdf_to_markdown.extractor.collect_font_stats`.
    ocr_func:
        If provided, called with an absolute image path; should return OCR
        text or ``""``.  A ``<details>`` block is emitted for non-empty results.
    """
    lines: list[str] = []
    lines.append(f"# {title}\n")

    for page in pages:
        lines.append(f"\n---\n\n## Page {page.page_num}\n")
        _emit_page_blocks(page, font_stats, ocr_func, lines)

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _emit_page_blocks(
    page: PageContent,
    font_stats: dict[str, float],
    ocr_func: Callable[[str], str] | None,
    lines: list[str],
) -> None:
    """Render all blocks for one page into *lines*."""
    blocks = page.blocks
    i = 0

    while i < len(blocks):
        blk = blocks[i]

        if blk.block_type == "text":
            # --- Check for figure caption, and whether next block is an image ---
            fig_match = _FIGURE_RE.search(blk.text)

            if fig_match and i + 1 < len(blocks) and blocks[i + 1].block_type == "image":
                # Emit caption + image together
                _emit_text(blk, font_stats, lines)
                i += 1
                _emit_image(blocks[i], ocr_func, lines, alt=_figure_alt(fig_match))
            else:
                _emit_text(blk, font_stats, lines)

        elif blk.block_type == "image":
            # Check if the *previous* text was a figure caption
            alt = ""
            if i > 0 and blocks[i - 1].block_type == "text":
                prev_match = _FIGURE_RE.search(blocks[i - 1].text)
                if prev_match:
                    alt = _figure_alt(prev_match)
            _emit_image(blk, ocr_func, lines, alt=alt)

        i += 1


def _emit_text(
    blk: ContentBlock,
    font_stats: dict[str, float],
    lines: list[str],
) -> None:
    """Emit a text block, promoting large/bold text to Markdown headings."""
    text = blk.text.strip()
    if not text:
        return

    size = blk.font_size
    short = len(text) < 200  # headings are typically short

    if short and size >= font_stats["h2_min"]:
        lines.append(f"### {_oneline(text)}\n")
    elif short and blk.is_bold and size >= font_stats["h3_min"]:
        lines.append(f"#### {_oneline(text)}\n")
    else:
        lines.append(f"{text}\n")


def _emit_image(
    blk: ContentBlock,
    ocr_func: Callable[[str], str] | None,
    lines: list[str],
    *,
    alt: str = "",
) -> None:
    """Emit an image reference, plus an optional OCR ``<details>`` block."""
    lines.append(f"![{alt}]({blk.image_rel_path})\n")

    if ocr_func and blk.image_abs_path:
        ocr_text = ocr_func(blk.image_abs_path)
        if ocr_text:
            lines.append(
                "<details>\n"
                "<summary>Image text (OCR)</summary>\n\n"
                f"```\n{ocr_text}\n```\n\n"
                "</details>\n"
            )


def _figure_alt(match: re.Match) -> str:  # type: ignore[type-arg]
    """Build alt-text from a regex match on 'Figure N.'."""
    return f"Figure {match.group(2)}"


def _oneline(text: str) -> str:
    """Collapse multi-line text into a single line (for headings)."""
    return " ".join(text.split())
