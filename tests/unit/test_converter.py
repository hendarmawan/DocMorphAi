from __future__ import annotations

from docmorph_converter import convert
from docmorph_schema import plain_text
from fixtures.factory import SAMPLE_MARKDOWN, make_docx, make_pdf


def _types(doc):
    return [b.type for b in doc.blocks]


def test_docx_preserves_structure():
    doc = convert(make_docx(), "report.docx", document_id="d1")
    assert doc.title == "Quarterly Strategy Report"
    assert doc.source.format == "docx" and doc.source.fidelity == "full"
    headings = [(b.level, plain_text(b.content)) for b in doc.blocks if b.type == "heading"]
    assert (1, "Executive summary") in headings
    assert (2, "Priorities") in headings

    para = next(b for b in doc.blocks if b.type == "paragraph")
    marks = {n.text: n.marks for n in para.content if n.type == "text"}
    assert marks["18%"] == ["bold"] and marks["enterprise"] == ["italic"]
    link = next(n for n in para.content if n.type == "link")
    assert link.href == "https://example.com/report"

    lists = [b for b in doc.blocks if b.type == "list"]
    assert [lst.ordered for lst in lists] == [False, True]
    assert len(lists[0].items) == 2

    table = next(b for b in doc.blocks if b.type == "table")
    assert table.header_rows == 1
    assert plain_text(table.rows[1][1]) == "$12,000"

    assert "quote" in _types(doc)
    image = next(b for b in doc.blocks if b.type == "image")
    assert image.asset_id in doc.assets
    assert doc.assets[image.asset_id].mime_type == "image/png"
    assert doc.metadata["author"] == "DocMorph QA"


def test_docx_conversion_is_deterministic():
    data = make_docx()
    a = convert(data, "r.docx", document_id="same").to_json_dict()
    b = convert(data, "r.docx", document_id="same").to_json_dict()
    assert a == b


def test_markdown_blocks():
    doc = convert(SAMPLE_MARKDOWN.encode(), "notes.md", document_id="d2")
    assert doc.title == "Research Notes"
    assert set(_types(doc)) >= {"heading", "paragraph", "list", "table", "quote", "code", "divider"}
    table = next(b for b in doc.blocks if b.type == "table")
    assert table.header_rows == 1 and len(table.rows) == 2
    code = next(b for b in doc.blocks if b.type == "code")
    assert code.language == "python"


def test_plain_text():
    doc = convert(b"My Notes\n\nFirst paragraph\nwraps here.\n\nSecond paragraph.", "n.txt", document_id="d3")
    assert doc.title == "My Notes"
    assert _types(doc) == ["heading", "paragraph", "paragraph"]
    assert plain_text(doc.blocks[1].content) == "First paragraph wraps here."


def test_pdf_text_layer_is_partial_fidelity():
    doc = convert(make_pdf(["Annual Overview", "Revenue increased across all regions."]), "a.pdf", document_id="d4")
    assert doc.source.fidelity == "partial"
    assert doc.source.warnings
    text = " ".join(plain_text(b.content) for b in doc.blocks if hasattr(b, "content"))
    assert "Revenue increased" in text
