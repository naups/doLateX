"""Markdown-to-LaTeX converter.

Provides a state-machine-based converter that transforms Markdown text
into valid LaTeX documents or fragments.
"""

from __future__ import annotations

import re
from typing import Final, Optional

# ---------------------------------------------------------------------------
# Regex helpers
# ---------------------------------------------------------------------------

_RE_HEADING: Final[re.Pattern] = re.compile(r"^(#{1,6})\s+(.+?)(?:\s+#+)?\s*$")
_RE_BOLD_ITALIC: Final[re.Pattern] = re.compile(r"\*\*\*(.+?)\*\*\*")
_RE_BOLD: Final[re.Pattern] = re.compile(r"\*\*(.+?)\*\*")
_RE_ITALIC: Final[re.Pattern] = re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)")
_RE_INLINE_CODE: Final[re.Pattern] = re.compile(r"`(.+?)`")
_RE_LINK: Final[re.Pattern] = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_RE_IMAGE: Final[re.Pattern] = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
_RE_ORDERED_LIST: Final[re.Pattern] = re.compile(r"^\s*(\d+)\.\s+(.+)$")
_RE_UNORDERED_LIST: Final[re.Pattern] = re.compile(r"^\s*[-*+]\s+(.+)$")
_RE_HORIZONTAL_RULE: Final[re.Pattern] = re.compile(
    r"^\s*[-*_]\s*[-*_]\s*[-*_](?:\s*[-*_])*\s*$"
)
_RE_BLOCKQUOTE: Final[re.Pattern] = re.compile(r"^>\s?(.*)$")
_RE_TABLE_SEPARATOR: Final[re.Pattern] = re.compile(r"^\|?[\s:-]+(?:\|[\s:-]+)*\|?$")
_RE_TABLE_ROW: Final[re.Pattern] = re.compile(r"^\|(.+)\|$")
_RE_CODE_FENCE_START: Final[re.Pattern] = re.compile(r"^```(\w*)\s*$")
_RE_CODE_FENCE_END: Final[re.Pattern] = re.compile(r"^```\s*$")
_RE_INLINE_MATH: Final[re.Pattern] = re.compile(r"\$(.+?)\$")
_RE_DISPLAY_MATH: Final[re.Pattern] = re.compile(r"\$\$(.+?)\$\$", re.DOTALL)

# Characters that must be escaped in LaTeX (outside math mode and verbatim).
_LATEX_SPECIAL: Final[dict[str, str]] = {
    "#": r"\#",
    "$": r"\$",
    "%": r"\%",
    "&": r"\&",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
    "\\": r"\textbackslash{}",
}


_BACKSLASH_PLACEHOLDER = "\x00BS\x00"


def _escape_latex(text: str) -> str:
    """Escape LaTeX special characters in *text*.

    Backslash is replaced with a placeholder first, then all other special
    characters are escaped, then the placeholder is restored to
    ``\\textbackslash{}``.  This ordering prevents the braces inside
    ``\\textbackslash{}`` from being re-escaped.
    """
    # 1. Protect backslashes with a placeholder.
    result = text.replace("\\", _BACKSLASH_PLACEHOLDER)
    # 2. Escape every other special character (backslash is already hidden).
    for ch, replacement in _LATEX_SPECIAL.items():
        if ch != "\\":
            result = result.replace(ch, replacement)
    # 3. Restore backslash placeholders to the real LaTeX command.
    result = result.replace(_BACKSLASH_PLACEHOLDER, r"\textbackslash{}")
    return result


# ---------------------------------------------------------------------------
# State machine types
# ---------------------------------------------------------------------------


class _ListStackEntry:
    """Tracks a single level of nesting for lists."""

    __slots__ = ("ordered", "items")

    def __init__(self, ordered: bool) -> None:
        self.ordered = ordered
        self.items: list[str] = []


class _BlockState:
    """Mutable state carried through a single convert() call."""

    __slots__ = (
        "lines",
        "output",
        "i",
        "n",
        "list_stack",
        "in_blockquote",
        "in_code_block",
        "code_block_lang",
        "code_block_lines",
        "in_html_comment",
    )

    def __init__(self, lines: list[str]) -> None:
        self.lines = lines
        self.output: list[str] = []
        self.i = 0
        self.n = len(lines)
        self.list_stack: list[_ListStackEntry] = []
        self.in_blockquote = False
        self.in_code_block = False
        self.code_block_lang: str = ""
        self.code_block_lines: list[str] = []
        self.in_html_comment = False


