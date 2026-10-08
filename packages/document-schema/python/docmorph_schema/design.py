from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

FontFamily = Literal["serif", "sans", "mono", "humanist", "slab"]
HexColor = str


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Typography(_Strict):
    body_font: FontFamily
    heading_font: FontFamily
    base_size_px: float = Field(ge=12, le=28)
    line_height: float = Field(ge=1.1, le=2.2)
    scale: float = Field(ge=1.05, le=1.6)
    heading_weight: int = Field(default=700, ge=300, le=900)


_HEX = r"^#[0-9a-fA-F]{6}$"


class Colors(_Strict):
    background: HexColor = Field(pattern=_HEX)
    text: HexColor = Field(pattern=_HEX)
    accent: HexColor = Field(pattern=_HEX)
    muted: HexColor = Field(pattern=_HEX)
    surface: HexColor = Field(pattern=_HEX)


class Layout(_Strict):
    max_width_px: int = Field(ge=480, le=1600)
    columns: int = Field(ge=1, le=2)
    spacing: Literal["compact", "normal", "relaxed"]
    align: Literal["left", "justify", "center"]
    show_toc: bool = False
    cover: bool = False


class ReaderSettings(_Strict):
    mode: Literal["scroll", "paginate", "swipe"] = "scroll"


class DesignConfig(_Strict):
    schema_version: Literal["1.0"] = "1.0"
    template_id: str
    typography: Typography
    colors: Colors
    layout: Layout
    reader: ReaderSettings = Field(default_factory=ReaderSettings)
