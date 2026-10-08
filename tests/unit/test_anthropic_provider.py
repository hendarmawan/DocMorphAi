"""The Claude adapter, exercised with a stub client (no network)."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

pytest.importorskip("anthropic")

from docmorph_ai import ContentEditRefused, propose_design_change  # noqa: E402
from docmorph_ai.providers.anthropic import AnthropicProvider  # noqa: E402
from docmorph_converter import convert  # noqa: E402
from docmorph_renderer.templates import template_design  # noqa: E402
from fixtures.factory import make_docx  # noqa: E402


class _StubMessages:
    def __init__(self, payload: dict, stop_reason: str = "end_turn"):
        self.payload = payload
        self.stop_reason = stop_reason
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            stop_reason=self.stop_reason,
            content=[SimpleNamespace(type="text", text=json.dumps(self.payload))],
        )


def _provider(payload: dict, **kw) -> tuple[AnthropicProvider, _StubMessages]:
    provider = AnthropicProvider(api_key="test-key")
    messages = _StubMessages(payload, **kw)
    provider._client = SimpleNamespace(beta=SimpleNamespace(messages=messages))
    return provider, messages


def test_structured_patch_is_validated_and_applied():
    provider, messages = _provider(
        {
            "status": "ok",
            "summary": "Warm magazine look.",
            "ops": [
                {"path": "/colors/accent", "value_json": '"#c2410c"'},
                {"path": "/typography/base_size_px", "value_json": "19"},
                {"path": "/layout/show_toc", "value_json": "false"},
            ],
        }
    )
    doc = convert(make_docx(), "r.docx", document_id="doc_a")
    change = propose_design_change(provider, "warm magazine look", template_design("corporate"), doc)
    assert change.design.colors.accent == "#c2410c"
    assert change.design.typography.base_size_px == 19
    assert change.design.layout.show_toc is False
    call = messages.calls[0]
    assert call["model"] == "claude-opus-5-5"
    assert call["output_config"]["format"]["type"] == "json_schema"
    assert "Revenue grew" not in call["messages"][0]["content"]  # body text is never sent


def test_model_flagged_content_edit_is_refused():
    provider, _ = _provider({"status": "content_edit", "summary": "", "ops": []})
    doc = convert(make_docx(), "r.docx", document_id="doc_b")
    with pytest.raises(ContentEditRefused):
        propose_design_change(provider, "shorten the summary", template_design("corporate"), doc)


def test_out_of_range_values_are_rejected():
    from docmorph_schema import PatchError

    provider, _ = _provider(
        {"status": "ok", "summary": "x", "ops": [{"path": "/typography/base_size_px", "value_json": "72"}]}
    )
    doc = convert(make_docx(), "r.docx", document_id="doc_c")
    with pytest.raises(PatchError):
        propose_design_change(provider, "huge text", template_design("corporate"), doc)
