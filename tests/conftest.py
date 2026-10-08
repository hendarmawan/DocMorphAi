from __future__ import annotations

import pytest
from docmorph_api.config import Settings
from docmorph_api.main import create_app
from fastapi.testclient import TestClient


@pytest.fixture
def settings(tmp_path) -> Settings:
    return Settings(
        env="test",
        database_url="sqlite:///:memory:",
        storage_local_path=str(tmp_path / "storage"),
        max_upload_bytes=2 * 1024 * 1024,
    )


@pytest.fixture
def client(settings):
    with TestClient(create_app(settings)) as c:
        yield c
