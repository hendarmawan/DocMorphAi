"""Validated design patches.

AI (and manual) design edits are expressed as a small list of ``replace``
operations against the :class:`DesignConfig`. Anything that targets a path
outside the design namespaces is rejected, so a patch can never alter content.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from docmorph_schema.design import Colors, DesignConfig, Layout, ReaderSettings, Typography

ALLOWED_ROOTS = ("typography", "colors", "layout", "reader", "template_id")
_SECTION_MODELS: dict[str, type[BaseModel]] = {
    "typography": Typography,
    "colors": Colors,
    "layout": Layout,
    "reader": ReaderSettings,
}


class PatchError(ValueError):
    pass


class PatchOp(BaseModel):
    model_config = ConfigDict(extra="forbid")

    op: Literal["replace"] = "replace"
    path: str = Field(pattern=r"^/[a-z_]+(/[a-z_]+)?$")
    value: Any


class DesignPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["design"] = "design"
    summary: str = ""
    ops: list[PatchOp] = Field(min_length=1, max_length=40)


def apply_design_patch(design: DesignConfig, patch: DesignPatch) -> DesignConfig:
    data = design.model_dump(mode="json")
    for op in patch.ops:
        parts = op.path.strip("/").split("/")
        if parts[0] not in ALLOWED_ROOTS:
            raise PatchError(f"path {op.path!r} is outside the design namespace")
        if parts[0] == "template_id":
            if len(parts) != 1:
                raise PatchError(f"invalid path {op.path!r}")
            data["template_id"] = op.value
            continue
        if len(parts) != 2:
            raise PatchError(f"path {op.path!r} must name a single design field")
        if parts[1] not in _SECTION_MODELS[parts[0]].model_fields:
            raise PatchError(f"unknown design field {op.path!r}")
        data[parts[0]][parts[1]] = op.value
    try:
        return DesignConfig.model_validate(data)
    except ValidationError as exc:
        raise PatchError(f"patch produces an invalid design: {exc.errors()[0]['msg']}") from exc
