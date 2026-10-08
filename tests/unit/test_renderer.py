from __future__ import annotations

import re

from docmorph_converter import convert
from docmorph_renderer import RenderOptions, render_document
from docmorph_renderer.templates import template_design
from fixtures.factory import SAMPLE_MARKDOWN, make_docx


def _doc():
    return convert(make_docx(), "report.docx", document_id="doc_r")


def test_rendering_is_deterministic():
    doc, design = _doc(), template_design("academic")
    assert render_document(doc, design) == render_document(doc, design)


def test_semantic_html_output():
    html = render_document(_doc(), template_design("corporate"))
    assert html.startswith("<!doctype html>")
    assert '<html lang="en">' in html
    assert "<h2" in html or "<h1" in html
    assert "<strong>18%</strong>" in html
    assert "<table>" in html and '<th scope="col">' in html
    assert "<ul" in html and "<ol" in html
    assert "data:image/png;base64," in html
    assert 'rel="noopener noreferrer nofollow"' in html
    assert 'class="dm-cover"' in html  # corporate template has a cover
    assert 'class="dm-toc"' in html


def test_each_template_changes_presentation_not_content():
    doc = _doc()
    outputs = {
        t: render_document(doc, template_design(t), RenderOptions(include_reader=False))
        for t in ("academic", "corporate", "bilingual", "presentation")
    }
    assert len(set(outputs.values())) == 4

    def text_of(html: str) -> str:
        body = html.split("<main", 1)[1]
        body = re.sub(r'<(header|nav) class="dm-(cover|toc)".*?</\1>', "", body, flags=re.S)
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body)).strip()

    texts = {t: text_of(h) for t, h in outputs.items()}
    assert "Revenue grew" in texts["academic"]
    assert "Revenue grew" in texts["presentation"]


def test_sections_and_reader_mode():
    doc = convert(SAMPLE_MARKDOWN.encode(), "n.md", document_id="doc_s")
    html = render_document(doc, template_design("presentation"), RenderOptions(include_reader=False))
    assert 'data-reader-mode="swipe"' in html
    assert html.count('class="dm-section"') >= 2  # Abstract, Results (title moves to the cover)
    override = render_document(
        doc, template_design("presentation"), RenderOptions(reader_mode="paginate", include_reader=False)
    )
    assert 'data-reader-mode="paginate"' in override


def test_two_column_template_emits_column_css():
    html = render_document(_doc(), template_design("bilingual"))
    assert "column-count:2" in html
