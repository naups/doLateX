"""Web app tests for doLatex using httpx."""

from __future__ import annotations

import io
import pytest
from httpx import AsyncClient, ASGITransport

from dolatex.web import app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
async def client() -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------

class TestIndex:
    async def test_index_returns_html(self, client: AsyncClient) -> None:
        resp = await client.get("/")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/html")
        assert "doLaTeX" in resp.text

    async def test_index_has_converter_ui(self, client: AsyncClient) -> None:
        resp = await client.get("/")
        assert "markdown-input" in resp.text
        assert "latex-output" in resp.text
        assert "convert-btn" in resp.text


# ---------------------------------------------------------------------------
# POST /convert
# ---------------------------------------------------------------------------

class TestConvertEndpoint:
    async def test_convert_markdown(self, client: AsyncClient) -> None:
        resp = await client.post("/convert", data={"markdown": "# Hello\n\nWorld.\n"})
        assert resp.status_code == 200
        data = resp.json()
        assert "latex_result" in data
        assert r"\section{Hello}" in data["latex_result"]

    async def test_convert_bold_text(self, client: AsyncClient) -> None:
        resp = await client.post("/convert", data={"markdown": "This is **bold**.\n"})
        assert resp.status_code == 200
        data = resp.json()
        assert r"\textbf{bold}" in data["latex_result"]

    async def test_convert_empty(self, client: AsyncClient) -> None:
        resp = await client.post("/convert", data={"markdown": ""})
        assert resp.status_code == 200
        data = resp.json()
        assert "latex_result" in data

    async def test_convert_missing_field(self, client: AsyncClient) -> None:
        resp = await client.post("/convert", data={})
        # With default="", missing field defaults to empty string.
        assert resp.status_code == 200
        data = resp.json()
        assert "latex_result" in data

    async def test_convert_with_preserve_format(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/convert",
            data={"markdown": "# Hello\n\nWorld.\n", "preserve_format": "true", "template": "base"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert r"\chapter{Hello}" in data["latex_result"]

    async def test_convert_preserve_format_default_template(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/convert",
            data={"markdown": "# Hello\n\nWorld.\n", "preserve_format": "true"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert r"\chapter{Hello}" in data["latex_result"]


# ---------------------------------------------------------------------------
# POST /upload
# ---------------------------------------------------------------------------

class TestUploadEndpoint:
    async def test_upload_markdown_file(self, client: AsyncClient) -> None:
        content = b"# Uploaded\n\nContent.\n"
        files = {"file": ("test.md", io.BytesIO(content), "text/markdown")}
        resp = await client.post("/upload", files=files)
        assert resp.status_code == 200
        data = resp.json()
        assert r"\section{Uploaded}" in data["latex_result"]

    async def test_upload_txt_file(self, client: AsyncClient) -> None:
        content = b"**Bold** in a text file.\n"
        files = {"file": ("test.txt", io.BytesIO(content), "text/plain")}
        resp = await client.post("/upload", files=files)
        assert resp.status_code == 200
        data = resp.json()
        assert r"\textbf{Bold}" in data["latex_result"]


# ---------------------------------------------------------------------------
# POST /download
# ---------------------------------------------------------------------------

class TestDownloadEndpoint:
    async def test_download_latex(self, client: AsyncClient) -> None:
        resp = await client.post("/download", data={"markdown": "# Doc\n\nBody.\n"})
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/x-tex"
        assert "attachment; filename=output.tex" in resp.headers["content-disposition"]
        assert r"\section{Doc}" in resp.text

    async def test_download_with_preserve_format(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/download",
            data={"markdown": "# Doc\n\nBody.\n", "preserve_format": "true"},
        )
        assert resp.status_code == 200
        assert r"\chapter{Doc}" in resp.text


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------

class TestHealth:
    async def test_health(self, client: AsyncClient) -> None:
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}
