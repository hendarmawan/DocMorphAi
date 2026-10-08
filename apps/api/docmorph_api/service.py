"""Document workflow logic shared by the routers (upload, versions, design history)."""

from __future__ import annotations

import secrets
from collections import Counter

from docmorph_ai import AIProvider
from docmorph_converter import ConversionError, UploadRejected, convert
from docmorph_renderer.templates import TemplateNotFound, template_design
from docmorph_schema import DesignConfig, Document, content_fingerprint, plain_text
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from docmorph_api.errors import ApiError
from docmorph_api.models import DesignVersionRecord, DocumentRecord, DocumentVersion
from docmorph_api.schemas import (
    DesignState,
    DesignVersion,
    DocumentSummary,
    OutlineEntry,
    StructureResponse,
)
from docmorph_api.storage import ObjectStorage
from docmorph_api.tenancy import TenantContext

_MIME = {
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "pdf": "application/pdf",
    "markdown": "text/markdown",
    "txt": "text/plain",
}


def new_document_id() -> str:
    return "doc_" + secrets.token_hex(12)


# ---------------------------------------------------------------- lookups
def get_record(session: Session, tenant: TenantContext, document_id: str) -> DocumentRecord:
    record = session.scalar(
        select(DocumentRecord).where(DocumentRecord.id == document_id, DocumentRecord.tenant_id == tenant.tenant_id)
    )
    if record is None:  # same answer for "missing" and "someone else's"
        raise ApiError(404, "document_not_found", "Document not found")
    return record


def load_document(session: Session, record: DocumentRecord) -> Document:
    version = session.scalar(
        select(DocumentVersion).where(
            DocumentVersion.document_id == record.id,
            DocumentVersion.tenant_id == record.tenant_id,
            DocumentVersion.version == record.current_version,
        )
    )
    assert version is not None
    return Document.model_validate(version.content)


def _design_rows(session: Session, record: DocumentRecord) -> list[DesignVersionRecord]:
    return list(
        session.scalars(
            select(DesignVersionRecord)
            .where(
                DesignVersionRecord.document_id == record.id,
                DesignVersionRecord.tenant_id == record.tenant_id,
            )
            .order_by(DesignVersionRecord.version)
        )
    )


def current_design(session: Session, record: DocumentRecord) -> DesignConfig:
    row = session.scalar(
        select(DesignVersionRecord).where(
            DesignVersionRecord.document_id == record.id,
            DesignVersionRecord.tenant_id == record.tenant_id,
            DesignVersionRecord.version == record.design_cursor,
        )
    )
    assert row is not None
    return DesignConfig.model_validate(row.design)


# ---------------------------------------------------------------- views
def summary(record: DocumentRecord, fidelity: str) -> DocumentSummary:
    return DocumentSummary(
        id=record.id,
        title=record.title,
        source_format=record.source_format,
        filename=record.filename,
        size_bytes=record.size_bytes,
        fidelity=fidelity,  # type: ignore[arg-type]
        created_at=record.created_at,
        current_version=record.current_version,
        current_design_version=record.design_cursor,
    )


def structure(doc: Document, record: DocumentRecord, provider: AIProvider) -> StructureResponse:
    counts = Counter(b.type for b in doc.blocks)
    words = 0
    for b in doc.blocks:
        if b.type in ("heading", "paragraph", "quote"):
            words += len(plain_text(b.content).split())
        elif b.type == "list":
            words += sum(len(plain_text(i).split()) for i in b.items)
        elif b.type == "table":
            words += sum(len(plain_text(c).split()) for row in b.rows for c in row)
    return StructureResponse(
        document_id=record.id,
        version=record.current_version,
        outline=[
            OutlineEntry(id=b.id, level=b.level, title=plain_text(b.content)) for b in doc.blocks if b.type == "heading"
        ],
        counts=dict(sorted(counts.items())),
        word_count=words,
        warnings=doc.source.warnings,
        analysis=provider.analyze(doc),
    )


def _version_view(row: DesignVersionRecord, cursor: int) -> DesignVersion:
    return DesignVersion(
        version=row.version,
        design=DesignConfig.model_validate(row.design),
        origin=row.origin,  # type: ignore[arg-type]
        summary=row.summary,
        created_at=row.created_at,
        is_current=row.version == cursor,
    )


