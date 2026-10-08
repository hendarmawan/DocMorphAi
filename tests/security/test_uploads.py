"""Upload restrictions: type validation, size limits and archive safety."""

from __future__ import annotations

import io
import zipfile

import pytest
from docmorph_converter import UploadRejected, detect_format
from docmorph_converter.validation import safe_filename


def _post(client, name, data, mime="application/octet-stream"):
    return client.post("/v1/documents", files={"file": (name, data, mime)})


@pytest.mark.parametrize(
    "name,data,code",
    [
        ("evil.exe", b"MZ\x90\x00", "unsupported_format"),
        ("evil.html", b"<script>alert(1)</script>", "unsupported_format"),
        ("fake.pdf", b"not a pdf at all", "content_mismatch"),
        ("fake.docx", b"plain text pretending", "content_mismatch"),
        ("binary.txt", b"abc\x00\x01\x02", "content_mismatch"),
        ("latin1.txt", "caf\u00e9".encode("latin-1"), "bad_encoding"),
        ("empty.md", b"", "empty_file"),
    ],
)
def test_rejects_invalid_uploads(client, name, data, code):
    res = _post(client, name, data)
    assert res.status_code in (415, 422)
    assert res.json()["error"]["code"] == code


def test_rejects_oversized_upload(client, settings):
    res = _post(client, "big.txt", b"a" * (settings.max_upload_bytes + 10), "text/plain")
    assert res.status_code == 413
    assert res.json()["error"]["code"] == "file_too_large"


def test_rejects_zip_bomb_docx():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("word/document.xml", b"0" * (50 * 1024 * 1024))
    with pytest.raises(UploadRejected) as exc:
        detect_format("bomb.docx", buf.getvalue())
    assert exc.value.code == "unsafe_archive"


def test_rejects_zip_without_word_document():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("hello.txt", b"hi")
    with pytest.raises(UploadRejected):
        detect_format("x.docx", buf.getvalue())


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("../../etc/passwd.md", "passwd.md"),
        ("C:\\Users\\me\\notes.txt", "notes.txt"),
        ('a<b>"c".md', "abc.md"),
        ("", "document"),
    ],
)
def test_filenames_are_sanitized(raw, expected):
    assert safe_filename(raw) == expected


def test_storage_keys_cannot_escape_root(tmp_path):
    from docmorph_api.storage import LocalStorage

    storage = LocalStorage(str(tmp_path))
    for key in ("../outside", "/abs/path", "a/../../b"):
        with pytest.raises(ValueError):
            storage.put(key, b"x", "text/plain")
