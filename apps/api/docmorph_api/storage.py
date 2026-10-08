"""Object storage behind one interface: local disk for development, any
S3-compatible service (AWS S3, MinIO, R2) for deployments."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Protocol

from docmorph_api.config import Settings

_KEY = re.compile(r"^[A-Za-z0-9_\-./]+$")


def _check_key(key: str) -> str:
    if not _KEY.match(key) or ".." in key.split("/") or key.startswith("/"):
        raise ValueError(f"invalid storage key {key!r}")
    return key


class ObjectStorage(Protocol):
    def put(self, key: str, data: bytes, content_type: str) -> None: ...

    def get(self, key: str) -> bytes: ...

    def delete(self, key: str) -> None: ...

    def ping(self) -> bool: ...


class LocalStorage:
    def __init__(self, root: str):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        path = (self.root / _check_key(key)).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError("storage key escapes the storage root")
        return path

    def put(self, key: str, data: bytes, content_type: str) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def get(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)

    def ping(self) -> bool:
        return self.root.is_dir()


class S3Storage:
    def __init__(self, settings: Settings):
        import boto3
        from botocore.config import Config

        self.bucket = settings.s3_bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url or None,
            aws_access_key_id=settings.s3_access_key or None,
            aws_secret_access_key=settings.s3_secret_key or None,
            region_name=settings.s3_region,
            # Self-hosted S3 services usually need path-style URLs (no bucket subdomains).
            config=Config(s3={"addressing_style": "path"}) if settings.s3_endpoint_url else None,
        )

    def put(self, key: str, data: bytes, content_type: str) -> None:
        self.client.put_object(
            Bucket=self.bucket,
            Key=_check_key(key),
            Body=data,
            ContentType=content_type,
        )

    def ensure_bucket(self) -> None:
        """Create the bucket on first start if the S3 service doesn't have it yet."""
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except Exception:
            self.client.create_bucket(Bucket=self.bucket)

    def get(self, key: str) -> bytes:
        return self.client.get_object(Bucket=self.bucket, Key=_check_key(key))["Body"].read()

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=_check_key(key))

    def ping(self) -> bool:
        try:
            self.client.head_bucket(Bucket=self.bucket)
            return True
        except Exception:
            return False


def make_storage(settings: Settings) -> ObjectStorage:
    if settings.storage_backend == "s3":
        return S3Storage(settings)
    return LocalStorage(settings.storage_local_path)
