"""CLI tests for doLatex using Click's CliRunner."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from dolatex.cli import cli


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


# ---------------------------------------------------------------------------
# convert command
# ---------------------------------------------------------------------------

class TestConvertCommand:
    def test_stdin(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["convert", "--stdin"], input="# Hello\n\nWorld.\n")
        assert result.exit_code == 0
        assert r"\section{Hello}" in result.output
        assert r"\begin{document}" in result.output

    def test_stdin_body_only(self, runner: CliRunner) -> None:
        result = runner.invoke(
            cli, ["convert", "--stdin", "--no-complete"], input="Hello **world**.\n"
        )
        assert result.exit_code == 0
        assert r"\textbf{world}" in result.output
        assert r"\begin{document}" not in result.output

    def test_input_file(self, runner: CliRunner, tmp_path: pytest.TempPathFactory) -> None:
        md_file = tmp_path / "test.md"
        md_file.write_text("# Doc\n\nContent.\n", encoding="utf-8")
        result = runner.invoke(cli, ["convert", "-i", str(md_file)])
        assert result.exit_code == 0
        assert r"\section{Doc}" in result.output
        assert "Content" in result.output

    def test_output_file(self, runner: CliRunner, tmp_path: pytest.TempPathFactory) -> None:
        md_file = tmp_path / "test.md"
        md_file.write_text("# Title\n\nBody.\n", encoding="utf-8")
        tex_file = tmp_path / "out.tex"
        result = runner.invoke(cli, ["convert", "-i", str(md_file), "-o", str(tex_file)])
        assert result.exit_code == 0
        assert tex_file.exists()
        contents = tex_file.read_text(encoding="utf-8")
        assert r"\section{Title}" in contents

    def test_input_file_not_found(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["convert", "-i", "nonexistent.md"])
        assert result.exit_code != 0

    def test_no_input_and_stdin_is_terminal(self, runner: CliRunner) -> None:
        """Simulate no stdin and no -i (runner pretends stdin is a TTY)."""
        result = runner.invoke(cli, ["convert"])
        assert result.exit_code != 0
        assert "Error" in result.output

    def test_custom_title(self, runner: CliRunner) -> None:
        result = runner.invoke(
            cli, ["convert", "--stdin", "--title", "My Custom Title"],
            input="# Other\n\nBody.\n"
        )
        assert result.exit_code == 0
        # The title from --title should appear in maketitle
        assert r"\title{My Custom Title}" in result.output

    def test_custom_author(self, runner: CliRunner) -> None:
        result = runner.invoke(
            cli, ["convert", "--stdin", "--author", "Alice"],
            input="# Doc\n\nBody.\n"
        )
        assert result.exit_code == 0
        assert r"\author{Alice}" in result.output


# ---------------------------------------------------------------------------
# serve command
# ---------------------------------------------------------------------------

class TestServeCommand:
    def test_serve_help(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["serve", "--help"])
        assert result.exit_code == 0
        assert "--host" in result.output
        assert "--port" in result.output
        assert "--debug" in result.output


# ---------------------------------------------------------------------------
# Top-level help
# ---------------------------------------------------------------------------

class TestCliHelp:
    def test_help(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "convert" in result.output
        assert "serve" in result.output
