"""Deterministic HTML rendering.

The same document version + design config always produces byte-identical
output: no timestamps, random ids or dict-order dependence. All text is escaped
at the point of emission, and URLs are restricted to safe schemes, so the
output is sanitized by construction rather than by post-filtering.
"""

from __future__ import annotations

import base64
import hashlib
import os
from dataclasses import dataclass
from html import escape
from pathlib import Path

from docmorph_schema import DesignConfig, Document, plain_text

from docmorph_renderer.css import build_css

_SAFE_URL_PREFIXES = ("http://", "https://", "mailto:", "#")
_MARK_TAGS = {
    "bold": "strong",
    "italic": "em",
    "underline": "u",
    "strike": "s",
    "code": "code",
    "superscript": "sup",
    "subscript": "sub",
}
_MARK_ORDER = ["bold", "italic", "underline", "strike", "superscript", "subscript", "code"]


@dataclass(frozen=True)
class RenderOptions:
    include_reader: bool = True
    reader_mode: str | None = None  # overrides design.reader.mode (preview toggles)
    generator: str = "DocMorph AI"


def reader_bundle() -> str | None:
    override = os.environ.get("DOCMORPH_READER_BUNDLE")
    path = (
        Path(override)
        if override
        else Path(__file__).resolve().parents[3] / "packages" / "reader" / "dist" / "reader.global.js"
    )
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def _attr(value: str) -> str:
    return escape(value, quote=True)


def _safe_url(href: str) -> str | None:
    h = href.strip()
    return h if h.lower().startswith(_SAFE_URL_PREFIXES) else None


def _inline(nodes: list) -> str:
    out: list[str] = []
    for n in nodes:
        if n.type == "break":
            out.append("<br>")
            continue
        html = escape(n.text, quote=False)
        for mark in sorted(n.marks, key=_MARK_ORDER.index, reverse=True):
            tag = _MARK_TAGS[mark]
            html = f"<{tag}>{html}</{tag}>"
        if n.type == "link":
            url = _safe_url(n.href)
            if url:
                rel = "" if url.startswith("#") else ' rel="noopener noreferrer nofollow" target="_blank"'
                html = f'<a href="{_attr(url)}"{rel}>{html}</a>'
        out.append(html)
    return "".join(out)


def _block(block, doc: Document) -> str:
    bid = _attr(block.id)
    t = block.type
    if t == "heading":
        lvl = block.level
        return f'<h{lvl} id="{bid}">{_inline(block.content)}</h{lvl}>'
    if t == "paragraph":
        return f'<p id="{bid}">{_inline(block.content)}</p>'
    if t == "quote":
        return f'<blockquote id="{bid}"><p>{_inline(block.content)}</p></blockquote>'
    if t == "list":
        tag = "ol" if block.ordered else "ul"
        items = "".join(f"<li>{_inline(item)}</li>" for item in block.items)
        return f'<{tag} id="{bid}">{items}</{tag}>'
    if t == "code":
        lang = f' data-language="{_attr(block.language)}"' if block.language else ""
        return f'<pre id="{bid}"{lang}><code>{escape(block.text, quote=False)}</code></pre>'
    if t == "divider":
        return f'<hr id="{bid}">'
    if t == "table":
        rows: list[str] = []
        for r, row in enumerate(block.rows):
            cell_tag = "th" if r < block.header_rows else "td"
            scope = ' scope="col"' if cell_tag == "th" else ""
            cells = "".join(f"<{cell_tag}{scope}>{_inline(c)}</{cell_tag}>" for c in row)
            rows.append(f"<tr>{cells}</tr>")
        head = "".join(rows[: block.header_rows])
        body = "".join(rows[block.header_rows :])
        caption = f"<caption>{escape(block.caption)}</caption>" if block.caption else ""
        thead = f"<thead>{head}</thead>" if head else ""
        return f'<div class="dm-table" id="{bid}"><table>{caption}{thead}<tbody>{body}</tbody></table></div>'
    if t == "image":
        asset = doc.assets.get(block.asset_id)
        if asset is None or not asset.data_base64:
            return ""
        # Re-encode to guarantee the payload is pure base64 (no attribute breakout).
        data = base64.b64encode(base64.b64decode(asset.data_base64, validate=True)).decode("ascii")
        caption = f"<figcaption>{escape(block.caption)}</figcaption>" if block.caption else ""
        return (
            f'<figure id="{bid}"><img src="data:{asset.mime_type};base64,{data}" '
            f'alt="{_attr(block.alt)}" loading="lazy" decoding="async">{caption}</figure>'
        )
    return ""


