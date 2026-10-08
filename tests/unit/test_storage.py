from __future__ import annotations

from types import SimpleNamespace

from docmorph_api.storage import S3Storage


class _StubS3:
    def __init__(self, exists: bool):
        self.exists = exists
        self.created: list[str] = []

    def head_bucket(self, Bucket: str):  # noqa: N803 (boto3 casing)
        if not self.exists:
            raise RuntimeError("404")

    def create_bucket(self, Bucket: str):  # noqa: N803
        self.created.append(Bucket)


def _storage(client) -> S3Storage:
    storage = S3Storage.__new__(S3Storage)
    storage.bucket = "docmorph"
    storage.client = client
    return storage


def test_missing_bucket_is_created_on_start():
    client = _StubS3(exists=False)
    _storage(client).ensure_bucket()
    assert client.created == ["docmorph"]


def test_existing_bucket_is_left_alone():
    client = _StubS3(exists=True)
    _storage(client).ensure_bucket()
    assert client.created == []
    assert _storage(SimpleNamespace(head_bucket=lambda Bucket: None)).ping()
