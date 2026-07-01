"""Document reader registry — auto-detect format and read to Markdown.

Usage::

    from dolatex.readers import read_document, SUPPORTED_EXTENSIONS

    md_text = read_document("report.docx")   # → Markdown str
    md_text = read_document("paper.pdf")      # → Markdown str
    md_text = read_document("notes.md")       # → raw text
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from .base import DocumentReader
from .markdown_reader import MarkdownReader
from .docx_reader import DocxReader
from .pdf_reader import PdfReader


# ---------------------------------------------------------------------------
# Registry — ordered so that more-specific readers can override generic ones.
# ---------------------------------------------------------------------------

_READERS: list[DocumentReader] = [
    MarkdownReader(),
    DocxReader(),
    PdfReader(),
]

# Pre-computed set of all supported extensions for quick look-ups.
_SUPPORTED_EXTENSIONS: frozenset[str] = frozenset().union(
    *(r.extensions() for r in _READERS)
)


def read_document(path: str | Path) -> str:
    """Auto-detect the format of *path* and return its content as Markdown.

    Parameters
    ----------
    path:
        Path to a document file (``.md``, ``.docx``, ``.pdf``, …).

    Returns
    -------
    str
        Markdown text extracted from the document.

    Raises
    ------
    ValueError
        If no reader supports the file extension.
    """
    path = Path(path)
    ext = path.suffix.lower()
    for reader in _READERS:
        if ext in reader.extensions():
            return reader.read(path)
    raise ValueError(
        f"Unsupported file extension {ext!r}. "
        f"Supported: {', '.join(sorted(_SUPPORTED_EXTENSIONS))}"
    )


def read_text(content: str | bytes, ext: str) -> str:
    """Read a document from an in-memory *content* blob.

    Parameters
    ----------
    content:
        Raw content as text (``.md``) or bytes (``.docx``, ``.pdf``).
    ext:
        File extension including the dot (e.g. ``.docx``, ``.pdf``, ``.md``).

    Returns
    -------
    str
        Markdown text extracted from the content.

    Raises
    ------
    ValueError
        If no reader supports the extension, or the content type is wrong.
    """
    ext = ext.lower()
    for reader in _READERS:
        if ext in reader.extensions():
            return reader.read(content)  # type: ignore[arg-type]
    raise ValueError(
        f"Unsupported extension {ext!r}. "
        f"Supported: {', '.join(sorted(_SUPPORTED_EXTENSIONS))}"
    )


def supported_extensions() -> frozenset[str]:
    """Return the set of all supported file extensions (with leading dot)."""
    return _SUPPORTED_EXTENSIONS


def get_reader(ext: str) -> Optional[DocumentReader]:
    """Return the reader that supports *ext*, or ``None``."""
    ext = ext.lower()
    for reader in _READERS:
        if ext in reader.extensions():
            return reader
    return None


__all__ = [
    "DocumentReader",
    "read_document",
    "read_text",
    "supported_extensions",
    "get_reader",
]
