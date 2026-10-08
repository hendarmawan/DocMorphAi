from __future__ import annotations

from typing import Protocol

from docmorph_schema import DesignConfig, DesignPatch, Document

from docmorph_ai.types import DocumentAnalysis


class NoDesignChange(ValueError):
    """The prompt did not translate into any design change."""


class ContentEditRefused(ValueError):
    """The prompt asks to change document content, which design prompts may not do."""


class AIProvider(Protocol):
    name: str

    def analyze(self, doc: Document) -> DocumentAnalysis: ...

    def design_patch(self, prompt: str, design: DesignConfig, doc: Document) -> DesignPatch: ...
