"""Upload validation: extension, magic bytes, encoding and archive safety."""

from __future__ import annotations

import io
import zipfile
from pathlib import PurePath
from typing import Literal

Format = Literal["docx", "pdf", "markdown", "txt"]

SUPPORTED_EXTENSIONS: dict[str, Format] = {
    ".docx": "docx",
    ".pdf": "pdf",
    ".md": "markdown",
    ".markdown": "markdown",
    ".txt": "txt",
}

# DOCX is a zip; refuse archives that would expand far beyond their upload size.
MAX_ZIP_ENTRIES = 2_000
MAX_ZIP_UNCOMPRESSED = 200 * 1024 * 1024
MAX_ZIP_RATIO = 100


class UploadRejected(ValueError):
    """The upload is not acceptable (wrong type, malformed, unsafe)."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class ConversionError(RuntimeError):
    """The file passed validation but could not be parsed."""


def safe_filename(filename: str) -> str:
    name = PurePath(filename.replace("\\", "/")).name.strip()
    cleaned = "".join(ch for ch in name if ch.isprintable() and ch not in '<>:"|?*')
    return cleaned[:200] or "document"


def detect_format(filename: str, data: bytes) -> Format:
    ext = PurePath(filename.lower()).suffix
    fmt = SUPPORTED_EXTENSIONS.get(ext)
    if fmt is None:
        allowed = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise UploadRejected("unsupported_format", f"Unsupported file type {ext or '(none)'}; allowed: {allowed}")
    if not data:
        raise UploadRejected("empty_file", "The uploaded file is empty")

    if fmt == "pdf":
        if not data.lstrip()[:5] == b"%PDF-":
            raise UploadRejected("content_mismatch", "File does not look like a PDF")
    elif fmt == "docx":
        _check_docx(data)
    else:
        if b"\x00" in data[:8192]:
            raise UploadRejected("content_mismatch", "Text file contains binary data")
        try:
            data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise UploadRejected("bad_encoding", "Text files must be UTF-8 encoded") from exc
    return fmt


def _check_docx(data: bytes) -> None:
    if not data.startswith(b"PK"):
        raise UploadRejected("content_mismatch", "File does not look like a DOCX document")
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            infos = zf.infolist()
            if len(infos) > MAX_ZIP_ENTRIES:
                raise UploadRejected("unsafe_archive", "DOCX contains too many parts")
            total = sum(i.file_size for i in infos)
            if total > MAX_ZIP_UNCOMPRESSED or total > MAX_ZIP_RATIO * max(len(data), 1):
                raise UploadRejected("unsafe_archive", "DOCX expands to an unsafe size")
            names = {i.filename for i in infos}
            if any(n.startswith("/") or ".." in PurePath(n).parts for n in names):
                raise UploadRejected("unsafe_archive", "DOCX contains unsafe paths")
            if "word/document.xml" not in names:
                raise UploadRejected("content_mismatch", "Zip file is not a Word document")
    except zipfile.BadZipFile as exc:
        raise UploadRejected("content_mismatch", "Corrupted DOCX file") from exc
