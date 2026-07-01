"""Unit tests for the LatexConverter class.

Tests cover all Markdown elements and edge cases.
"""

from __future__ import annotations

import pytest

from dolatex.converter import LatexConverter, _escape_latex


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def converter() -> LatexConverter:
    return LatexConverter()


# ---------------------------------------------------------------------------
# _escape_latex
# ---------------------------------------------------------------------------

class TestEscapeLatex:
    def test_escapes_special_chars(self) -> None:
        result = _escape_latex("# $ % & _ { } ~ ^ \\")
        assert "\\#" in result
        assert "\\$" in result
        assert "\\%" in result
        assert "\\&" in result
        assert "\\_" in result
        assert "\\{" in result
        assert "\\}" in result
        assert "\\textasciitilde{}" in result
        assert "\\textasciicircum{}" in result
        assert "\\textbackslash{}" in result

    def test_plain_text_unchanged(self) -> None:
        assert _escape_latex("hello world") == "hello world"

    def test_numbers_and_punctuation(self) -> None:
        assert _escape_latex("12345,.;:!?") == "12345,.;:!?"

    def test_quotes(self) -> None:
        assert _escape_latex("'single' \"double\"") == "'single' \"double\""


# ---------------------------------------------------------------------------
# Headings
# ---------------------------------------------------------------------------

class TestHeadings:
    def test_h1(self, converter: LatexConverter) -> None:
        result = converter.convert("# Introduction\n\nSome text.", complete=False)
        assert r"\section{Introduction}" in result

    def test_h2(self, converter: LatexConverter) -> None:
        result = converter.convert("## Background\n\nText.", complete=False)
        assert r"\subsection{Background}" in result

    def test_h3(self, converter: LatexConverter) -> None:
        result = converter.convert("### Details\n\nText.", complete=False)
        assert r"\subsubsection{Details}" in result

    def test_h4(self, converter: LatexConverter) -> None:
        result = converter.convert("#### Note\n\nText.", complete=False)
        assert r"\paragraph{Note}" in result

    def test_h5(self, converter: LatexConverter) -> None:
        result = converter.convert("##### Deep\n\nText.", complete=False)
        assert r"\subparagraph{Deep}" in result

    def test_h6(self, converter: LatexConverter) -> None:
        result = converter.convert("###### Deepest\n\nText.", complete=False)
        assert r"\subparagraph{Deepest}" in result

    def test_heading_with_trailing_hashes(self, converter: LatexConverter) -> None:
        result = converter.convert("# Title #\n\nBody.", complete=False)
        assert r"\section{Title}" in result

    def test_heading_with_special_chars(self, converter: LatexConverter) -> None:
        result = converter.convert("# Cost: $50 & more\n\nBody.", complete=False)
        assert r"\section{Cost: \$50 \& more}" in result


# ---------------------------------------------------------------------------
# Bold & Italic
# ---------------------------------------------------------------------------

class TestBoldItalic:
    def test_bold(self, converter: LatexConverter) -> None:
        result = converter.convert("This is **bold** text.", complete=False)
        assert r"\textbf{bold}" in result

    def test_italic(self, converter: LatexConverter) -> None:
        result = converter.convert("This is *italic* text.", complete=False)
        assert r"\textit{italic}" in result

    def test_bold_italic_combined(self, converter: LatexConverter) -> None:
        result = converter.convert("This is ***both*** styles.", complete=False)
        assert r"\textbf{\textit{both}}" in result

    def test_bold_inside_paragraph(self, converter: LatexConverter) -> None:
        result = converter.convert("A **bold** word in a paragraph.", complete=False)
        assert r"\textbf{bold}" in result


# ---------------------------------------------------------------------------
# Inline code
# ---------------------------------------------------------------------------

class TestInlineCode:
    def test_inline_code(self, converter: LatexConverter) -> None:
        result = converter.convert("Use the `print()` function.", complete=False)
        assert r"\texttt{print()}" in result

    def test_inline_code_special_chars(self, converter: LatexConverter) -> None:
        result = converter.convert("Escape `# $ % & _ { }` in code.", complete=False)
        assert r"\texttt{" in result
        assert r"\#" in result


# ---------------------------------------------------------------------------
# Code blocks
# ---------------------------------------------------------------------------

class TestCodeBlocks:
    def test_code_block_no_lang(self, converter: LatexConverter) -> None:
        md = "```\nprint('hello')\n```\n"
        result = converter.convert(md, complete=False)
        assert r"\begin{verbatim}" in result
        assert r"\end{verbatim}" in result
        assert "print('hello')" in result

    def test_code_block_with_language(self, converter: LatexConverter) -> None:
        md = "```python\nprint('hello')\n```\n"
        result = converter.convert(md, complete=False)
        assert r"\begin{lstlisting}[language=python]" in result
        assert r"\end{lstlisting}" in result
        assert "print('hello')" in result

    def test_code_block_multiline(self, converter: LatexConverter) -> None:
        md = "```\ndef foo():\n    pass\n```\n"
        result = converter.convert(md, complete=False)
        assert "def foo():" in result
        assert "    pass" in result


