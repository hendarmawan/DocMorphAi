from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from docmorph_renderer import RenderOptions, render_document
from docmorph_schema import DesignConfig, Document


@dataclass(frozen=True)
class ExportResult:
    filename: str
    html: str
    sha256: str
    size_bytes: int


def _slug(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug[:80] or "document"


def export_standalone_html(doc: Document, design: DesignConfig) -> ExportResult:
    """A single self-contained .html file: inline CSS, images as data URIs and
    the reader script, with a strict CSP. It opens offline with no server."""
    html = render_document(doc, design, RenderOptions(include_reader=True))
    data = html.encode("utf-8")
    return ExportResult(
        filename=f"{_slug(doc.title)}.html",
        html=html,
        sha256=hashlib.sha256(data).hexdigest(),
        size_bytes=len(data),
    )
