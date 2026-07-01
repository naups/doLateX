"""Reader for PDF files — extracts text content as Markdown.

Uses ``pypdf`` to extract text page-by-page, then applies simple heuristics
to recover basic structure:

* Lines that are all-caps or end with no period → potential headings
* Numbered lines → ordered list items
* Bullet-like lines (``-``, ``*``, ``•``) → unordered list items
* Blank lines → paragraph separators
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from .base import DocumentReader

# Heuristic patterns
_RE_HEADING_CAPS: re.Pattern = re.compile(r"^[A-Z\s]{4,}$")
_RE_ORDERED_ITEM: re.Pattern = re.compile(r"^\s*(\d+)[.)]\s+(.+)$")
_RE_BULLET_ITEM: re.Pattern = re.compile(r"^\s*[-*•]\s+(.+)$")


class PdfReader(DocumentReader):
    """Convert a PDF file to Markdown text via text extraction + heuristics."""

    def extensions(self) -> frozenset[str]:
        return frozenset({".pdf"})

    def read(self, path: Path | str | bytes) -> str:
        """Read a PDF file and return a best-effort Markdown representation."""
        try:
            from pypdf import PdfReader as PdfExtract
        except ModuleNotFoundError:
            raise ValueError(
                "pypdf is required to read .pdf files. "
                "Install with: pip install dolatex[pdf] or pip install pypdf"
            )

        if isinstance(path, bytes):
            import io
            reader = PdfExtract(io.BytesIO(path))
        else:
            reader = PdfExtract(str(path))

        pages_text: list[str] = []
        for page in reader.pages:
            raw = page.extract_text() or ""
            md = self._page_to_markdown(raw)
            pages_text.append(md)

        return "\n\n".join(pages_text).strip()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @classmethod
    def _page_to_markdown(cls, text: str) -> str:
        """Convert a single page of extracted text to Markdown.

        Strategy:

        1. Split into lines.
        2. Group consecutive lines into paragraphs.
        3. Apply heuristics for headings, lists, and code blocks.
        """
        lines = text.splitlines()
        output: list[str] = []
        i = 0
        n = len(lines)

        while i < n:
            line = lines[i].strip()

            # Skip empty / near-empty lines
            if not line:
                i += 1
                continue

            # ---- Heuristic: ALL-CAPS heading --------------------------------
            if _RE_HEADING_CAPS.match(line) and len(line) > 3:
                output.append(f"## {line.title()}")
                i += 1
                continue

            # ---- Heuristic: numbered list item ------------------------------
            olm = _RE_ORDERED_ITEM.match(line)
            if olm:
                output.append(f"{olm.group(1)}. {olm.group(2)}")
                i += 1
                continue

            # ---- Heuristic: bullet list item --------------------------------
            blm = _RE_BULLET_ITEM.match(line)
            if blm:
                output.append(f"- {blm.group(1)}")
                i += 1
                continue

            # ---- Paragraph: accumulate consecutive non-blank lines ----------
            para: list[str] = [line]
            i += 1
            while i < n:
                next_line = lines[i].strip()
                if not next_line:
                    break
                # Don't absorb lines that look like headings or list items.
                if _RE_HEADING_CAPS.match(next_line):
                    break
                if _RE_ORDERED_ITEM.match(next_line):
                    break
                if _RE_BULLET_ITEM.match(next_line):
                    break
                para.append(next_line)
                i += 1

            output.append(" ".join(para))

        return "\n\n".join(output) + "\n"