# ---------------------------------------------------------------------------
# Lists
# ---------------------------------------------------------------------------

class TestLists:
    def test_unordered_list_simple(self, converter: LatexConverter) -> None:
        md = "- Item A\n- Item B\n- Item C\n"
        result = converter.convert(md, complete=False)
        assert r"\begin{itemize}" in result
        assert r"\end{itemize}" in result
        assert r"\item Item A" in result
        assert r"\item Item B" in result
        assert r"\item Item C" in result

    def test_unordered_list_asterisk(self, converter: LatexConverter) -> None:
        md = "* Item 1\n* Item 2\n"
        result = converter.convert(md, complete=False)
        assert r"\begin{itemize}" in result
        assert r"\end{itemize}" in result
        assert r"\item Item 1" in result

    def test_ordered_list(self, converter: LatexConverter) -> None:
        md = "1. First\n2. Second\n3. Third\n"
        result = converter.convert(md, complete=False)
        assert r"\begin{enumerate}" in result
        assert r"\end{enumerate}" in result
        assert r"\item First" in result
        assert r"\item Second" in result
        assert r"\item Third" in result


# ---------------------------------------------------------------------------
# Links
# ---------------------------------------------------------------------------

class TestLinks:
    def test_link(self, converter: LatexConverter) -> None:
        result = converter.convert("Click [here](https://example.com).", complete=False)
        assert r"\href{https://example.com}{here}" in result

    def test_link_with_formatting(self, converter: LatexConverter) -> None:
        result = converter.convert(
            "A [**bold link**](https://example.com).", complete=False
        )
        assert r"\href{https://example.com}{\textbf{bold link}}" in result


# ---------------------------------------------------------------------------
# Images
# ---------------------------------------------------------------------------

class TestImages:
    def test_image(self, converter: LatexConverter) -> None:
        result = converter.convert(
            "![alt text](image.png)", complete=False
        )
        assert r"\includegraphics[width=\textwidth]{image.png}" in result

    def test_image_alt_text(self, converter: LatexConverter) -> None:
        result = converter.convert(
            "![A diagram](fig1.png)", complete=False
        )
        assert r"\includegraphics" in result
        assert r"{fig1.png}" in result


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------

class TestTables:
    def test_simple_table(self, converter: LatexConverter) -> None:
        md = (
            "| Name | Age |\n"
            "|------|-----|\n"
            "| Alice | 30 |\n"
            "| Bob   | 25 |\n"
        )
        result = converter.convert(md, complete=False)
        assert r"\begin{tabular}" in result
        assert r"\end{tabular}" in result
        assert r"\toprule" in result
        assert r"\midrule" in result
        assert r"\bottomrule" in result
        assert "Name" in result
        assert "Age" in result
        assert "Alice" in result
        assert "Bob" in result


# ---------------------------------------------------------------------------
# Math
# ---------------------------------------------------------------------------

class TestMath:
    def test_inline_math_passthrough(self, converter: LatexConverter) -> None:
        result = converter.convert("Einstein's $E = mc^2$ is famous.", complete=False)
        assert "$E = mc^2$" in result

    def test_display_math_passthrough(self, converter: LatexConverter) -> None:
        md = "$$\n\\int_{0}^{\\infty} e^{-x} dx\n$$\n"
        result = converter.convert(md, complete=False)
        assert "$$" in result
        assert r"\int_{0}^{\infty} e^{-x} dx" in result


# ---------------------------------------------------------------------------
# Horizontal rules
# ---------------------------------------------------------------------------

class TestHorizontalRules:
    def test_hrule_dashes(self, converter: LatexConverter) -> None:
        result = converter.convert("---\n", complete=False)
        assert r"\hrule" in result

    def test_hrule_asterisks(self, converter: LatexConverter) -> None:
        result = converter.convert("***\n", complete=False)
        assert r"\hrule" in result

    def test_hrule_underscores(self, converter: LatexConverter) -> None:
        result = converter.convert("___\n", complete=False)
        assert r"\hrule" in result


# ---------------------------------------------------------------------------
# Blockquotes
# ---------------------------------------------------------------------------

class TestBlockquotes:
    def test_blockquote_single_line(self, converter: LatexConverter) -> None:
        result = converter.convert("> This is a quote.\n", complete=False)
        assert r"\begin{quote}" in result
        assert r"\end{quote}" in result
        assert "This is a quote" in result

    def test_blockquote_multiple_lines(self, converter: LatexConverter) -> None:
        md = "> Line one\n> Line two\n"
        result = converter.convert(md, complete=False)
        assert r"\begin{quote}" in result
        assert "Line one" in result
        assert "Line two" in result
        assert r"\end{quote}" in result


# ---------------------------------------------------------------------------
# Complete document
# ---------------------------------------------------------------------------

