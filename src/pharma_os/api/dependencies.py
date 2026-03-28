"""Shared FastAPI dependency helpers."""

from collections.abc import Generator

from motor.motor_asyncio import AsyncIOMotorDatabase
from sqlalchemy.orm import Session

from pharma_os.core.settings import Settings, get_settings
from pharma_os.db.mongo import get_mongo_database
from pharma_os.db.postgres import get_db_session


def get_app_settings() -> Settings:
    """Dependency provider for typed runtime settings."""
    return get_settings()


def get_postgres_session_dependency() -> Generator[Session, None, None]:
    """Dependency provider for PostgreSQL session."""
    yield from get_db_session()


def get_mongo_database_dependency() -> AsyncIOMotorDatabase:
    """Dependency provider for MongoDB database handle."""
    return get_mongo_database()
