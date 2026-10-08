"""Canonical DocMorph document model.

The JSON Schemas in ``packages/document-schema/schema`` are the contract; these
pydantic models mirror them for the Python services, and the TypeScript types in
``src/`` mirror them for the web app. Contract tests keep all three in sync.
"""

from docmorph_schema.design import (
    Colors,
    DesignConfig,
    Layout,
    ReaderSettings,
    Typography,
)
from docmorph_schema.document import (
    SCHEMA_VERSION,
    Asset,
    Block,
    BreakInline,
    CodeBlock,
    DividerBlock,
    Document,
    HeadingBlock,
    ImageBlock,
    Inline,
    LinkInline,
    ListBlock,
    ParagraphBlock,
    Source,
    TableBlock,
    TextInline,
    content_fingerprint,
    plain_text,
)
from docmorph_schema.patch import DesignPatch, PatchError, PatchOp, apply_design_patch

__all__ = [
    "SCHEMA_VERSION",
    "Asset",
    "Block",
    "BreakInline",
    "CodeBlock",
    "Colors",
    "DesignConfig",
    "DesignPatch",
    "DividerBlock",
    "Document",
    "HeadingBlock",
    "ImageBlock",
    "Inline",
    "Layout",
    "LinkInline",
    "ListBlock",
    "ParagraphBlock",
    "PatchError",
    "PatchOp",
    "ReaderSettings",
    "Source",
    "TableBlock",
    "TextInline",
    "Typography",
    "apply_design_patch",
    "content_fingerprint",
    "plain_text",
]


def json_schema_dir():
    """Directory holding the JSON Schema contract files."""
    from pathlib import Path

    here = Path(__file__).resolve().parent
    for candidate in (here / "json", here.parents[1] / "schema"):
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("document-schema JSON files not found")
