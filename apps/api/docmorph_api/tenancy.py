"""Tenant resolution.

Until authentication lands (M5), the tenant comes from the ``X-Tenant-ID``
header, falling back to a default tenant unless the header is required
(the production default, see ``Settings.require_tenant_header``). Every data access
goes through a ``TenantContext`` so queries are always ownership-scoped.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header, Request
from sqlalchemy.orm import Session

from docmorph_api.errors import ApiError
from docmorph_api.models import Tenant

_TENANT_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")


@dataclass(frozen=True)
class TenantContext:
    tenant_id: str


def get_session(request: Request):
    yield from request.app.state.db.session()


SessionDep = Annotated[Session, Depends(get_session)]


def get_tenant(
    request: Request,
    session: SessionDep,
    x_tenant_id: Annotated[str | None, Header()] = None,
) -> TenantContext:
    settings = request.app.state.settings
    tenant_id = (x_tenant_id or "").strip().lower()
    if not tenant_id:
        if settings.tenant_header_required:
            raise ApiError(401, "tenant_required", "X-Tenant-ID header is required")
        tenant_id = settings.default_tenant
    if not _TENANT_RE.match(tenant_id):
        raise ApiError(400, "invalid_tenant", "Tenant id must be 1-64 chars of a-z, 0-9, _ or -")
    if session.get(Tenant, tenant_id) is None:
        single_tenant = not settings.tenant_header_required and tenant_id == settings.default_tenant
        if settings.env == "production" and not single_tenant:
            raise ApiError(403, "unknown_tenant", "Unknown tenant")
        session.add(Tenant(id=tenant_id, name=tenant_id))
        session.commit()
    return TenantContext(tenant_id=tenant_id)


TenantDep = Annotated[TenantContext, Depends(get_tenant)]
