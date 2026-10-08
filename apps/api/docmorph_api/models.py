"""Persistence model.

Every row that holds customer data carries ``tenant_id`` and every query is
scoped by it (see ``tenancy.py``). Personal Studio users get a personal tenant,
Creator Cloud teams and Enterprise orgs get their own; storage never needs a
redesign to add multi-user features.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from docmorph_api.db import Base, JSONType


def _now() -> datetime:
    return datetime.now(UTC)


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    edition: Mapped[str] = mapped_column(String(32), default="personal")  # personal|creator|enterprise
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class DocumentRecord(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(500))
    source_format: Mapped[str] = mapped_column(String(16))
    filename: Mapped[str] = mapped_column(String(255))
    size_bytes: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))
    storage_key: Mapped[str] = mapped_column(String(512))
    current_version: Mapped[int] = mapped_column(Integer, default=1)
    design_cursor: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    versions: Mapped[list[DocumentVersion]] = relationship(
        back_populates="document", cascade="all, delete-orphan", order_by="DocumentVersion.version"
    )
    designs: Mapped[list[DesignVersionRecord]] = relationship(
        back_populates="document", cascade="all, delete-orphan", order_by="DesignVersionRecord.version"
    )


class DocumentVersion(Base):
    """Immutable snapshot of the canonical document (content)."""

    __tablename__ = "document_versions"
    __table_args__ = (UniqueConstraint("document_id", "version"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    version: Mapped[int] = mapped_column(Integer)
    schema_version: Mapped[str] = mapped_column(String(8))
    content: Mapped[dict] = mapped_column(JSONType)
    content_fingerprint: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    document: Mapped[DocumentRecord] = relationship(back_populates="versions")


class DesignVersionRecord(Base):
    """Immutable snapshot of the presentation settings; undo/redo moves a cursor."""

    __tablename__ = "design_versions"
    __table_args__ = (UniqueConstraint("document_id", "version"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    version: Mapped[int] = mapped_column(Integer)
    design: Mapped[dict] = mapped_column(JSONType)
    origin: Mapped[str] = mapped_column(String(16))  # template|manual|ai|restore
    summary: Mapped[str] = mapped_column(String(500), default="")
    patch: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    document: Mapped[DocumentRecord] = relationship(back_populates="designs")
