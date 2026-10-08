from __future__ import annotations

from dataclasses import dataclass

from docmorph_renderer.templates import template_design
from docmorph_schema import DesignConfig, DesignPatch, Document, apply_design_patch, content_fingerprint

from docmorph_ai.providers.base import AIProvider


@dataclass(frozen=True)
class DesignChange:
    patch: DesignPatch
    design: DesignConfig
    content_unchanged: bool


def propose_design_change(provider: AIProvider, prompt: str, design: DesignConfig, doc: Document) -> DesignChange:
    """Ask the provider for a patch, validate it, and apply it to the design only.

    Switching ``template_id`` resets to that template's defaults first, then the
    remaining ops are layered on top, so "use the academic template in dark mode"
    behaves as expected.
    """
    before = content_fingerprint(doc)
    patch = provider.design_patch(prompt, design, doc)

    base = design
    ops = list(patch.ops)
    template_ops = [op for op in ops if op.path == "/template_id"]
    if template_ops:
        base = template_design(str(template_ops[-1].value))
        ops = [op for op in ops if op.path != "/template_id"]

    new_design = apply_design_patch(base, DesignPatch(summary=patch.summary, ops=ops)) if ops else base
    return DesignChange(
        patch=patch,
        design=new_design,
        content_unchanged=content_fingerprint(doc) == before,
    )
