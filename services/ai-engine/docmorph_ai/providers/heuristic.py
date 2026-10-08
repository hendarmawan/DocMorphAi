"""Offline, deterministic provider.

Interprets common design requests ("make it dark", "bigger serif text",
"swipe like slides") into design patches with no network access. It is the
default in development and CI, and the fallback when no hosted model is set up.
"""

from __future__ import annotations

import re

from docmorph_schema import DesignConfig, DesignPatch, Document, PatchOp

from docmorph_ai.analysis import analyze_document
from docmorph_ai.providers.base import ContentEditRefused, NoDesignChange
from docmorph_ai.types import DocumentAnalysis

_CONTENT_EDIT = re.compile(
    r"\b(rewrite|reword|paraphrase|summari[sz]e|translate|delete (the )?(paragraph|section|sentence)|"
    r"remove (the )?(paragraph|section|sentence)|change the (text|wording)|fix (the )?(typos|grammar)|"
    r"add (a )?(paragraph|section|sentence))\b",
    re.IGNORECASE,
)

_ACCENTS = {
    "blue": "#1d4ed8",
    "navy": "#1e3a8a",
    "green": "#15803d",
    "teal": "#0f766e",
    "red": "#b91c1c",
    "maroon": "#7a1f1f",
    "purple": "#7e22ce",
    "violet": "#6d28d9",
    "orange": "#c2410c",
    "amber": "#b45309",
    "pink": "#be185d",
    "gold": "#a16207",
    "black": "#111827",
    "gray": "#4b5563",
    "grey": "#4b5563",
}

_DARK = {"background": "#0f172a", "text": "#e5e7eb", "muted": "#94a3b8", "surface": "#1e293b"}
_LIGHT = {"background": "#ffffff", "text": "#1f2937", "muted": "#6b7280", "surface": "#f3f4f6"}
_SEPIA = {"background": "#f6efe1", "text": "#3b2f20", "muted": "#7c6a53", "surface": "#ece2cc"}

_TEMPLATES = ("academic", "corporate", "bilingual", "presentation")


def _has(text: str, *phrases: str) -> bool:
    return any(re.search(rf"\b{p}\b", text) for p in phrases)