class TestCompleteDocument:
    def test_document_structure(self, converter: LatexConverter) -> None:
        result = converter.convert("# Title\n\nBody.\n")
        assert r"\documentclass" in result
        assert r"\begin{document}" in result
        assert r"\title{Title}" in result
        assert r"\maketitle" in result
        assert r"\end{document}" in result
        assert r"\section{Title}" in result

    def test_custom_preamble(self) -> None:
        conv = LatexConverter(custom_preamble="\\usepackage{extra}")
        result = conv.convert("Hello", complete=True)
        assert "\\usepackage{extra}" in result

    def test_custom_title_author(self) -> None:
        conv = LatexConverter(title="My Doc", author="Jane Doe")
        result = conv.convert("Content.", complete=True)
        assert r"\title{My Doc}" in result
        assert r"\author{Jane Doe}" in result
        assert r"\maketitle" in result

    def test_body_only(self, converter: LatexConverter) -> None:
        result = converter.convert("Just body text.", complete=False)
        assert r"\documentclass" not in result
        assert r"\begin{document}" not in result

    def test_preserve_format_uses_chapter(self, converter: LatexConverter) -> None:
        conv = LatexConverter(preserve_format=True, template_name="base")
        result = conv.convert("# Introduction\n\nContent.\n")
        assert r"\chapter{Introduction}" in result
        assert r"\documentclass" in result

    def test_preserve_format_heading_mapping(self, converter: LatexConverter) -> None:
        conv = LatexConverter(preserve_format=True, template_name="base")
        md = "# H1\n## H2\n### H3\n#### H4\n"
        result = conv.convert(md, complete=False)
        assert r"\chapter{H1}" in result
        assert r"\section{H2}" in result
        assert r"\subsection{H3}" in result
        assert r"\subsubsection{H4}" in result

    def test_preserve_format_template_base(self, converter: LatexConverter) -> None:
        from dolatex.format import DocumentFormat
        fmt = DocumentFormat()
        conv = LatexConverter(preserve_format=True, template_name="base", doc_format=fmt.to_template_vars())
        result = conv.convert("# Title\n\nBody.\n")
        assert r"\documentclass" in result
        assert r"\begin{document}" in result
        assert r"\end{document}" in result

    def test_legacy_mode_still_works(self, converter: LatexConverter) -> None:
        """Existing tests must still pass — no preserve flag."""
        result = converter.convert("# Hello\n\nWorld.\n")
        assert r"\section{Hello}" in result
        assert r"\documentclass[11pt,a4paper]{article}" in result

    def test_regression_legacy_output_structure(self, converter: LatexConverter) -> None:
        """Complete document output with preserve_format=False must match old format."""
        result = converter.convert("# Title\n\nBody.\n")
        assert r"\documentclass[11pt,a4paper]{article}" in result
        assert r"\section{Title}" in result
        assert r"\begin{document}" in result
        assert r"\end{document}" in result

    def test_preserve_format_body_only(self, converter: LatexConverter) -> None:
        conv = LatexConverter(preserve_format=True)
        result = conv.convert("# Title\n\nBody.\n", complete=False)
        assert r"\chapter{Title}" in result
        assert r"\documentclass" not in result

    def test_preserve_format_with_custom_metadata(self, converter: LatexConverter) -> None:
        from dolatex.format import DocumentFormat
        conv = LatexConverter(
            preserve_format=True,
            template_name="base",
            title="My Thesis",
            author="Student",
            doc_format=DocumentFormat().to_template_vars(),
        )
        result = conv.convert("# Title\n\nBody.\n")
        assert r"\title{My Thesis}" in result
        assert r"\author{Student}" in result
        assert r"\chapter{Title}" in result


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_input(self, converter: LatexConverter) -> None:
        result = converter.convert("", complete=False)
        assert result.strip() == ""

    def test_only_whitespace(self, converter: LatexConverter) -> None:
        result = converter.convert("   \n\n  \n", complete=False)
        assert result.strip() == ""

    def test_only_special_chars(self, converter: LatexConverter) -> None:
        result = converter.convert("# $ % & _ { } ~ ^ \\\n", complete=False)
        # Should not crash
        assert result is not None
        assert len(result) > 0

    def test_consecutive_blank_lines(self, converter: LatexConverter) -> None:
        result = converter.convert("Para1.\n\n\n\nPara2.\n", complete=False)
        assert "Para1" in result
        assert "Para2" in result

    def test_mixed_bold_italic_in_heading(self, converter: LatexConverter) -> None:
        result = converter.convert(
            "# **Title** with *emphasis*\n\nBody.\n", complete=False
        )
        assert r"\textbf{Title}" in result
        assert r"\textit{emphasis}" in result

    def test_html_comments_ignored(self, converter: LatexConverter) -> None:
        result = converter.convert("<!-- comment -->\nNot a comment.\n", complete=False)
        assert "<!--" not in result
        assert "-->" not in result
        assert "Not a comment" in result


class TestDocxFormatExtraction:
    def test_extract_format_from_docx_returns_defaults_on_missing_file(self):
        """Should return DocumentFormat with defaults when python-docx unavailable or file missing."""
        from dolatex.format import DocumentFormat

        result = DocumentFormat()
        assert result.page_size == "a4paper"
        assert result.font_family == "calibri"
        assert result.margin_left == "4cm"
