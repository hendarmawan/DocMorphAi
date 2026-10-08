"""Markdown -> canonical blocks. Raw HTML is disabled so markup cannot smuggle scripts."""

from __future__ import annotations

from dataclasses import dataclass, field

from docmorph_schema import (
    BreakInline,
    CodeBlock,
    DividerBlock,
    HeadingBlock,
    ListBlock,
    ParagraphBlock,
    TableBlock,
    plain_text,
)
from markdown_it import MarkdownIt
from markdown_it.token import Token

from docmorph_converter.builder import BlockIds, link_inline, merge_inlines, text_inline

_md = MarkdownIt("commonmark", {"html": False, "linkify": False}).enable(["table", "strikethrough"])


@dataclass
class ParsedText:
    title: str | None
    blocks: list
    warnings: list[str] = field(default_factory=list)


def parse_markdown(source: str) -> ParsedText:
    tokens = _md.parse(source)
    ids = BlockIds()
    blocks: list = []
    warnings: list[str] = []
    title: str | None = None

    list_stack: list[ListBlock] = []
    quote_depth = 0
    table: TableBlock | None = None
    row: list | None = None
    in_thead = False

    i = 0
    while i < len(tokens):
        tok = tokens[i]
        t = tok.type
        if t == "heading_open":
            inl = _inlines(tokens[i + 1], warnings)
            if inl:
                level = int(tok.tag[1])
                if title is None and level == 1:
                    title = plain_text(inl)
                blocks.append(HeadingBlock(id=ids.next(), level=level, content=inl))
            i += 3
            continue
        if t in ("bullet_list_open", "ordered_list_open"):
            if not list_stack:
                lst = ListBlock(id=ids.next(), ordered=t == "ordered_list_open", items=[])
                blocks.append(lst)
                list_stack.append(lst)
            else:  # nested lists are flattened into the outer list
                list_stack.append(list_stack[-1])
        elif t in ("bullet_list_close", "ordered_list_close"):
            list_stack.pop()
        elif t == "blockquote_open":
            quote_depth += 1
        elif t == "blockquote_close":
            quote_depth -= 1
        elif t == "inline" and table is not None and row is not None:
            row.append(_inlines(tok, warnings))
        elif t == "inline":
            inl = _inlines(tok, warnings)
            if inl:
                if list_stack:
                    list_stack[-1].items.append(inl)
                elif quote_depth:
                    blocks.append(ParagraphBlock(id=ids.next(), type="quote", content=inl))
                else:
                    blocks.append(ParagraphBlock(id=ids.next(), content=inl))
        elif t in ("fence", "code_block"):
            lang = (tok.info or "").strip().split(" ")[0] or None
            blocks.append(CodeBlock(id=ids.next(), text=tok.content.rstrip("\n"), language=lang))
        elif t == "hr":
            blocks.append(DividerBlock(id=ids.next()))
        elif t == "table_open":
            table = TableBlock(id=ids.next(), rows=[], header_rows=0)
        elif t == "thead_open":
            in_thead = True
        elif t == "thead_close":
            in_thead = False
        elif t == "tr_open":
            row = []
        elif t == "tr_close" and table is not None and row is not None:
            table.rows.append(row)
            if in_thead:
                table.header_rows += 1
            row = None
        elif t == "table_close" and table is not None:
            blocks.append(table)
            table = None
        i += 1

    return ParsedText(title=title, blocks=blocks, warnings=warnings)


def _inlines(tok: Token, warnings: list[str]) -> list:
    out: list = []
    marks: list[str] = []
    link: str | None = None
    link_text: list[str] = []
    for child in tok.children or []:
        ct = child.type
        if ct == "text":
            if link is not None:
                link_text.append(child.content)
            else:
                out.append(text_inline(child.content, marks))
        elif ct == "softbreak":
            out.append(text_inline(" ", marks))
        elif ct == "hardbreak":
            out.append(BreakInline())
        elif ct == "code_inline":
            out.append(text_inline(child.content, [*marks, "code"]))
        elif ct in ("strong_open", "em_open", "s_open"):
            marks.append({"strong_open": "bold", "em_open": "italic", "s_open": "strike"}[ct])
        elif ct in ("strong_close", "em_close", "s_close"):
            if marks:
                marks.pop()
        elif ct == "link_open":
            link = str(child.attrs.get("href", ""))
            link_text = []
        elif ct == "link_close":
            out.append(link_inline("".join(link_text), link or "", marks))
            link = None
        elif ct == "image":
            alt = child.content or "image"
            warnings.append("External image references are not imported; kept alt text")
            out.append(text_inline(f"[{alt}]", [*marks, "italic"]))
    return merge_inlines(out)
