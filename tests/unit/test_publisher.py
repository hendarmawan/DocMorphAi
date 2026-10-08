from __future__ import annotations

from docmorph_converter import convert
from docmorph_publisher import export_standalone_html, hash_token, new_share_token
from docmorph_renderer.templates import template_design
from fixtures.factory import make_docx


def test_export_is_self_contained():
    doc = convert(make_docx(), "Quarterly Report.docx", document_id="doc_e")
    result = export_standalone_html(doc, template_design("academic"))
    assert result.filename == "quarterly-strategy-report.html"
    assert result.size_bytes == len(result.html.encode())
    # no external fetches: every src is a data URI and nothing links out for assets
    assert 'src="http' not in result.html
    assert "<link" not in result.html
    assert "Content-Security-Policy" in result.html


def test_share_tokens_store_only_hashes():
    token = new_share_token()
    assert len(token.token) >= 32
    assert token.token_hash == hash_token(token.token)
    assert token.token not in token.token_hash
