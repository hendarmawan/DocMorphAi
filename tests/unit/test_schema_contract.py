"""The pydantic models, JSON Schemas and templates must agree."""

from __future__ import annotations

import json

import pytest
from docmorph_converter import convert
from docmorph_renderer.templates import list_templates, template_design
from docmorph_schema import DesignPatch, PatchError, apply_design_patch, json_schema_dir
from fixtures.factory import SAMPLE_MARKDOWN, make_docx
from jsonschema import Draft202012Validator


def _validator(name: str) -> Draft202012Validator:
    schema = json.loads((json_schema_dir() / name).read_text())
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


@pytest.mark.parametrize(
    "data,filename",
    [(make_docx(), "report.docx"), (SAMPLE_MARKDOWN.encode(), "notes.md"), (b"Title\n\nBody text.", "a.txt")],
)
def test_converted_documents_match_json_schema(data, filename):
    doc = convert(data, filename, document_id="doc_test")
    errors = list(_validator("document.v1.schema.json").iter_errors(doc.to_json_dict()))
    assert not errors, errors[0].message


def test_templates_match_design_schema():
    validator = _validator("design.v1.schema.json")
    templates = list_templates()
    assert len(templates) >= 4
    for t in templates:
        assert not list(validator.iter_errors(t["design"])), t["id"]


def test_patch_applies_design_changes():
    design = template_design("academic")
    patch = DesignPatch(
        ops=[{"path": "/typography/base_size_px", "value": 20}, {"path": "/colors/accent", "value": "#123456"}]
    )
    updated = apply_design_patch(design, patch)
    assert updated.typography.base_size_px == 20
    assert updated.colors.accent == "#123456"
    assert design.typography.base_size_px == 18  # original untouched


@pytest.mark.parametrize(
    "path,value",
    [
        ("/blocks", []),  # content namespace
        ("/title", "hijacked"),  # content namespace
        ("/colors/accent", "red"),  # not a hex colour
        ("/typography/base_size_px", 99),  # out of range
        ("/layout/unknown", 1),  # unknown field
    ],
)
def test_patch_rejects_invalid_or_content_paths(path, value):
    with pytest.raises((PatchError, ValueError)):
        apply_design_patch(template_design("corporate"), DesignPatch(ops=[{"path": path, "value": value}]))
