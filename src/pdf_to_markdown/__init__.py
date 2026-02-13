"""pdf-to-markdown: Convert PDF documents to Markdown with image extraction and optional OCR."""

__version__ = "0.1.0"

from .converter import PDFToMarkdownConverter

__all__ = ["PDFToMarkdownConverter", "__version__"]
