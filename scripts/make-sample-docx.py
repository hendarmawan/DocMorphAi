"""Regenerates tests/fixtures/files/quarterly-report.docx (used by the e2e smoke test)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))

from fixtures.factory import make_docx  # noqa: E402

out = ROOT / "tests" / "fixtures" / "files" / "quarterly-report.docx"
out.write_bytes(make_docx())
print(f"wrote {out}")
