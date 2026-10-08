"""HTTP response/request models (mirrored in packages/shared-types)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from docmorph_ai import DocumentAnalysis
from docmorph_schema import DesignConfig, DesignPatch
from pydantic import BaseModel, Field


class DocumentSummary(BaseModel):
    id: str
    title: str
    source_format: str
    filename: str
    size_bytes: int
    fidelity: Literal["full", "partial"]
    created_at: datetime
    current_version: int
    current_design_version: int


class OutlineEntry(BaseModel):
    id: str
    level: int
    title: str


class StructureResponse(BaseModel):
    document_id: str
    version: int
    outline: list[OutlineEntry]
    counts: dict[str, int]
    word_count: int
    warnings: list[str]
    analysis: DocumentAnalysis


class UploadResponse(BaseModel):
    document: DocumentSummary
    structure: StructureResponse


class TemplateSummary(BaseModel):
    id: str
    name: str
    description: str
    suited_for: list[str]
    design: DesignConfig


class DesignVersion(BaseModel):
    version: int
    design: DesignConfig
    origin: Literal["template", "manual", "ai", "restore"]
    summary: str
    created_at: datetime
    is_current: bool


class DesignState(BaseModel):
    current: DesignVersion
    can_undo: bool
    can_redo: bool


class TemplateRequest(BaseModel):
    template_id: str = Field(min_length=1, max_length=64)


class DesignUpdateRequest(BaseModel):
    design: DesignConfig
    summary: str = Field(default="Manual edit", max_length=200)


class PromptRequest(BaseModel):
    prompt: str = Field(min_length=2, max_length=1000)


class PromptResult(BaseModel):
    patch: DesignPatch
    design: DesignVersion
    content_unchanged: bool
    provider: str


class RestoreRequest(BaseModel):
    version: int = Field(ge=1)
