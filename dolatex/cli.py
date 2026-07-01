"""Command-line interface for doLatex.

Provides ``convert`` (file/stdin → LaTeX) and ``serve`` (web server) commands.
Auto-detects input format from file extension (``.md``, ``.docx``, ``.pdf``, …).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import click

from .converter import LatexConverter
from .readers import read_document, supported_extensions


# ---------------------------------------------------------------------------
# Shared options
# ---------------------------------------------------------------------------

_CONVERTER_OPTIONS = [
    click.option("--document-class", default="article", help="LaTeX document class"),
    click.option("--font-size", default="11pt", help="Font size (e.g. 11pt, 12pt)"),
    click.option("--geometry", default="a4paper", help="Page geometry (e.g. a4paper, letterpaper)"),
    click.option("--title", default=None, help="Document title"),
    click.option("--author", default=None, help="Document author"),
]


def _apply_options(decorators):
    """Apply a list of decorators in reverse order (bottom-up)."""
    def wrapper(f):
        for decorator in reversed(decorators):
            f = decorator(f)
        return f
    return wrapper


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@click.group()
def cli() -> None:
    """doLatex — Convert Markdown documents to LaTeX."""


@cli.command()
@click.option("-i", "--input", "input_file", type=click.Path(exists=True, dir_okay=False),
              help=f"Input file ({', '.join(supported_extensions())} — auto-detected)")
@click.option("-o", "--output", "output_file", type=click.Path(dir_okay=False),
              help="Output .tex file (defaults to stdout)")
@click.option("--stdin", "read_stdin", is_flag=True, default=False,
              help="Read Markdown from stdin (text only)")
@click.option("--format", "format_hint", type=click.Choice(["md", "docx", "pdf"]),
              default=None,
              help="Input format (auto-detected from extension when possible)")
@_apply_options(_CONVERTER_OPTIONS)
@click.option("--no-complete", "no_complete", is_flag=True, default=False,
              help="Output only the body, not a complete document")
def convert(
    input_file: Optional[str],
    output_file: Optional[str],
    read_stdin: bool,
    format_hint: Optional[str],
    document_class: str,
    font_size: str,
    geometry: str,
    title: Optional[str],
    author: Optional[str],
    no_complete: bool,
) -> None:
    """Convert a document to LaTeX.

    Supports Markdown (``.md``, ``.txt``), Word (``.docx``), and PDF (``.pdf``).
    Input format is auto-detected from the file extension.
    """
    # --- Read input ----------------------------------------------------------
    if input_file is not None:
        markdown_text = read_document(input_file)
    elif read_stdin:
        markdown_text = click.get_text_stream("stdin").read()
    else:
        click.echo("Error: provide input via -i/--input or --stdin", err=True)
        sys.exit(1)

    # --- Convert -------------------------------------------------------------
    converter = LatexConverter(
        document_class=document_class,
        font_size=font_size,
        geometry=geometry,
        title=title,
        author=author,
    )
    latex = converter.convert(markdown_text, complete=not no_complete)

    # --- Write output --------------------------------------------------------
    if output_file:
        Path(output_file).write_text(latex, encoding="utf-8")
        click.echo(f"Written to {output_file}")
    else:
        click.echo(latex)


@cli.command()
@click.option("--host", default="127.0.0.1", help="Host to bind to")
@click.option("--port", default=5000, type=int, help="Port to listen on")
@click.option("--debug", is_flag=True, default=False, help="Enable debug mode")
def serve(host: str, port: int, debug: bool) -> None:
    """Start the doLatex web server."""
    try:
        import uvicorn
    except ImportError:
        click.echo(
            "Error: uvicorn is required to run the server. "
            "Install with: pip install dolatex[web] or uvicorn",
            err=True,
        )
        sys.exit(1)

    click.echo(f"Starting doLatex server on http://{host}:{port}")
    uvicorn.run(
        "dolatex.web:app",
        host=host,
        port=port,
        reload=debug,
        log_level="debug" if debug else "info",
    )


if __name__ == "__main__":
    cli()
