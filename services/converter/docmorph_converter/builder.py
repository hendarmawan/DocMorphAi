from __future__ import annotations

import re

from docmorph_schema import (
    BreakInline,
    LinkInline,
    TextInline,
)

_SAFE_SCHEMES = ("http://", "https://", "mailto:", "#")


class BlockIds:
    """Deterministic block ids: the same input always yields the same ids."""

    def __init__(self) -> None:
        self._n = 0

    def next(self) -> str:
        self._n += 1
        return f"b{self._n}"


def safe_href(href: str | None) -> str | None:
    if not href:
        return None
    href = href.strip()
    if href.lower().startswith(_SAFE_SCHEMES):
        return href
    return None


def text_inline(text: str, marks: list[str] | None = None) -> TextInline:
    return TextInline(text=text, marks=sorted(set(marks or [])))  # type: ignore[arg-type]


def link_inline(text: str, href: str, marks: list[str] | None = None) -> LinkInline | TextInline:
    safe = safe_href(href)
    if safe is None:
        return text_inline(text, marks)
    return LinkInline(text=text, href=safe, marks=sorted(set(marks or [])))  # type: ignore[arg-type]


def merge_inlines(inlines: list) -> list:
    """Merge adjacent text runs with identical marks (Word splits runs a lot)."""
    merged: list = []
    for node in inlines:
        if isinstance(node, TextInline) and not node.text:
            continue
        prev = merged[-1] if merged else None
        if isinstance(node, TextInline) and isinstance(prev, TextInline) and prev.marks == node.marks:
            merged[-1] = TextInline(text=prev.text + node.text, marks=prev.marks)
        else:
            merged.append(node)
    # trim surrounding whitespace / breaks
    while merged and isinstance(merged[-1], BreakInline):
        merged.pop()
    if merged and isinstance(merged[0], TextInline):
        merged[0] = TextInline(text=merged[0].text.lstrip(), marks=merged[0].marks)
    if merged and isinstance(merged[-1], TextInline):
        merged[-1] = TextInline(text=merged[-1].text.rstrip(), marks=merged[-1].marks)
    return [n for n in merged if not (isinstance(n, TextInline) and not n.text)]


_WS = re.compile(r"[ \t\r\f\v]+")


def normalize_ws(text: str) -> str:
    return _WS.sub(" ", text)
