"""DOCX -> canonical blocks, preserving heading hierarchy, lists, tables and images."""

from __future__ import annotations

import base64
import hashlib
import io
import re
from dataclasses import dataclass, field

from docmorph_schema import (
    Asset,
    BreakInline,
    CodeBlock,
    HeadingBlock,
    ImageBlock,
    ListBlock,
    ParagraphBlock,
    TableBlock,
    plain_text,
)
from docx import Document as load_docx
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.hyperlink import Hyperlink
from docx.text.paragraph import Paragraph
from docx.text.run import Run

from docmorph_converter.builder import BlockIds, link_inline, merge_inlines, text_inline

MAX_IMAGE_BYTES = 10 * 1024 * 1024
_IMAGE_TYPES = {"image/png", "image/jpeg", "image/gif", "image/webp"}
_HEADING_STYLE = re.compile(r"^heading\s*([1-6])$", re.IGNORECASE)


@dataclass
class ParsedDocx:
    title: str | None
    blocks: list
    assets: dict[str, Asset]
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)


def parse_docx(data: bytes) -> ParsedDocx:
    doc = load_docx(io.BytesIO(data))
    ids = BlockIds()
    state = _State(doc=doc, ids=ids)

    for item in doc.iter_inner_content():
        if isinstance(item, Paragraph):
            state.paragraph(item)
        elif isinstance(item, Table):
            state.flush_list()
            state.table(item)
    state.flush_list()

    props = doc.core_properties
    metadata = {
        k: v
        for k, v in {
            "author": props.author or "",
            "subject": props.subject or "",
            "keywords": props.keywords or "",
        }.items()
        if v
    }
    title = (props.title or "").strip() or state.first_title
    return ParsedDocx(title=title, blocks=state.blocks, assets=state.assets, warnings=state.warnings, metadata=metadata)


