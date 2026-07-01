"""doLatex: Document to LaTeX converter."""

from .converter import LatexConverter
from .readers import read_document, read_text, supported_extensions

__version__ = "0.2.0"
__all__ = [
    "LatexConverter",
    "read_document",
    "read_text",
    "supported_extensions",
]