def design_state(session: Session, record: DocumentRecord) -> DesignState:
    rows = _design_rows(session, record)
    current = next(r for r in rows if r.version == record.design_cursor)
    return DesignState(
        current=_version_view(current, record.design_cursor),
        can_undo=record.design_cursor > rows[0].version,
        can_redo=record.design_cursor < rows[-1].version,
    )


def design_history(session: Session, record: DocumentRecord) -> list[DesignVersion]:
    return [_version_view(r, record.design_cursor) for r in _design_rows(session, record)]


# ---------------------------------------------------------------- mutations
def create_document(
    session: Session,
    storage: ObjectStorage,
    tenant: TenantContext,
    provider: AIProvider,
    data: bytes,
    filename: str,
) -> tuple[DocumentRecord, Document]:
    doc_id = new_document_id()
    try:
        doc = convert(data, filename, document_id=doc_id)
    except UploadRejected as exc:
        status = 415 if exc.code in ("unsupported_format", "content_mismatch") else 422
        raise ApiError(status, exc.code, str(exc)) from exc
    except ConversionError as exc:
        raise ApiError(422, "conversion_failed", str(exc)) from exc
    if not doc.blocks:
        raise ApiError(422, "empty_document", "No readable content was found in the file")

    key = f"tenants/{tenant.tenant_id}/documents/{doc_id}/original/{doc.source.sha256}"
    storage.put(key, data, _MIME[doc.source.format])

    analysis = provider.analyze(doc)
    design = template_design(analysis.suggested_template)
    design = design.model_copy(
        update={"reader": design.reader.model_copy(update={"mode": analysis.suggested_reader_mode})}
    )

    record = DocumentRecord(
        id=doc_id,
        tenant_id=tenant.tenant_id,
        title=doc.title[:500],
        source_format=doc.source.format,
        filename=doc.source.filename,
        size_bytes=len(data),
        sha256=doc.source.sha256,
        storage_key=key,
        current_version=1,
        design_cursor=1,
    )
    session.add(record)
    session.add(
        DocumentVersion(
            tenant_id=tenant.tenant_id,
            document_id=doc_id,
            version=1,
            schema_version=doc.schema_version,
            content=doc.to_json_dict(),
            content_fingerprint=content_fingerprint(doc),
        )
    )
    session.add(
        DesignVersionRecord(
            tenant_id=tenant.tenant_id,
            document_id=doc_id,
            version=1,
            design=design.model_dump(mode="json"),
            origin="template",
            summary=f"Started from the {analysis.suggested_template} template (suggested)",
        )
    )
    session.commit()
    return record, doc


def push_design(
    session: Session,
    record: DocumentRecord,
    design: DesignConfig,
    origin: str,
    summary_text: str,
    patch: dict | None = None,
) -> DesignState:
    """Append a design version after the cursor, discarding any redo branch."""
    session.execute(
        delete(DesignVersionRecord).where(
            DesignVersionRecord.document_id == record.id,
            DesignVersionRecord.tenant_id == record.tenant_id,
            DesignVersionRecord.version > record.design_cursor,
        )
    )
    new_version = record.design_cursor + 1
    session.add(
        DesignVersionRecord(
            tenant_id=record.tenant_id,
            document_id=record.id,
            version=new_version,
            design=design.model_dump(mode="json"),
            origin=origin,
            summary=summary_text[:500],
            patch=patch,
        )
    )
    record.design_cursor = new_version
    session.commit()
    return design_state(session, record)


def apply_template(session: Session, record: DocumentRecord, template_id: str) -> DesignState:
    try:
        design = template_design(template_id)
    except TemplateNotFound as exc:
        raise ApiError(404, "template_not_found", f"Unknown template {template_id!r}") from exc
    return push_design(session, record, design, "template", f"Applied the {template_id} template")


def move_cursor(session: Session, record: DocumentRecord, delta: int) -> DesignState:
    versions = [r.version for r in _design_rows(session, record)]
    target = record.design_cursor + delta
    if target not in versions:
        raise ApiError(
            409, "nothing_to_" + ("undo" if delta < 0 else "redo"), "Nothing to " + ("undo" if delta < 0 else "redo")
        )
    record.design_cursor = target
    session.commit()
    return design_state(session, record)


def restore(session: Session, record: DocumentRecord, version: int) -> DesignState:
    row = next((r for r in _design_rows(session, record) if r.version == version), None)
    if row is None:
        raise ApiError(404, "version_not_found", f"Design version {version} not found")
    return push_design(
        session,
        record,
        DesignConfig.model_validate(row.design),
        "restore",
        f"Restored design version {version}",
    )
