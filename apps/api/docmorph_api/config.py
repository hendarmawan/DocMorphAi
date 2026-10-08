from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DOCMORPH_", env_file=".env", extra="ignore")

    env: Literal["development", "test", "production"] = "development"
    database_url: str = "sqlite:///./var/docmorph.db"
    redis_url: str | None = None

    storage_backend: Literal["local", "s3"] = "local"
    storage_local_path: str = "./var/storage"
    s3_endpoint_url: str | None = None
    s3_bucket: str = "docmorph"
    s3_access_key: str | None = None
    s3_secret_key: str | None = None
    s3_region: str = "us-east-1"

    max_upload_bytes: int = Field(default=25 * 1024 * 1024, ge=1024)
    cors_origins: list[str] = ["http://localhost:3000"]
    default_tenant: str = "default"

    ai_provider: Literal["heuristic", "anthropic"] = "heuristic"
    ai_model: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
