"""Canonical document + design config -> standalone, sanitized HTML."""

from docmorph_renderer.render import RenderOptions, render_document
from docmorph_renderer.templates import TemplateNotFound, get_template, list_templates

__all__ = ["RenderOptions", "TemplateNotFound", "get_template", "list_templates", "render_document"]