def _sections(blocks: list) -> list[tuple[str | None, list]]:
    """Group blocks into reader sections at the top two heading levels present."""
    levels = sorted({b.level for b in blocks if b.type == "heading"})
    split_at = levels[1] if len(levels) > 1 else (levels[0] if levels else 0)
    sections: list[tuple[str | None, list]] = []
    current: list = []
    for b in blocks:
        if b.type == "heading" and b.level <= split_at and current:
            sections.append((current[0].id, current))
            current = []
        current.append(b)
    if current:
        sections.append((current[0].id, current))
    return sections


def _toc(blocks: list) -> str:
    entries = [b for b in blocks if b.type == "heading" and b.level <= 3]
    if len(entries) < 2:
        return ""
    base = min(b.level for b in entries)
    items = "".join(
        f'<li class="dm-toc--l{b.level - base + 1}"><a href="#{_attr(b.id)}">{escape(plain_text(b.content))}</a></li>'
        for b in entries
    )
    return f'<nav class="dm-toc" aria-label="Contents"><h2>Contents</h2><ol>{items}</ol></nav>'


def render_document(doc: Document, design: DesignConfig, options: RenderOptions | None = None) -> str:
    opts = options or RenderOptions()
    mode = opts.reader_mode or design.reader.mode
    if mode not in ("scroll", "paginate", "swipe"):
        mode = "scroll"
    css = build_css(design)

    body: list[str] = []
    blocks = list(doc.blocks)
    if design.layout.cover:
        meta = [doc.metadata.get("author", ""), doc.metadata.get("subject", "")]
        sub = " · ".join(m for m in meta if m)
        if blocks and blocks[0].type == "heading" and plain_text(blocks[0].content) == doc.title:
            blocks = blocks[1:]
        body.append(
            f'<header class="dm-cover"><h1>{escape(doc.title)}</h1>'
            + (f"<p>{escape(sub)}</p>" if sub else "")
            + "</header>"
        )
    if design.layout.show_toc:
        body.append(_toc(blocks))

    for anchor, section_blocks in _sections(blocks):
        inner = "".join(_block(b, doc) for b in section_blocks)
        body.append(
            f'<section class="dm-section" data-section="{_attr(anchor or "")}">'
            f'<div class="dm-section__body">{inner}</div></section>'
        )

    script = ""
    csp_script = "'none'"
    bundle = reader_bundle() if opts.include_reader and mode != "scroll" else None
    if bundle:
        digest = base64.b64encode(hashlib.sha256(bundle.encode("utf-8")).digest()).decode()
        csp_script = f"'sha256-{digest}'"
        script = f"<script>{bundle}</script>"

    csp = (
        "default-src 'none'; img-src data:; style-src 'unsafe-inline'; "
        f"script-src {csp_script}; base-uri 'none'; form-action 'none'"
    )
    lang = _attr(doc.language or "en")
    return (
        "<!doctype html>"
        f'<html lang="{lang}"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f'<meta http-equiv="Content-Security-Policy" content="{_attr(csp)}">'
        f'<meta name="generator" content="{_attr(opts.generator)}">'
        f'<meta name="docmorph:template" content="{_attr(design.template_id)}">'
        f"<title>{escape(doc.title)}</title><style>{css}</style></head>"
        f'<body><main class="dm-doc" data-docmorph-root data-reader-mode="{mode}">'
        + "".join(body)
        + f"</main>{script}</body></html>"
    )
