"""Abstract base class for document readers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from dolatex.format import DocumentFormat


class DocumentReader(ABC):
    """Base class for all document format readers.

    Each subclass implements :meth:`read` to convert a document file into
    plain Markdown text that can be fed to :class:`dolatex.converter.LatexConverter`.
    """

    @abstractmethod
    def read(self, path: Path) -> str:
        """Read a document file and return its content as Markdown text.

        Parameters
        ----------
        path:
            Path to the document file.

        Returns
        -------
        str
            Markdown representation of the document content.
        """
        ...

    @abstractmethod
    def extensions(self) -> frozenset[str]:
        """Return the set of file extensions this reader supports.

        Extensions should be lower-case and include the leading dot, e.g.
        ``{".md", ".markdown"}``.
        """
        ...

    def extract_format(self, data: str | bytes | Path) -> Optional[DocumentFormat]:
        """Extract format metadata from *data*.

        Returns ``None`` to signal "format extraction not supported".
        Subclasses that support format extraction should override this.
        """
        return None
