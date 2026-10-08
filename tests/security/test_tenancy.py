"""Tenant resolution in production: multi-tenant (header required) vs single-tenant deployments."""

from __future__ import annotations

import pytest
from docmorph_api.config import Settings
from docmorph_api.main import create_app
from fastapi.testclient import TestClient


def _client(tmp_path, **overrides):
    settings = Settings(
        env="production",
        database_url="sqlite:///:memory:",
        storage_local_path=str(tmp_path / "storage"),
        **overrides,
    )
    return TestClient(create_app(settings))


def test_production_requires_tenant_header_by_default(tmp_path):
    with _client(tmp_path) as c:
        res = c.get("/v1/documents")
        assert res.status_code == 401
        assert res.json()["error"]["code"] == "tenant_required"
        # Tenants are never created on the fly in multi-tenant production, not even the default one.
        assert c.get("/v1/documents", headers={"X-Tenant-ID": "default"}).status_code == 403


@pytest.mark.parametrize("tenant", ["acme", "default"])
def test_single_tenant_production_uses_default_tenant_only(tmp_path, tenant):
    with _client(tmp_path, require_tenant_header=False) as c:
        assert c.get("/v1/documents").status_code == 200
        expected = 200 if tenant == "default" else 403
        assert c.get("/v1/documents", headers={"X-Tenant-ID": tenant}).status_code == expected
