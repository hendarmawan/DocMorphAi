from __future__ import annotations

from docmorph_ai import ContentEditRefused, NoDesignChange, propose_design_change
from docmorph_schema import PatchError
from fastapi import APIRouter, Request

from docmorph_api import service
from docmorph_api.errors import ApiError
from docmorph_api.schemas import (
    DesignState,
    DesignUpdateRequest,
    DesignVersion,
    PromptRequest,
    PromptResult,
    RestoreRequest,
    TemplateRequest,
)
from docmorph_api.tenancy import SessionDep, TenantDep

router = APIRouter(prefix="/v1/documents/{document_id}/design", tags=["design"])


@router.get("", response_model=DesignState)
def get_design(document_id: str, session: SessionDep, tenant: TenantDep):
    return service.design_state(session, service.get_record(session, tenant, document_id))


@router.get("/versions", response_model=list[DesignVersion])
def versions(document_id: str, session: SessionDep, tenant: TenantDep):
    return service.design_history(session, service.get_record(session, tenant, document_id))


@router.put("", response_model=DesignState)
def update_design(document_id: str, body: DesignUpdateRequest, session: SessionDep, tenant: TenantDep):
    record = service.get_record(session, tenant, document_id)
    return service.push_design(session, record, body.design, "manual", body.summary)


@router.post("/template", response_model=DesignState)
def apply_template(document_id: str, body: TemplateRequest, session: SessionDep, tenant: TenantDep):
    record = service.get_record(session, tenant, document_id)
    return service.apply_template(session, record, body.template_id)


@router.post("/prompt", response_model=PromptResult)
def prompt(document_id: str, body: PromptRequest, request: Request, session: SessionDep, tenant: TenantDep):
    record = service.get_record(session, tenant, document_id)
    doc = service.load_document(session, record)
    provider = request.app.state.ai
    try:
        change = propose_design_change(provider, body.prompt, service.current_design(session, record), doc)
    except ContentEditRefused as exc:
        raise ApiError(422, "content_edit_refused", str(exc)) from exc
    except NoDesignChange as exc:
        raise ApiError(422, "no_design_change", str(exc)) from exc
    except PatchError as exc:
        raise ApiError(422, "invalid_patch", str(exc)) from exc
    if not change.content_unchanged:  # defence in depth; design patches cannot reach content
        raise ApiError(500, "content_changed", "Design change altered document content; discarded")
    state = service.push_design(
        session, record, change.design, "ai", change.patch.summary, change.patch.model_dump(mode="json")
    )
    return PromptResult(patch=change.patch, design=state.current, content_unchanged=True, provider=provider.name)


@router.post("/undo", response_model=DesignState)
def undo(document_id: str, session: SessionDep, tenant: TenantDep):
    return service.move_cursor(session, service.get_record(session, tenant, document_id), -1)


@router.post("/redo", response_model=DesignState)
def redo(document_id: str, session: SessionDep, tenant: TenantDep):
    return service.move_cursor(session, service.get_record(session, tenant, document_id), +1)


@router.post("/restore", response_model=DesignState)
def restore(document_id: str, body: RestoreRequest, session: SessionDep, tenant: TenantDep):
    return service.restore(session, service.get_record(session, tenant, document_id), body.version)