# ---------------------------------------------------------------------------
# Main converter class
# ---------------------------------------------------------------------------

DEFAULT_PREAMBLE: Final[str] = (
    r"\usepackage[utf8]{inputenc}" + "\n"
    r"\usepackage[T1]{fontenc}" + "\n"
    r"\usepackage{hyperref}" + "\n"
    r"\usepackage{graphicx}" + "\n"
    r"\usepackage{listings}" + "\n"
    r"\usepackage{amsmath}" + "\n"
    r"\usepackage{booktabs}"
)


class LatexConverter:
    """Markdown-to-LaTeX converter using a line-by-line state machine.

    Constructor parameters control the structure of the generated document.
    Set *title*, *author*, and *date* to override automatic detection.
    """

    def __init__(
        self,
        document_class: str = "article",
        font_size: str = "11pt",
        geometry: str = "a4paper",
        custom_preamble: str = "",
        title: Optional[str] = None,
        author: Optional[str] = None,
        date: Optional[str] = None,
        *,
        preserve_format: bool = False,
        template_name: str = "base",
        doc_format: Optional[dict] = None,
    ) -> None:
        self.document_class = document_class
        self.font_size = font_size
        self.geometry = geometry
        self.custom_preamble = custom_preamble
        self.title = title
        self.author = author
        self.date = date
        self.preserve_format = preserve_format
        self.template_name = template_name
        self.doc_format = doc_format or {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def convert(self, markdown_text: str, *, complete: bool = True) -> str:
        """Convert *markdown_text* to LaTeX.

        Parameters
        ----------
        markdown_text:
            The raw Markdown string to convert.
        complete:
            If *True* (the default) wrap the body in a full LaTeX document
            preamble and ``\\begin{{document}}`` ... ``\\end{{document}}``.

        Returns
        -------
        str
            The resulting LaTeX source.
        """
        lines = markdown_text.splitlines(keepends=False)
        state = _BlockState(lines)
        body = self._convert_body(state)

        if not complete:
            return body

        return self._wrap_document(body)

    # ------------------------------------------------------------------
    # Wrapping
    # ------------------------------------------------------------------

    def _wrap_document(self, body: str) -> str:
        """Wrap *body* in a complete LaTeX document structure."""
        title_block = self._build_title_block(body)

        if self.preserve_format:
            # Generate preamble from template
            from dolatex.template import TemplateEngine
            engine = TemplateEngine()
            preamble = engine.render(self.template_name, self.doc_format)
            parts: list[str] = [preamble]
        else:
            # Traditional preamble
            parts = [
                rf"\documentclass[{self.font_size},{self.geometry}]{{{self.document_class}}}",
                DEFAULT_PREAMBLE,
            ]
            if self.custom_preamble:
                parts.append(self.custom_preamble.strip())

        parts.append("")
        parts.append(r"\begin{document}")
        if title_block:
            parts.append(title_block)
        parts.append("")
        parts.append(body.strip())
        parts.append("")
        parts.append(r"\end{document}")
        return "\n".join(parts) + "\n"

    def _build_title_block(self, body: str) -> str:
        """Build \\title{...}, \\author{...}, \\date{...} and
        \\maketitle from constructor params or the first heading."""
        title = self.title or self._extract_first_heading(body) or "Untitled"
        author = self.author or ""
        date = self.date or r"\today"

        lines: list[str] = [rf"\title{{{title}}}"]
        if author:
            lines.append(rf"\author{{{author}}}")
        lines.append(rf"\date{{{date}}}")
        lines.append(r"\maketitle")
        return "\n".join(lines)

    @staticmethod
    def _extract_first_heading(body: str) -> Optional[str]:
        """Return the text of the first \\section found in *body*, or None."""
        m = re.search(r"\\section\{([^}]+)\}", body)
        if m:
            return m.group(1)
        return None

    # ------------------------------------------------------------------
    # Body conversion (state machine)
    # ------------------------------------------------------------------

    def _convert_body(self, state: _BlockState) -> str:
        """Walk the line list with a state machine and return the LaTeX body."""
        while state.i < state.n:
            line = state.lines[state.i]

            # --- Code fence handling (highest priority) ----------------------
            if state.in_code_block:
                if _RE_CODE_FENCE_END.match(line):
                    self._close_code_block(state)
                    state.i += 1
                    continue
                state.code_block_lines.append(line)
                state.i += 1
                continue

            if _RE_CODE_FENCE_START.match(line):
                m = _RE_CODE_FENCE_START.match(line)
                assert m is not None
                self._close_all_lists(state)
                self._close_blockquote(state)
                state.in_code_block = True
                state.code_block_lang = m.group(1)
                state.code_block_lines = []
                state.i += 1
                continue

            # --- HTML comments (multi-line aware) ----------------------------
            if state.in_html_comment:
                if "-->" in line:
                    state.in_html_comment = False
                state.i += 1
                continue

            if "<!--" in line:
                state.in_html_comment = True
                if "-->" in line:
                    state.in_html_comment = False
                state.i += 1
                continue

            # --- Horizontal rules --------------------------------------------
            if _RE_HORIZONTAL_RULE.match(line):
                self._close_all_lists(state)
                self._close_blockquote(state)
                state.output.append(r"\hrule")
                state.i += 1
                continue

            # --- Headings ----------------------------------------------------
            hm = _RE_HEADING.match(line)
            if hm:
                self._close_all_lists(state)
                self._close_blockquote(state)
                self._append_heading(state, hm)
                state.i += 1
                continue

            # --- Blank lines -------------------------------------------------
            if not line.strip():
                self._handle_blank_line(state)
                state.i += 1
                continue

            # --- Blockquotes -------------------------------------------------
            bqm = _RE_BLOCKQUOTE.match(line)
            if bqm:
                self._close_all_lists(state)
                self._handle_blockquote(state, bqm)
                state.i += 1
                continue
            elif state.in_blockquote:
                self._close_blockquote(state)

            # --- Tables ------------------------------------------------------
            trm = _RE_TABLE_ROW.match(line)
            if trm and state.i + 1 < state.n and _RE_TABLE_SEPARATOR.match(
                state.lines[state.i + 1]
            ):
                self._close_all_lists(state)
                self._close_blockquote(state)
                self._handle_table(state)
                continue

            # --- Lists -------------------------------------------------------
            olm = _RE_ORDERED_LIST.match(line)
            ulm = _RE_UNORDERED_LIST.match(line)
            if olm:
                self._close_blockquote(state)
                content = self._inline_to_latex(olm.group(2))
                self._ensure_list(state, ordered=True)
                state.list_stack[-1].items.append(content)
                state.i += 1
                continue
            if ulm:
                self._close_blockquote(state)
                content = self._inline_to_latex(ulm.group(1))
                self._ensure_list(state, ordered=False)
                state.list_stack[-1].items.append(content)
                state.i += 1
                continue

            # If we were in a list and this line doesn't match, close lists.
            if state.list_stack:
                self._close_all_lists(state)

            # --- Paragraph (everything else) ---------------------------------
            self._handle_paragraph(state)

        # Flush any open structures.
        self._close_all_lists(state)
        self._close_blockquote(state)
        self._close_code_block(state)
        state.in_html_comment = False

        return "\n".join(state.output)

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    def _append_heading(self, state: _BlockState, m: re.Match) -> None:
        """Convert a heading match to the corresponding LaTeX command."""
        level = len(m.group(1))
        text = self._inline_to_latex(m.group(2).strip())

        if self.preserve_format:
            # report class: chapter/section/subsection/subsubsection
            commands = {
                1: "chapter",
                2: "section",
                3: "subsection",
                4: "subsubsection",
            }
        else:
            # article class: section/subsection/subparagraph
            commands = {
                1: "section",
                2: "subsection",
                3: "subsubsection",
                4: "paragraph",
            }

        cmd = commands.get(level, "subparagraph")
        state.output.append(rf"\{cmd}{{{text}}}")

    def _close_code_block(self, state: _BlockState) -> None:
        """Emit the accumulated code block."""
        if not state.in_code_block:
            return
        lang = state.code_block_lang
        code = "\n".join(state.code_block_lines)
        if lang:
            state.output.append(
                rf"\begin{{lstlisting}}[language={_escape_latex(lang)}]"
            )
        else:
            state.output.append(r"\begin{verbatim}")
        state.output.append(code)
        if lang:
            state.output.append(r"\end{lstlisting}")
        else:
            state.output.append(r"\end{verbatim}")
        state.in_code_block = False
        state.code_block_lang = ""
        state.code_block_lines = []

    def _handle_blockquote(self, state: _BlockState, m: re.Match) -> None:
        """Process a single blockquote line."""
        content = m.group(1)
        if not state.in_blockquote:
            state.output.append(r"\begin{quote}")
            state.in_blockquote = True
        converted = self._inline_to_latex(content)
        state.output.append(converted)

    def _close_blockquote(self, state: _BlockState) -> None:
        if state.in_blockquote:
            state.output.append(r"\end{quote}")
            state.in_blockquote = False

    def _handle_table(self, state: _BlockState) -> None:
        """Consume consecutive table rows and emit a LaTeX tabular."""
        header_row = self._parse_table_row(state.lines[state.i])
        state.i += 1  # skip header
        state.i += 1  # skip separator

        rows: list[list[str]] = []
        while state.i < state.n:
            trm = _RE_TABLE_ROW.match(state.lines[state.i])
            if not trm:
                break
            if _RE_TABLE_SEPARATOR.match(state.lines[state.i]):
                break
            rows.append(self._parse_table_row(state.lines[state.i]))
            state.i += 1

        n_cols = max(len(header_row), max((len(r) for r in rows), default=0))
        if n_cols == 0:
            return

        align = self._infer_table_alignment(state, n_cols)

        state.output.append(r"\begin{tabular}{" + align + "}")
        state.output.append(r"\toprule")
        state.output.append(" & ".join(header_row) + r" \\")
        state.output.append(r"\midrule")
        for row in rows:
            padded = list(row) + [""] * (n_cols - len(row))
            state.output.append(" & ".join(padded) + r" \\")
        state.output.append(r"\bottomrule")
        state.output.append(r"\end{tabular}")

    def _parse_table_row(self, line: str) -> list[str]:
        """Split a table row line into cell contents."""
        line = line.strip()
        if line.startswith("|"):
            line = line[1:]
        if line.endswith("|"):
            line = line[:-1]
        cells = [cell.strip() for cell in line.split("|")]
        return [self._inline_to_latex(c) for c in cells]

    def _infer_table_alignment(self, state: _BlockState, n_cols: int) -> str:
        """Look back two lines (the separator row) for alignment."""
        sep_line = state.lines[state.i - 2] if state.i >= 2 else ""
        sep_parts = self._parse_table_row(sep_line) if sep_line else []
        alignments: list[str] = []
        for idx in range(n_cols):
            part = sep_parts[idx] if idx < len(sep_parts) else ""
            left = part.startswith(":")
            right = part.endswith(":")
            if left and right:
                alignments.append("c")
            elif right:
                alignments.append("r")
            elif left:
                alignments.append("l")
            else:
                alignments.append("c")
        return " ".join(alignments)

    def _handle_paragraph(self, state: _BlockState) -> None:
        """Accumulate consecutive non-blank lines as a single paragraph."""
        para_lines: list[str] = []

        while state.i < state.n:
            line = state.lines[state.i]

            if not line.strip():
                break
            if _RE_HEADING.match(line):
                break
            if _RE_ORDERED_LIST.match(line) or _RE_UNORDERED_LIST.match(line):
                break
            if _RE_BLOCKQUOTE.match(line):
                break
            if _RE_HORIZONTAL_RULE.match(line):
                break
            if _RE_CODE_FENCE_START.match(line):
                break
            if _RE_TABLE_ROW.match(line):
                if state.i + 1 < state.n and _RE_TABLE_SEPARATOR.match(
                    state.lines[state.i + 1]
                ):
                    break
            para_lines.append(line)
            state.i += 1

        text = " ".join(para_lines).strip()
        if not text:
            return

        converted = self._inline_to_latex(text)
        state.output.append(converted)
        # A blank line after the paragraph separates it in LaTeX.
        if state.i < state.n and not state.lines[state.i].strip():
            state.output.append("")

    def _handle_blank_line(self, state: _BlockState) -> None:
        """Handle a blank line: emit spacing inside open constructs."""
        if state.in_blockquote:
            state.output.append("")

    # ------------------------------------------------------------------
    # List management
    # ------------------------------------------------------------------

    def _ensure_list(self, state: _BlockState, *, ordered: bool) -> None:
        """Make sure we have an open list of the correct type for items."""
        if state.list_stack and state.list_stack[-1].ordered == ordered:
            return
        state.list_stack.append(_ListStackEntry(ordered))

    def _close_all_lists(self, state: _BlockState) -> None:
        """Close all open list environments."""
        while state.list_stack:
            entry = state.list_stack.pop()
            env = "enumerate" if entry.ordered else "itemize"
            state.output.append(rf"\begin{{{env}}}")
            for item in entry.items:
                state.output.append(rf"\item {item}")
            state.output.append(rf"\end{{{env}}}")

    # ------------------------------------------------------------------
    # Inline conversion
    # ------------------------------------------------------------------

    def _inline_to_latex(self, text: str) -> str:
        """Convert inline Markdown formatting in *text* to LaTeX.

        Uses a placeholder approach so that LaTeX command syntax generated
        by the regex substitutions is not subsequently escaped.  Each
        Markdown construct is replaced with a unique placeholder that
        survives LaTeX escaping.  After escaping the surrounding text,
        placeholders are restored to their proper LaTeX commands.

        Math segments (``$...$``, ``$$...$$``) are protected so that their
        content passes through unchanged.
        """
        if not text:
            return ""

        placeholders: dict[str, str] = {}
        counter: int = 0

        def _mark(replacement: str) -> str:
            nonlocal counter
            key = f"\x00PLACEHOLDER{counter}X\x00"
            placeholders[key] = replacement
            counter += 1
            return key

        # 0. Protect display math ($$...$$) before inline math ($...$).
        text = _RE_DISPLAY_MATH.sub(lambda m: _mark(m.group(0)), text)
        # 1. Protect inline math ($...$).
        text = _RE_INLINE_MATH.sub(lambda m: _mark(m.group(0)), text)
        # 2. Images (must come before links).
        text = _RE_IMAGE.sub(
            lambda m: _mark(
                rf"\includegraphics[width=\textwidth]{{{m.group(2)}}}"
            ),
            text,
        )
        # 3. Links (process inline formatting on link text recursively).
        text = _RE_LINK.sub(
            lambda m: _mark(
                rf"\href{{{_escape_latex(m.group(2))}}}{{{self._inline_to_latex(m.group(1))}}}"
            ),
            text,
        )
        # 4. Inline code (must come before bold/italic so code inside backticks
        #    is treated as literal).
        text = _RE_INLINE_CODE.sub(
            lambda m: _mark(rf"\texttt{{{_escape_latex(m.group(1))}}}"),
            text,
        )
        # 5. Bold + Italic combined (recursively process nested formatting).
        text = _RE_BOLD_ITALIC.sub(
            lambda m: _mark(
                rf"\textbf{{\textit{{{self._inline_to_latex(m.group(1))}}}}}"
            ),
            text,
        )
        # 6. Bold (recursively process nested formatting).
        text = _RE_BOLD.sub(
            lambda m: _mark(rf"\textbf{{{self._inline_to_latex(m.group(1))}}}"),
            text,
        )
        # 7. Italic (recursively process nested formatting).
        text = _RE_ITALIC.sub(
            lambda m: _mark(rf"\textit{{{self._inline_to_latex(m.group(1))}}}"),
            text,
        )

        # Escape remaining special characters in the text.
        text = _escape_latex(text)

        # Restore placeholders in reverse insertion order (innermost first)
        # so that inner placeholders referenced by outer replacements are
        # resolved before the outer placeholder is itself restored.
        for key, replacement in reversed(list(placeholders.items())):
            text = text.replace(key, replacement)

        return text