@dataclass
class _State:
    doc: object
    ids: BlockIds
    blocks: list = field(default_factory=list)
    assets: dict[str, Asset] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    first_title: str | None = None
    _list: ListBlock | None = None

    # ---------------- paragraphs ----------------
    def paragraph(self, p: Paragraph) -> None:
        style = (p.style.name if p.style is not None else "") or ""
        inlines, images = self._inlines(p)
        list_kind = self._list_kind(p, style)

        if list_kind is not None:
            ordered = list_kind == "ordered"
            if self._list is None or self._list.ordered != ordered:
                self.flush_list()
                self._list = ListBlock(id=self.ids.next(), ordered=ordered, items=[])
            if inlines:
                self._list.items.append(inlines)
            self._emit_images(images)
            return

        self.flush_list()
        level = self._heading_level(p, style)
        if level is not None and inlines:
            text = plain_text(inlines)
            if self.first_title is None and (style.lower() == "title" or level == 1):
                self.first_title = text
            self.blocks.append(HeadingBlock(id=self.ids.next(), level=level, content=inlines))
        elif inlines:
            lowered = style.lower()
            if "quote" in lowered:
                self.blocks.append(ParagraphBlock(id=self.ids.next(), type="quote", content=inlines))
            elif "code" in lowered or "preformatted" in lowered:
                self.blocks.append(CodeBlock(id=self.ids.next(), text=plain_text(inlines)))
            else:
                self.blocks.append(ParagraphBlock(id=self.ids.next(), content=inlines))
        self._emit_images(images)

    def flush_list(self) -> None:
        if self._list is not None and self._list.items:
            self.blocks.append(self._list)
        self._list = None

    @staticmethod
    def _heading_level(p: Paragraph, style: str) -> int | None:
        if style.lower() == "title":
            return 1
        m = _HEADING_STYLE.match(style.strip())
        if m:
            return int(m.group(1))
        ppr = p._p.pPr
        if ppr is not None:
            lvl = ppr.find(qn("w:outlineLvl"))
            if lvl is not None:
                val = int(lvl.get(qn("w:val"), "9"))
                if 0 <= val <= 5:
                    return val + 1
        return None

    def _list_kind(self, p: Paragraph, style: str) -> str | None:
        lowered = style.lower()
        ppr = p._p.pPr
        num_pr = ppr.numPr if ppr is not None else None
        if num_pr is None and not lowered.startswith("list"):
            return None
        if "number" in lowered:
            return "ordered"
        if "bullet" in lowered:
            return "unordered"
        if num_pr is not None:
            return self._numbering_kind(num_pr)
        return "unordered"

    def _numbering_kind(self, num_pr) -> str:
        try:
            num_id = num_pr.numId.val
            ilvl = num_pr.ilvl.val if num_pr.ilvl is not None else 0
            numbering = self.doc.part.numbering_part.element  # type: ignore[attr-defined]
            num = numbering.num_having_numId(num_id)
            abstract_id = num.abstractNumId.val
            for abstract in numbering.findall(qn("w:abstractNum")):
                if abstract.get(qn("w:abstractNumId")) != str(abstract_id):
                    continue
                for lvl in abstract.findall(qn("w:lvl")):
                    if lvl.get(qn("w:ilvl")) == str(ilvl):
                        fmt = lvl.find(qn("w:numFmt"))
                        if fmt is not None and fmt.get(qn("w:val")) == "bullet":
                            return "unordered"
                        return "ordered"
        except (KeyError, AttributeError, NotImplementedError, ValueError):
            pass
        return "unordered"

    # ---------------- inline content ----------------
    def _inlines(self, p: Paragraph) -> tuple[list, list[str]]:
        inlines: list = []
        images: list[str] = []
        for item in p.iter_inner_content():
            if isinstance(item, Hyperlink):
                text = item.text
                if text:
                    href = item.address or (f"#{item.fragment}" if item.fragment else "")
                    marks = _marks(item.runs[0]) if item.runs else []
                    inlines.append(link_inline(text, href, marks))
            elif isinstance(item, Run):
                images.extend(self._run_images(item))
                text = item.text
                if not text:
                    continue
                marks = _marks(item)
                parts = text.split("\n")
                for i, part in enumerate(parts):
                    if i:
                        inlines.append(BreakInline())
                    if part:
                        inlines.append(text_inline(part.replace("\t", " "), marks))
        return merge_inlines(inlines), images

    def _run_images(self, run: Run) -> list[str]:
        found: list[str] = []
        for blip in run._r.iter(qn("a:blip")):
            rid = blip.get(qn("r:embed"))
            if not rid:
                continue
            try:
                part = run.part.related_parts[rid]
            except KeyError:
                continue
            mime = getattr(part, "content_type", "")
            blob: bytes = part.blob
            if mime not in _IMAGE_TYPES:
                self.warnings.append(f"Skipped unsupported image type {mime or 'unknown'}")
                continue
            if len(blob) > MAX_IMAGE_BYTES:
                self.warnings.append("Skipped an image larger than 10 MB")
                continue
            digest = hashlib.sha256(blob).hexdigest()
            asset_id = f"img_{digest[:16]}"
            if asset_id not in self.assets:
                self.assets[asset_id] = Asset(
                    id=asset_id,
                    mime_type=mime,
                    sha256=digest,
                    size=len(blob),
                    data_base64=base64.b64encode(blob).decode("ascii"),
                )
            alt = ""
            for doc_pr in run._r.iter(qn("wp:docPr")):
                alt = doc_pr.get("descr") or doc_pr.get("title") or ""
            found.append(f"{asset_id}\x00{alt}")
        return found

    def _emit_images(self, images: list[str]) -> None:
        for entry in images:
            asset_id, alt = entry.split("\x00", 1)
            self.blocks.append(ImageBlock(id=self.ids.next(), asset_id=asset_id, alt=alt))

    # ---------------- tables ----------------
    def table(self, t: Table) -> None:
        rows: list[list[list]] = []
        for row in t.rows:
            cells: list[list] = []
            seen: set[int] = set()
            for cell in row.cells:
                key = id(cell._tc)
                if key in seen:  # horizontally merged cells repeat
                    continue
                seen.add(key)
                content: list = []
                for i, p in enumerate(cell.paragraphs):
                    inl, _ = self._inlines(p)
                    if i and inl and content:
                        content.append(BreakInline())
                    content.extend(inl)
                cells.append(content)
            rows.append(cells)
        if not rows:
            return
        header_rows = 1 if _is_header_row(t) else 0
        self.blocks.append(TableBlock(id=self.ids.next(), rows=rows, header_rows=header_rows))


def _marks(run: Run) -> list[str]:
    marks = []
    if run.bold:
        marks.append("bold")
    if run.italic:
        marks.append("italic")
    if run.underline:
        marks.append("underline")
    font = run.font
    if font.strike:
        marks.append("strike")
    if font.superscript:
        marks.append("superscript")
    if font.subscript:
        marks.append("subscript")
    return marks


def _is_header_row(t: Table) -> bool:
    if len(t.rows) < 2:
        return False
    first = t.rows[0]
    trpr = first._tr.trPr
    if trpr is not None and trpr.find(qn("w:tblHeader")) is not None:
        return True
    runs = [r for c in first.cells for p in c.paragraphs for r in p.runs if r.text.strip()]
    return bool(runs) and all(r.bold for r in runs)
