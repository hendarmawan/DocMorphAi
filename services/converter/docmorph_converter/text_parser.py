"""Plain text -> paragraphs. Short, title-like opening lines become the heading."""

from __future__ import annotations

import re

from docmorph_schema import HeadingBlock, ParagraphBlock

from docmorph_converter.builder import BlockIds, normalize_ws, text_inline
from docmorph_converter.markdown_parser import ParsedText

_SPLIT = re.compile(r"\n\s*\n")


def _looks_like_heading(chunk: str) -> bool:
    return "\n" not in chunk and len(chunk) <= 80 and not chunk.rstrip().endswith((".", ",", ";", ":"))


def parse_text(source: str, *, pdf: bool = False) -> ParsedText:
    ids = BlockIds()
    blocks: list = []
    title: str | None = None
    chunks = [c.strip() for c in _SPLIT.split(source.replace("\r\n", "\n")) if c.strip()]
    for idx, chunk in enumerate(chunks):
        if _looks_like_heading(chunk) and (idx == 0 or (len(chunk.split()) <= 8 and chunk[:1].isupper())):
            level = 1 if title is None else 2
            if title is None:
                title = chunk
            blocks.append(HeadingBlock(id=ids.next(), level=level, content=[text_inline(chunk)]))
            continue
        # In PDFs, single newlines are layout wraps; in TXT they are soft wraps too.
        text = normalize_ws(chunk.replace("-\n", "") if pdf else chunk).replace("\n", " ")
        blocks.append(ParagraphBlock(id=ids.next(), content=[text_inline(text)]))
    return ParsedText(title=title, blocks=blocks)
