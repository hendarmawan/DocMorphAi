from __future__ import annotations

import json
import os
from functools import cache
from pathlib import Path

from docmorph_schema import DesignConfig


class TemplateNotFound(KeyError):
    pass


def templates_dir() -> Path:
    override = os.environ.get("DOCMORPH_TEMPLATES_DIR")
    if override:
        return Path(override)
    # Monorepo layout: services/renderer/docmorph_renderer -> packages/templates/templates
    return Path(__file__).resolve().parents[3] / "packages" / "templates" / "templates"


@cache
def _load() -> dict[str, dict]:
    root = templates_dir()
    found: dict[str, dict] = {}
    for path in sorted(root.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        DesignConfig.model_validate(data["design"])  # fail fast on a broken template
        found[data["id"]] = data
    if not found:
        raise FileNotFoundError(f"No templates found in {root}")
    return found


def list_templates() -> list[dict]:
    return list(_load().values())


def get_template(template_id: str) -> dict:
    try:
        return _load()[template_id]
    except KeyError as exc:
        raise TemplateNotFound(template_id) from exc


def template_design(template_id: str) -> DesignConfig:
    return DesignConfig.model_validate(get_template(template_id)["design"])
