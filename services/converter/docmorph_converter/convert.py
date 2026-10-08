from __future__ import annotations

import hashlib
from pathlib import PurePath

from docmorph_schema import Document, Source

from docmorph_converter.validation import ConversionError, detect_format, safe_filename


def convert(data: bytes, filename: str, *, document_id: str, language: str = "en") -> Document:
    """Validate and convert an uploaded file into the canonical document model.

    Raises :class:`UploadRejected` for invalid uploads and :class:`ConversionError`
    when a valid file cannot be parsed.
    """
    fmt = detect_format(filename, data)
    name = safe_filename(filename)
    warnings: list[str] = []
    metadata: dict[str, str] = {}
    assets = {}
    fidelity = "full"

    try:
        if fmt == "docx":
            from docmorph_converter.docx_parser import parse_docx

            parsed = parse_docx(data)
            assets = parsed.assets
            metadata = parsed.metadata
        elif fmt == "pdf":
            from docmorph_converter.pdf_parser import parse_pdf

            parsed = parse_pdf(data)
            fidelity = "partial"
        elif fmt == "markdown":
            from docmorph_converter.markdown_parser import parse_markdown

            parsed = parse_markdown(data.decode("utf-8-sig"))
        else:
            from docmorph_converter.text_parser import parse_text

            parsed = parse_text(data.decode("utf-8-sig"))
    except (ConversionError, ValueError):
        raise
    except Exception as exc:  # parser libraries raise a wide variety of errors
        raise ConversionError(f"Could not parse {fmt.upper()} file") from exc

    warnings.extend(dict.fromkeys(parsed.warnings))  # de-duplicate, keep order
    title = (parsed.title or PurePath(name).stem).strip() or "Untitled document"

    return Document(
        id=document_id,
        title=title,
        language=language,
        source=Source(
            format=fmt,
            filename=name,
            sha256=hashlib.sha256(data).hexdigest(),
            fidelity=fidelity,
            warnings=warnings,
        ),
        metadata=metadata,
        blocks=parsed.blocks,
        assets=assets,
    )
