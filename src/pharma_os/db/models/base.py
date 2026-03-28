"""Declarative base and shared ORM mixins for PHARMA-OS domain models."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, MetaData, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Root declarative base with Alembic-friendly naming conventions."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class UUIDPrimaryKeyMixin:
    """Shared UUID primary key field for aggregate roots and events."""

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )


class TimestampMixin:
    """Shared audit timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class MetadataMixin:
    """Optional flexible metadata payload for traceability/extensibility."""

    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )


class DomainBase(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Canonical base for PHARMA-OS PostgreSQL entities."""

    __abstract__ = True

    def to_dict(self) -> dict[str, Any]:
        """Serialize mapped columns to a dictionary for internal diagnostics."""
        values: dict[str, Any] = {}
        for column in self.__table__.columns:
            key = column.name
            value = getattr(self, key)
            if isinstance(value, datetime):
                value = value.astimezone(UTC).isoformat()
            values[key] = value
        return values
