"""Base SQLAlchemy repository abstractions."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from pharma_os.core.exceptions import NotFoundError, RepositoryError
from pharma_os.db.models.base import DomainBase

ModelT = TypeVar("ModelT", bound=DomainBase)


class BaseRepository(Generic[ModelT]):
    """Generic repository with CRUD and query helpers for SQLAlchemy models."""

    model: type[ModelT]
    immutable_fields: frozenset[str] = frozenset({"id", "created_at"})

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, entity_id: UUID) -> ModelT | None:
        """Fetch entity by primary key."""
        try:
            statement = select(self.model).where(self.model.id == entity_id)
            return self.session.scalar(statement)
        except SQLAlchemyError as exc:
            raise RepositoryError("Failed to fetch entity", details={"reason": str(exc)}) from exc

    def get_or_raise(self, entity_id: UUID) -> ModelT:
        """Fetch entity or raise NotFoundError."""
        item = self.get(entity_id)
        if not item:
            raise NotFoundError(
                f"{self.model.__name__} not found",
                details={"id": str(entity_id)},
            )
        return item

    def list(self, *, limit: int = 100, offset: int = 0) -> list[ModelT]:
        """List entities with pagination."""
        try:
            statement = select(self.model).offset(offset).limit(limit)
            return list(self.session.scalars(statement).all())
        except SQLAlchemyError as exc:
            raise RepositoryError("Failed to list entities", details={"reason": str(exc)}) from exc

    def count(self, statement: Select[Any] | None = None) -> int:
        """Count entities for a statement or the whole model table."""
        try:
            if statement is None:
                statement = select(self.model)
            count_statement = select(func.count()).select_from(statement.subquery())
            return int(self.session.scalar(count_statement) or 0)
        except SQLAlchemyError as exc:
            raise RepositoryError("Failed to count entities", details={"reason": str(exc)}) from exc

    def create(self, **kwargs: Any) -> ModelT:
        """Create and persist a new entity."""
        try:
            instance = self.model(**kwargs)
            self.session.add(instance)
            self.session.flush()
            self.session.refresh(instance)
            return instance
        except SQLAlchemyError as exc:
            raise RepositoryError("Failed to create entity", details={"reason": str(exc)}) from exc

    def bulk_create(self, entries: Sequence[dict[str, Any]]) -> list[ModelT]:
        """Create multiple entities in one unit of work."""
        try:
            instances = [self.model(**payload) for payload in entries]
            self.session.add_all(instances)
            self.session.flush()
            for instance in instances:
                self.session.refresh(instance)
            return instances
        except SQLAlchemyError as exc:
            raise RepositoryError("Failed to bulk create entities", details={"reason": str(exc)}) from exc

    def update(self, instance: ModelT, **kwargs: Any) -> ModelT:
        """Update mutable fields on an existing entity instance."""
        try:
            for key, value in kwargs.items():
                if key in self.immutable_fields:
                    continue
                if hasattr(instance, key):
                    setattr(instance, key, value)
            self.session.flush()
            self.session.refresh(instance)
            return instance
        except SQLAlchemyError as exc:
            raise RepositoryError("Failed to update entity", details={"reason": str(exc)}) from exc

    def delete(self, instance: ModelT) -> None:
        """Delete a persisted entity instance."""
        try:
            self.session.delete(instance)
            self.session.flush()
        except SQLAlchemyError as exc:
            raise RepositoryError("Failed to delete entity", details={"reason": str(exc)}) from exc
