from __future__ import annotations

import hashlib
import json
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION = "1.0"

Mark = Literal["bold", "italic", "underline", "strike", "code", "superscript", "subscript"]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=False)


class TextInline(_Strict):
    type: Literal["text"] = "text"
    text: str
    marks: list[Mark] = Field(default_factory=list)


class LinkInline(_Strict):
    type: Literal["link"] = "link"
    text: str
    href: str
    marks: list[Mark] = Field(default_factory=list)


class BreakInline(_Strict):
    type: Literal["break"] = "break"


Inline = Annotated[TextInline | LinkInline | BreakInline, Field(discriminator="type")]


class HeadingBlock(_Strict):
    type: Literal["heading"] = "heading"
    id: str
    level: int = Field(ge=1, le=6)
    content: list[Inline]


class ParagraphBlock(_Strict):
    type: Literal["paragraph", "quote"] = "paragraph"
    id: str
    content: list[Inline]


class ListBlock(_Strict):
    type: Literal["list"] = "list"
    id: str
    ordered: bool = False
    items: list[list[Inline]]


class TableBlock(_Strict):
    type: Literal["table"] = "table"
    id: str
    header_rows: int = Field(default=0, ge=0)
    caption: str | None = None
    rows: list[list[list[Inline]]]


class ImageBlock(_Strict):
    type: Literal["image"] = "image"
    id: str
    asset_id: str
    alt: str = ""
    caption: str | None = None


class CodeBlock(_Strict):
    type: Literal["code"] = "code"
    id: str
    text: str
    language: str | None = None


class DividerBlock(_Strict):
    type: Literal["divider"] = "divider"
    id: str


Block = Annotated[
    HeadingBlock | ParagraphBlock | ListBlock | TableBlock | ImageBlock | CodeBlock | DividerBlock,
    Field(discriminator="type"),
]


class Source(_Strict):
    format: Literal["docx", "pdf", "markdown", "txt"]
    filename: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    fidelity: Literal["full", "partial"] = "full"
    warnings: list[str] = Field(default_factory=list)


class Asset(_Strict):
    id: str
    mime_type: Literal["image/png", "image/jpeg", "image/gif", "image/webp"]
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size: int = Field(ge=0)
    filename: str | None = None
    storage_key: str | None = None
    data_base64: str | None = None


class Document(_Strict):
    schema_version: Literal["1.0"] = SCHEMA_VERSION
    id: str
    title: str
    language: str = "en"
    source: Source
    metadata: dict[str, str] = Field(default_factory=dict)
    blocks: list[Block]
    assets: dict[str, Asset] = Field(default_factory=dict)

    def to_json_dict(self) -> dict:
        """Serialize to the JSON-Schema shape (drops ``None`` optionals)."""
        return self.model_dump(mode="json", exclude_none=True)


def plain_text(inlines: list) -> str:
    out: list[str] = []
    for node in inlines:
        if node.type == "break":
            out.append("\n")
        else:
            out.append(node.text)
    return "".join(out)


def content_fingerprint(doc: Document) -> str:
    """Stable hash of everything that counts as *content*.

    Design changes must never alter this value; it is how the API proves an AI
    edit did not silently rewrite the source document.
    """
    payload = json.dumps(
        {"title": doc.title, "blocks": [b.model_dump(mode="json") for b in doc.blocks]},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
