from __future__ import annotations

from typing import Annotated, Literal

from docmorph_publisher import export_standalone_html
from docmorph_renderer import RenderOptions, render_document
from fastapi import APIRouter, Query, Request, UploadFile
from fastapi.responses import HTMLResponse, Response
from sqlalchemy import select

from docmorph_api import service
from docmorph_api.errors import ApiError
from docmorph_api.models import DocumentRecord
from docmorph_api.schemas import DocumentSummary, StructureResponse, UploadResponse
from docmorph_api.tenancy import SessionDep, TenantDep

router = APIRouter(prefix="/v1/documents", tags=["documents"])

# Rendered documents are untrusted output: never allow them to run with the API's origin.
_RENDER_HEADERS = {
    "Content-Security-Policy": "sandbox allow-scripts; default-src 'none'; img-src data:; "
    "style-src 'unsafe-inline'; script-src 'unsafe-inline'",
    "X-Content-Type-Options": "nosniff",
    "Cache-Control": "no-store",
}


async def _read_limited(file: UploadFile, limit: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while chunk := await file.read(1024 * 1024):
        total += len(chunk)
        if total > limit:
            raise ApiError(413, "file_too_large", f"Files are limited to {limit // (1024 * 1024)} MB")
        chunks.append(chunk)
    return b"".join(chunks)


@router.post("", response_model=UploadResponse, status_code=201)
async def upload(request: Request, file: UploadFile, session: SessionDep, tenant: TenantDep):
    state = request.app.state
    declared = request.headers.get("content-length")
    if declared and declared.isdigit() and int(declared) > state.settings.max_upload_bytes + 64 * 1024:
        raise ApiError(413, "file_too_large", "Upload exceeds the size limit")
    data = await _read_limited(file, state.settings.max_upload_bytes)
    record, doc = service.create_document(session, state.storage, tenant, state.ai, data, file.filename or "document")
    return UploadResponse(
        document=service.summary(record, doc.source.fidelity),
        structure=service.structure(doc, record, state.ai),
    )


@router.get("", response_model=list[DocumentSummary])
def list_documents(session: SessionDep, tenant: TenantDep):
    records = session.scalars(
        select(DocumentRecord)
        .where(DocumentRecord.tenant_id == tenant.tenant_id)
        .order_by(DocumentRecord.created_at.desc())
        .limit(200)
    )
    out = []
    for r in records:
        doc = service.load_document(session, r)
        out.append(service.summary(r, doc.source.fidelity))
    return out


@router.get("/{document_id}", response_model=DocumentSummary)
def get_document(document_id: str, session: SessionDep, tenant: TenantDep):
    record = service.get_record(session, tenant, document_id)
    return service.summary(record, service.load_document(session, record).source.fidelity)


@router.get("/{document_id}/content")
def get_content(document_id: str, session: SessionDep, tenant: TenantDep) -> dict:
    """The canonical document JSON (schema v1)."""
    record = service.get_record(session, tenant, document_id)
    return service.load_document(session, record).to_json_dict()


@router.get("/{document_id}/structure", response_model=StructureResponse)
def get_structure(document_id: str, request: Request, session: SessionDep, tenant: TenantDep):
    record = service.get_record(session, tenant, document_id)
    return service.structure(service.load_document(session, record), record, request.app.state.ai)


@router.delete("/{document_id}", status_code=204)
def delete_document(document_id: str, request: Request, session: SessionDep, tenant: TenantDep):
    record = service.get_record(session, tenant, document_id)
    request.app.state.storage.delete(record.storage_key)
    session.delete(record)
    session.commit()
    return Response(status_code=204)


@router.get("/{document_id}/render", response_class=HTMLResponse)
def render(
    document_id: str,
    session: SessionDep,
    tenant: TenantDep,
    reader_mode: Annotated[Literal["scroll", "paginate", "swipe"] | None, Query()] = None,
):
    record = service.get_record(session, tenant, document_id)
    html = render_document(
        service.load_document(session, record),
        service.current_design(session, record),
        RenderOptions(reader_mode=reader_mode),
    )
    return HTMLResponse(html, headers=_RENDER_HEADERS)


@router.get("/{document_id}/export")
def export(document_id: str, session: SessionDep, tenant: TenantDep):
    record = service.get_record(session, tenant, document_id)
    result = export_standalone_html(service.load_document(session, record), service.current_design(session, record))
    return Response(
        result.html,
        media_type="text/html; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{result.filename}"',
            "X-Content-Type-Options": "nosniff",
            "X-DocMorph-SHA256": result.sha256,
        },
    )
