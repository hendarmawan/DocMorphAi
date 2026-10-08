from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import JSON, create_engine, event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

JSONType = JSON().with_variant(JSONB(), "postgresql")


class Base(DeclarativeBase):
    pass


def make_engine(url: str) -> Engine:
    kwargs: dict = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
        path = url.removeprefix("sqlite:///")
        if path in ("", ":memory:"):
            kwargs["poolclass"] = StaticPool  # one shared in-memory database
        else:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(url, **kwargs)
    if url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def _fk_on(dbapi_conn, _):  # pragma: no cover - trivial
            dbapi_conn.execute("PRAGMA foreign_keys=ON")

    return engine


class Database:
    def __init__(self, url: str):
        self.engine = make_engine(url)
        self.sessions = sessionmaker(self.engine, expire_on_commit=False)

    def create_all(self) -> None:
        from docmorph_api import models  # noqa: F401  (register tables)

        Base.metadata.create_all(self.engine)

    def session(self) -> Iterator[Session]:
        with self.sessions() as s:
            yield s
