"""Reader for plain-text Markdown files (``.md``, ``.markdown``, ``.txt``)."""

from __future__ import annotations

from pathlib import Path

from .base import DocumentReader


class MarkdownReader(DocumentReader):
    """Read a plain-text file and return it verbatim as Markdown."""

    def extensions(self) -> frozenset[str]:
        return frozenset({".md", ".markdown", ".txt"})

    def read(self, data: str | bytes | Path) -> str:
        """Read Markdown from *data*.

        If *data* is bytes, decode it as UTF-8.
        If *data* is a string that looks like a file path (exists on
        disk or contains path separators), read the file.
        Otherwise return *data* verbatim (already raw Markdown content).
        """
        if isinstance(data, bytes):
            return data.decode("utf-8")

        # If it's already a Path or looks like a file path, read from disk.
        if isinstance(data, Path):
            return data.read_text(encoding="utf-8")

        # String: check if it's a file path or raw content.
        if _is_path_like(data):
            return Path(data).read_text(encoding="utf-8")

        # Already raw Markdown content.
        return data


def _is_path_like(text: str) -> bool:
    """Heuristic: return *True* if *text* looks like a filesystem path."""
    if not text:
        return False
    # Path separators or dots with short extensions are strong signals.
    if "/" in text or "\\" in text:
        return True
    # If it exists on disk, it's a path.
    if Path(text).exists():
        return True
    return False
