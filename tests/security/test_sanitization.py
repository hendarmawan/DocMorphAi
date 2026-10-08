"""Content from uploads must never become executable markup in rendered output."""

from __future__ import annotations

import re
from html import unescape

from docmorph_converter import convert
from docmorph_renderer import RenderOptions, render_document
from docmorph_renderer.templates import template_design
from fixtures.factory import make_docx

HOSTILE_MD = b"""# <img src=x onerror=alert(1)>

<script>alert('xss')</script>

[click me](javascript:alert(1)) and [data](data:text/html;base64,PHNjcmlwdD4=)

Text with "quotes" & <b>tags</b>.

<iframe src="https://evil.example"></iframe>
"""


def _render(doc, **kw):
    return render_document(doc, template_design("academic"), RenderOptions(include_reader=False, **kw))


def test_markdown_html_and_scripts_are_escaped():
    html = _render(convert(HOSTILE_MD, "x.md", document_id="doc_x"))
    body = html.split("<body>", 1)[1]
    assert "<script" not in body
    assert "<iframe" not in body
    assert "<img src=x" not in body
    assert not re.search(r"\son\w+=", body.replace("&lt;img src=x onerror=alert(1)&gt;", ""))
    assert "&lt;script&gt;" in body


def test_dangerous_link_schemes_are_dropped():
    html = _render(convert(HOSTILE_MD, "x.md", document_id="doc_x"))
    # markdown-it refuses these links, so they survive only as escaped literal text
    assert not re.search(r'href="(javascript|data):', html, re.I)


def test_docx_javascript_hyperlink_is_neutralised():
    doc = convert(make_docx(link_url="javascript:alert(document.cookie)"), "r.docx", document_id="doc_j")
    assert all(n.type != "link" for b in doc.blocks if b.type == "paragraph" for n in b.content)
    assert "javascript:" not in _render(doc)


def test_title_and_attributes_are_escaped():
    doc = convert(b'Title "><script>alert(1)</script>\n\nBody.', "t.txt", document_id="doc_t")
    html = _render(doc)
    assert "<title>Title &quot;&gt;&lt;script&gt;" in html


def test_csp_blocks_scripts_when_reader_is_not_embedded():
    html = unescape(_render(convert(b"# A\n\ntext", "a.md", document_id="doc_c")))
    assert "script-src 'none'" in html
    assert "default-src 'none'" in html


def test_render_endpoint_is_sandboxed(client):
    res = client.post("/v1/documents", files={"file": ("x.md", HOSTILE_MD, "text/markdown")})
    doc_id = res.json()["document"]["id"]
    render = client.get(f"/v1/documents/{doc_id}/render")
    assert render.headers["content-security-policy"].startswith("sandbox")
    assert render.headers["x-content-type-options"] == "nosniff"
