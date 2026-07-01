"""FastAPI web application for doLatex.

Provides a REST API and serves the browser-based converter UI.
Supports Markdown (``.md``), Word (``.docx``), and PDF (``.pdf``) uploads.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Form, UploadFile, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .converter import LatexConverter
from .readers import read_text, supported_extensions


# ---------------------------------------------------------------------------
# Template cache workaround (Jinja2 LRUCache on Python 3.14+ cannot handle
# unhashable cache keys containing dicts).
# ---------------------------------------------------------------------------


class _SafeCache(dict[Any, Any]):
    """A dict that silently skips unhashable keys instead of raising."""

    def get(self, key: Any, default: Any = None) -> Any:
        try:
            return dict.get(self, key, default)
        except TypeError:
            return default

    def __setitem__(self, key: Any, value: Any) -> None:
        try:
            dict.__setitem__(self, key, value)
        except TypeError:
            pass


# ---------------------------------------------------------------------------
# Application setup
# ---------------------------------------------------------------------------

_HERE = Path(__file__).resolve().parent

app = FastAPI(title="doLatex", version="0.2.0")

# Static files
static_dir = _HERE / "static"
if static_dir.is_dir():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Templates
templates_dir = _HERE / "templates"
templates = Jinja2Templates(directory=str(templates_dir))
templates.env.cache = _SafeCache()

converter = LatexConverter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ALLOWED_EXTENSIONS: frozenset[str] = supported_extensions()


def _extract_markdown(content: bytes, filename: str) -> str:
    """Extract Markdown text from *content* using the appropriate reader."""
    ext = Path(filename).suffix.lower()
    if ext not in _ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Unsupported format {ext!r}. "
            f"Allowed: {', '.join(sorted(_ALLOWED_EXTENSIONS))}"
        )
    try:
        return read_text(content, ext)
    except UnicodeDecodeError:
        raise ValueError("Could not decode file content.")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """Render the main converter UI."""
    return templates.TemplateResponse(request, "index.html", {"request": request})


@app.post("/convert")
async def convert_markdown(markdown: str = Form(default="")) -> dict:
    """Accept Markdown text, return LaTeX result as JSON."""
    latex = converter.convert(markdown)
    return {"latex_result": latex}


@app.post("/upload")
async def upload_file(file: UploadFile) -> dict:
    """Accept an uploaded file (``.md``, ``.docx``, ``.pdf``), return LaTeX JSON."""
    content = await file.read()
    filename = file.filename or "document.md"
    try:
        markdown_text = _extract_markdown(content, filename)
        latex = converter.convert(markdown_text)
        return {
            "latex_result": latex,
            "markdown_text": markdown_text,
            "filename": filename,
        }
    except ValueError as exc:
        return {
            "latex_result": "",
            "markdown_text": "",
            "error": str(exc),
        }


def _extract_markdown(content: bytes, filename: str) -> str:
    """Extract Markdown text from *content* using the appropriate reader."""
    ext = Path(filename).suffix.lower()
    if ext not in _ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Unsupported format {ext!r}. "
            f"Allowed: {', '.join(sorted(_ALLOWED_EXTENSIONS))}"
        )
    try:
        return read_text(content, ext)
    except UnicodeDecodeError:
        raise ValueError("Could not decode file content.")


@app.post("/download")
async def download_latex(markdown: str = Form(default="")) -> Response:
    """Accept Markdown text, return .tex file as a download."""
    latex = converter.convert(markdown)
    return PlainTextResponse(
        content=latex,
        media_type="application/x-tex",
        headers={"Content-Disposition": "attachment; filename=output.tex"},
    )


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
