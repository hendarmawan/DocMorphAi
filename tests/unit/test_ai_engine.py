from __future__ import annotations

import pytest
from docmorph_ai import ContentEditRefused, NoDesignChange, get_provider, propose_design_change
from docmorph_converter import convert
from docmorph_renderer.templates import template_design
from docmorph_schema import content_fingerprint
from fixtures.factory import SAMPLE_MARKDOWN, make_docx


@pytest.fixture
def provider():
    return get_provider("heuristic")


@pytest.fixture
def doc():
    return convert(make_docx(), "report.docx", document_id="doc_ai")


def test_analysis_identifies_topic_and_template(provider, doc):
    analysis = provider.analyze(doc)
    assert analysis.topic == "Quarterly Strategy Report"
    assert analysis.document_type == "business document"
    assert analysis.suggested_template == "corporate"
    assert analysis.keywords


def test_research_document_suggests_academic(provider):
    research = convert(SAMPLE_MARKDOWN.encode(), "r.md", document_id="doc_r")
    assert provider.analyze(research).suggested_template == "academic"


@pytest.mark.parametrize(
    "prompt,check",
    [
        ("make the text bigger", lambda d: d.typography.base_size_px == 18),
        ("use a dark mode", lambda d: d.colors.background == "#0f172a"),
        ("switch to serif fonts", lambda d: d.typography.body_font == "serif"),
        ("blue accent please", lambda d: d.colors.accent == "#1d4ed8"),
        ("two columns", lambda d: d.layout.columns == 2),
        ("swipe through it like slides", lambda d: d.reader.mode == "swipe"),
        ("more space and justified text", lambda d: d.layout.spacing == "relaxed" and d.layout.align == "justify"),
    ],
)
def test_prompts_map_to_design_patches(provider, doc, prompt, check):
    change = propose_design_change(provider, prompt, template_design("corporate"), doc)
    assert check(change.design), change.patch
    assert change.content_unchanged


def test_template_switch_then_overrides(provider, doc):
    change = propose_design_change(
        provider, "use the academic template in dark mode", template_design("corporate"), doc
    )
    assert change.design.template_id == "academic"
    assert change.design.colors.background == "#0f172a"


def test_content_edits_are_refused(provider, doc):
    before = content_fingerprint(doc)
    with pytest.raises(ContentEditRefused):
        propose_design_change(
            provider, "rewrite the executive summary to be shorter", template_design("corporate"), doc
        )
    assert content_fingerprint(doc) == before


def test_unrecognised_prompt(provider, doc):
    with pytest.raises(NoDesignChange):
        propose_design_change(provider, "hmm", template_design("corporate"), doc)
