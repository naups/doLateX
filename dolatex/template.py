"""Jinja2-based LaTeX template renderer.

Loads ``.tpl`` files from the package's ``templates/latex/`` directory and
renders them with template variables from ``DocumentFormat``.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from jinja2 import BaseLoader, Environment, FileSystemLoader, TemplateNotFound

logger = logging.getLogger(__name__)

# Path to the templates/latex directory within the package.
_HERE = Path(__file__).resolve().parent
_TEMPLATE_DIR = _HERE / "templates" / "latex"


class TemplateEngine:
    """Renders LaTeX preamble templates with format metadata.

    Parameters
    ----------
    template_dir:
        Override the default template directory (useful for testing).
    """

    def __init__(self, template_dir: Optional[Path] = None) -> None:
        self._template_dir = template_dir or _TEMPLATE_DIR
        self._env = Environment(
            loader=FileSystemLoader(str(self._template_dir)),
            autoescape=False,
        )

    def render(self, template_name: str, variables: dict[str, str]) -> str:
        """Render *template_name* with *variables* and return the LaTeX preamble.

        Parameters
        ----------
        template_name:
            Template file name without extension (e.g. ``"base"``, ``"skripsi-filkom"``).
        variables:
            Flat dict of template variables from ``DocumentFormat.to_template_vars()``.

        Returns
        -------
        str
            The rendered LaTeX preamble (may be empty on fallback).
        """
        try:
            template = self._env.get_template(f"{template_name}.tpl")
            return template.render(**variables)
        except TemplateNotFound:
            logger.warning("Template '%s' not found, falling back to 'base'", template_name)
            try:
                template = self._env.get_template("base.tpl")
                return template.render(**variables)
            except TemplateNotFound:
                logger.error("Base template 'base.tpl' also not found — returning empty preamble")
                return ""
