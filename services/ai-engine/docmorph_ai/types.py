from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class DocumentAnalysis(BaseModel):
    topic: str
    keywords: list[str]
    document_type: str
    suggested_template: str
    suggested_reader_mode: Literal["scroll", "paginate", "swipe"]
    rationale: str
    provider: str
