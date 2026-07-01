"""Format metadata dataclasses for document-to-LaTeX conversion.

Holds extracted formatting information (margins, fonts, spacing, alignment)
from original documents (DOCX, PDF) so the LaTeX output can preserve them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ParaFormat:
    """Per-paragraph formatting override."""

    index: int
    alignment: str = "justified"  # justified, left, center, right
    first_line_indent: Optional[str] = None


@dataclass
class DocumentFormat:
    """Format metadata extracted from original document.

    Defaults reflect the most common Indonesian thesis layout (FILKOM UB).
    """

    # Page layout
    page_size: str = "a4paper"
    margin_top: str = "3cm"
    margin_bottom: str = "3cm"
    margin_left: str = "4cm"
    margin_right: str = "3cm"
    orientation: str = "portrait"

    # Typography
    font_family: str = "calibri"
    body_font_size: str = "12pt"
    heading_sizes: dict[int, str] = field(
        default_factory=lambda: {1: "16pt", 2: "14pt", 3: "14pt", 4: "12pt"}
    )
    line_spacing: float = 1.0

    # Paragraph defaults
    alignment: str = "justified"
    first_line_indent: str = "1.27cm"
    paragraph_spacing: str = "0pt"

    # Per-paragraph overrides
    paragraph_formats: Optional[list[ParaFormat]] = None

    def to_template_vars(self) -> dict[str, str]:
        """Flatten to a dict suitable for Jinja2 template rendering."""
        return {
            "page_size": self.page_size,
            "margin_top": self.margin_top,
            "margin_bottom": self.margin_bottom,
            "margin_left": self.margin_left,
            "margin_right": self.margin_right,
            "orientation": self.orientation,
            "font_family": self.font_family,
            "body_font_size": self.body_font_size,
            "heading_1_size": self.heading_sizes.get(1, "16pt"),
            "heading_2_size": self.heading_sizes.get(2, "14pt"),
            "heading_3_size": self.heading_sizes.get(3, "14pt"),
            "heading_4_size": self.heading_sizes.get(4, "12pt"),
            "line_spacing": str(self.line_spacing),
            "alignment": self.alignment,
            "first_line_indent": self.first_line_indent,
            "paragraph_spacing": self.paragraph_spacing,
        }
