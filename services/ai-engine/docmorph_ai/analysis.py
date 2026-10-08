"""Deterministic document understanding used by the offline provider."""

from __future__ import annotations

import re
from collections import Counter

from docmorph_schema import Document, plain_text

from docmorph_ai.types import DocumentAnalysis

_WORD = re.compile(r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'-]{2,}")
_STOP = set(
    [
        "the",
        "and",
        "for",
        "are",
        "but",
        "not",
        "you",
        "all",
        "any",
        "can",
        "had",
        "her",
        "was",
        "one",
        "our",
        "out",
        "has",
        "have",
        "this",
        "that",
        "with",
        "from",
        "they",
        "will",
        "would",
        "there",
        "their",
        "what",
        "about",
        "which",
        "when",
        "your",
        "into",
        "than",
        "then",
        "them",
        "these",
        "some",
        "such",
        "only",
        "other",
        "also",
        "more",
        "most",
        "over",
        "very",
        "just",
        "like",
        "been",
        "were",
        "being",
        "does",
        "done",
        "each",
        "how",
        "its",
        "may",
        "upon",
        "shall",
        "should",
        "could",
        "within",
        "without",
        "between",
        "where",
        "while",
        "those",
        "through",
        "after",
        "before",
        "yang",
        "dan",
        "di",
        "ke",
        "dari",
        "untuk",
        "dengan",
        "pada",
        "adalah",
        "ini",
        "itu",
        "dalam",
        "tidak",
        "akan",
        "juga",
        "atau",
        "oleh",
        "sebagai",
        "karena",
        "bahwa",
        "telah",
        "dapat",
        "lebih",
        "para",
        "kami",
        "kita",
        "mereka",
        "saya",
        "anda",
    ]
)

_TYPE_SIGNALS: list[tuple[str, str, tuple[str, ...]]] = [
    (
        "research paper",
        "academic",
        (
            "abstract",
            "methodology",
            "references",
            "hypothesis",
            "literature",
            "results",
            "conclusion",
            "abstrak",
            "metodologi",
            "pustaka",
        ),
    ),
    (
        "business document",
        "corporate",
        ("revenue", "strategy", "stakeholder", "quarter", "budget", "proposal", "policy", "market", "kpi", "anggaran"),
    ),
    (
        "presentation",
        "presentation",
        ("agenda", "slide", "overview", "pitch", "workshop", "training", "objectives", "key takeaways"),
    ),
    ("bilingual material", "bilingual", ("translation", "terjemahan", "bilingual", "glossary", "vocabulary")),
]


def _words(doc: Document) -> list[str]:
    texts: list[str] = [doc.title]
    for b in doc.blocks:
        if b.type in ("heading", "paragraph", "quote"):
            texts.append(plain_text(b.content))
        elif b.type == "list":
            texts.extend(plain_text(i) for i in b.items)
        elif b.type == "table":
            texts.extend(plain_text(c) for row in b.rows for c in row)
    return [w.lower() for t in texts for w in _WORD.findall(t)]


def analyze_document(doc: Document, provider: str = "heuristic") -> DocumentAnalysis:
    words = _words(doc)
    counts = Counter(w for w in words if w not in _STOP)
    keywords = [w for w, _ in counts.most_common(8)]
    text = " ".join(words)

    headings = [b for b in doc.blocks if b.type == "heading"]
    paragraphs = [b for b in doc.blocks if b.type == "paragraph"]
    avg_section = len(paragraphs) / max(len(headings), 1)

    scored = []
    for label, template, signals in _TYPE_SIGNALS:
        score = sum(text.count(s) for s in signals)
        scored.append((score, label, template))
    scored.sort(key=lambda s: (-s[0], s[1]))
    best_score, doc_type, template = scored[0]

    if best_score == 0:
        if headings and avg_section <= 1.5 and len(headings) >= 4:
            doc_type, template = "presentation", "presentation"
        else:
            doc_type, template = "general document", "corporate" if headings else "academic"

    mode = "swipe" if template == "presentation" else ("paginate" if len(headings) >= 12 else "scroll")
    topic = doc.title.strip() or (", ".join(keywords[:3]).title() if keywords else "Untitled")
    rationale = (
        f"{len(headings)} headings, {len(paragraphs)} paragraphs"
        + (f"; matched {best_score} {doc_type} signal(s)" if best_score else "; no strong genre signals")
        + f". Suggested the {template} template with {mode} reading."
    )
    return DocumentAnalysis(
        topic=topic,
        keywords=keywords,
        document_type=doc_type,
        suggested_template=template,
        suggested_reader_mode=mode,  # type: ignore[arg-type]
        rationale=rationale,
        provider=provider,
    )
