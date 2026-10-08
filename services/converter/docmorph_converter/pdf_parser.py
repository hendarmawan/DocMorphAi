"""PDF -> text blocks. Text-layer only; layout fidelity is reported as partial."""

from __future__ import annotations

import io

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from docmorph_converter.markdown_parser import ParsedText
from docmorph_converter.text_parser import parse_text
from docmorph_converter.validation import ConversionError, UploadRejected

MAX_PAGES = 500


def parse_pdf(data: bytes) -> ParsedText:
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            raise UploadRejected("encrypted_pdf", "Password-protected PDFs are not supported")
        if len(reader.pages) > MAX_PAGES:
            raise UploadRejected("too_many_pages", f"PDFs are limited to {MAX_PAGES} pages")
        pages = [page.extract_text() or "" for page in reader.pages]
        meta_title = (reader.metadata.title if reader.metadata else None) or None
    except PdfReadError as exc:
        raise ConversionError(f"Could not read PDF: {exc}") from exc

    text = "\n\n".join(p.strip() for p in pages if p.strip())
    parsed = parse_text(text, pdf=True)
    parsed.warnings.append(
        "PDF conversion uses the text layer only; complex layouts, tables and images are partially supported."
    )
    if not text.strip():
        parsed.warnings.append("No extractable text found; the PDF may be scanned (OCR is not yet supported).")
    if meta_title:
        parsed.title = meta_title
    return parsed
