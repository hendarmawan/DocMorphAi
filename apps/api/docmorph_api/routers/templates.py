from __future__ import annotations

from docmorph_renderer import list_templates
from fastapi import APIRouter

from docmorph_api.schemas import TemplateSummary

router = APIRouter(prefix="/v1/templates", tags=["templates"])


@router.get("", response_model=list[TemplateSummary])
def templates() -> list[dict]:
    return list_templates()
