"""Writes docs/openapi.json from the FastAPI app (CI checks it stays current)."""

import json
from pathlib import Path

from docmorph_api.config import Settings
from docmorph_api.main import create_app

out = Path(__file__).resolve().parents[1] / "docs" / "openapi.json"
app = create_app(Settings(database_url="sqlite:///:memory:", storage_local_path="var/openapi-storage"))
out.write_text(json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(f"wrote {out}")
