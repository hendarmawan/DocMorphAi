import json
from pathlib import Path

SPEC = Path(__file__).resolve().parents[2] / "docs" / "openapi.json"


def test_committed_openapi_spec_is_current(client):
    committed = json.loads(SPEC.read_text(encoding="utf-8"))
    assert client.app.openapi() == committed, "Run `uv run python scripts/export-openapi.py` and commit"