class HeuristicProvider:
    name = "heuristic"

    def analyze(self, doc: Document) -> DocumentAnalysis:
        return analyze_document(doc, provider=self.name)

    def design_patch(self, prompt: str, design: DesignConfig, doc: Document) -> DesignPatch:
        text = prompt.lower().strip()
        if _CONTENT_EDIT.search(text):
            raise ContentEditRefused(
                "Design prompts change presentation only. Content edits (rewriting, translating, "
                "deleting text) are not applied so the source document is never silently changed."
            )

        ops: list[PatchOp] = []
        notes: list[str] = []

        def put(path: str, value, note: str) -> None:
            ops.append(PatchOp(path=path, value=value))
            notes.append(note)

        t = design.typography
        lay = design.layout

        for name in _TEMPLATES:
            if _has(text, name) and _has(text, "template", "style", "look", "like", "use", "switch"):
                put("/template_id", name, f"switched to the {name} template")

        # --- typography ---
        if _has(text, "bigger", "larger", "increase", "more readable", "easier to read") and _has(
            text, "text", "font", "type", "size", "readable", "read"
        ):
            put("/typography/base_size_px", min(t.base_size_px + 2, 28), "increased text size")
        elif _has(text, "smaller", "decrease", "denser") and _has(text, "text", "font", "type", "size"):
            put("/typography/base_size_px", max(t.base_size_px - 2, 12), "decreased text size")

        for family, words in (
            ("serif", ("serif", "classic", "elegant", "bookish")),
            ("sans", ("sans", "sans-serif", "modern", "clean")),
            ("mono", ("monospace", "mono", "typewriter", "code-like")),
            ("slab", ("slab", "bold headings")),
            ("humanist", ("humanist", "friendly", "warm font")),
        ):
            if _has(text, *words) and not (family == "serif" and _has(text, "sans", "sans-serif")):
                target = "/typography/heading_font" if _has(text, "heading", "headings", "titles") else None
                if target:
                    put(target, family, f"set heading font to {family}")
                else:
                    put("/typography/body_font", family, f"set body font to {family}")
                    put("/typography/heading_font", family, f"set heading font to {family}")
                break

        if _has(text, "more line spacing", "line height", "airier", "more leading", "double spaced"):
            put("/typography/line_height", min(round(t.line_height + 0.2, 2), 2.2), "increased line height")
        if _has(text, "tighter lines", "less line spacing"):
            put("/typography/line_height", max(round(t.line_height - 0.2, 2), 1.1), "decreased line height")

        # --- colors ---
        palette = None
        if _has(text, "dark", "dark mode", "night", "darker"):
            palette, label = _DARK, "dark palette"
        elif _has(text, "sepia", "paper", "warm background"):
            palette, label = _SEPIA, "sepia palette"
        elif _has(text, "light mode", "light theme", "light background", "white background", "brighter"):
            palette, label = _LIGHT, "light palette"
        if palette:
            for key, value in palette.items():
                ops.append(PatchOp(path=f"/colors/{key}", value=value))
            notes.append(f"applied a {label}")
        for color, hex_ in _ACCENTS.items():
            if _has(text, color):
                put("/colors/accent", hex_, f"set accent colour to {color}")
                break

        # --- layout ---
        if _has(text, "two columns", "two-column", "2 columns", "side by side"):
            put("/layout/columns", 2, "switched to two columns")
            if lay.max_width_px < 1000:
                put("/layout/max_width_px", 1200, "widened the page for two columns")
        elif _has(text, "one column", "single column", "single-column"):
            put("/layout/columns", 1, "switched to a single column")
        if _has(text, "wider", "full width", "wide layout"):
            put("/layout/max_width_px", min(lay.max_width_px + 200, 1600), "widened the page")
        elif _has(text, "narrower", "narrow", "focused"):
            put("/layout/max_width_px", max(lay.max_width_px - 160, 480), "narrowed the page")
        if _has(text, "compact", "tight", "less space", "less whitespace"):
            put("/layout/spacing", "compact", "used compact spacing")
        elif _has(text, "spacious", "more space", "more whitespace", "breathing room", "relaxed"):
            put("/layout/spacing", "relaxed", "used relaxed spacing")
        if _has(text, "justify", "justified"):
            put("/layout/align", "justify", "justified paragraphs")
        elif _has(text, "left align", "left-align", "ragged"):
            put("/layout/align", "left", "left-aligned paragraphs")
        elif _has(text, "center", "centre", "centered", "centred"):
            put("/layout/align", "center", "centred paragraphs")
        if _has(text, "table of contents", "toc"):
            off = _has(text, "remove", "hide", "no", "without")
            put("/layout/show_toc", not off, "hid the table of contents" if off else "added a table of contents")
        if _has(text, "cover"):
            off = _has(text, "remove", "hide", "no", "without")
            put("/layout/cover", not off, "removed the cover" if off else "added a cover header")

        # --- reader ---
        if _has(text, "swipe", "slides", "slideshow", "deck", "presentation mode"):
            put("/reader/mode", "swipe", "enabled swipe reading")
        elif _has(text, "paginate", "paginated", "paged", "page by page", "book-like"):
            put("/reader/mode", "paginate", "enabled paginated reading")
        elif _has(text, "scroll", "scrolling", "continuous"):
            put("/reader/mode", "scroll", "enabled continuous scrolling")

        if not ops:
            raise NoDesignChange(
                "I couldn't map that to a design change. Try describing typography (bigger serif "
                "text), colours (dark mode, blue accent), layout (two columns, more space) or "
                "reading mode (swipe like slides)."
            )
        summary = "; ".join(dict.fromkeys(notes))
        return DesignPatch(summary=summary[:1].upper() + summary[1:], ops=ops)
