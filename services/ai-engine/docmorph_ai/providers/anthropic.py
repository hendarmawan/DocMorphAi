"""Hosted-model provider using Claude via the official Anthropic SDK.

The model only ever proposes a design patch against a fixed set of paths; the
engine validates and applies it, so the model cannot touch document content.
"""

from __future__ import annotations

import json
import os

from docmorph_schema import DesignConfig, DesignPatch, Document, plain_text

from docmorph_ai.analysis import analyze_document
from docmorph_ai.providers.base import ContentEditRefused, NoDesignChange
from docmorph_ai.types import DocumentAnalysis

DEFAULT_MODEL = "claude-opus-5-5"

_PATHS = [
    "/template_id",
    "/typography/body_font",
    "/typography/heading_font",
    "/typography/base_size_px",
    "/typography/line_height",
    "/typography/scale",
    "/typography/heading_weight",
    "/colors/background",
    "/colors/text",
    "/colors/accent",
    "/colors/muted",
    "/colors/surface",
    "/layout/max_width_px",
    "/layout/columns",
    "/layout/spacing",
    "/layout/align",
    "/layout/show_toc",
    "/layout/cover",
    "/reader/mode",
]

_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["ok", "content_edit", "no_change"]},
        "summary": {"type": "string"},
        "ops": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "enum": _PATHS},
                    "value_json": {"type": "string"},
                },
                "required": ["path", "value_json"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["status", "summary", "ops"],
    "additionalProperties": False,
}

_SYSTEM = """You are the design assistant inside DocMorph AI, which turns documents into web pages.
You change presentation only. You never change the document's words.

Given the current design configuration and a user's request, return the smallest set of replace
operations that achieves the request. Each op has a path from the allowed list and value_json, the
new value encoded as JSON (a JSON string for text, a number, or a boolean).

Constraints: fonts are one of serif, sans, mono, humanist, slab. Colors are #rrggbb. base_size_px
12-28, line_height 1.1-2.2, scale 1.05-1.6, heading_weight 300-900, max_width_px 480-1600,
columns 1-2, spacing compact|normal|relaxed, align left|justify|center, reader mode
scroll|paginate|swipe, template_id academic|corporate|bilingual|presentation. Keep text and
background colors readable (WCAG AA contrast).

If the request asks to rewrite, translate, summarize, add or delete content, return status
"content_edit" with no ops. If it is not a design request at all, return status "no_change".
Otherwise return status "ok" and write summary as one short sentence describing the change."""


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, model: str | None = None, api_key: str | None = None):
        try:
            import anthropic
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("Install docmorph-ai-engine[anthropic] to use the Anthropic provider") from exc
        self._anthropic = anthropic
        self._client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
        self.model = model or os.environ.get("DOCMORPH_AI_MODEL", DEFAULT_MODEL)

    def analyze(self, doc: Document) -> DocumentAnalysis:
        # Structure analysis stays deterministic in Release 1; the hosted model is used for
        # reprompting, where language understanding matters most.
        return analyze_document(doc, provider="heuristic")

    def design_patch(self, prompt: str, design: DesignConfig, doc: Document) -> DesignPatch:
        outline = [plain_text(b.content) for b in doc.blocks if b.type == "heading"][:20]
        user = (
            f"<document_title>{doc.title}</document_title>\n"
            f"<outline>{json.dumps(outline, ensure_ascii=False)}</outline>\n"
            f"<current_design>{design.model_dump_json()}</current_design>\n"
            f"<request>{prompt}</request>"
        )
        response = self._client.beta.messages.create(
            model=self.model,
            max_tokens=4000,
            system=_SYSTEM,
            messages=[{"role": "user", "content": user}],
            output_config={"effort": "low", "format": {"type": "json_schema", "schema": _OUTPUT_SCHEMA}},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
        if response.stop_reason == "refusal":
            raise NoDesignChange("The AI provider declined this request.")
        text = next((b.text for b in response.content if b.type == "text"), "")
        data = json.loads(text)
        if data["status"] == "content_edit":
            raise ContentEditRefused("Design prompts change presentation only; content edits are not applied.")
        if data["status"] != "ok" or not data["ops"]:
            raise NoDesignChange("The request did not translate into a design change.")
        ops = [{"op": "replace", "path": o["path"], "value": json.loads(o["value_json"])} for o in data["ops"]]
        return DesignPatch.model_validate({"summary": data["summary"], "ops": ops})
