"""Optional OCR support via pytesseract + Pillow."""

from __future__ import annotations

import shutil
from pathlib import Path


def is_available() -> bool:
    """Return True if both *pytesseract* and the *tesseract* binary are installed."""
    if shutil.which("tesseract") is None:
        return False
    try:
        import pytesseract as _  # noqa: F401
        return True
    except ImportError:
        return False


def ocr_image(image_path: str | Path) -> str:
    """Run Tesseract OCR on *image_path* and return the extracted text.

    Returns an empty string on failure or if no meaningful text is found.
    """
    try:
        import pytesseract
        from PIL import Image

        img = Image.open(str(image_path))

        # Convert palette / CMYK images to RGB so Tesseract handles them cleanly
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        raw: str = pytesseract.image_to_string(img)
        text = raw.strip()

        # Discard if it's just noise (very short or mostly non-alpha)
        alpha_chars = sum(c.isalpha() for c in text)
        if alpha_chars < 4:
            return ""
        return text

    except Exception:
        return ""
