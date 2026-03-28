"""PostgreSQL engine and session lifecycle management."""

from collections.abc import Generator

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from pharma_os.core.exceptions import ConfigurationError, DatabaseConnectionError
from pharma_os.core.settings import Settings
from pharma_os.observability.logging import get_logger

logger = get_logger(__name__)

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def initialize_postgres(settings: Settings) -> None:
    """Initialize SQLAlchemy engine and session factory."""
    global _engine, _session_factory

    db_url = settings.resolved_postgres_url
    if not db_url:
        raise ConfigurationError("PostgreSQL URL is not configured")

    logger.info("initializing postgresql engine")
    try:
        _engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            future=True,
        )
        _session_factory = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)
    except SQLAlchemyError as exc:
        raise DatabaseConnectionError(
            "Failed to initialize PostgreSQL engine",
            details={"reason": str(exc)},
        ) from exc


def close_postgres() -> None:
    """Dispose SQLAlchemy engine resources."""
    global _engine, _session_factory

    if _engine is not None:
        logger.info("disposing postgresql engine")
        _engine.dispose()

    _engine = None
    _session_factory = None


def get_postgres_engine() -> Engine:
    """Return initialized SQLAlchemy engine."""
    if _engine is None:
        raise DatabaseConnectionError("PostgreSQL engine not initialized")
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    """Return initialized SQLAlchemy sessionmaker."""
    if _session_factory is None:
        raise DatabaseConnectionError("PostgreSQL session factory not initialized")
    return _session_factory


def get_db_session() -> Generator[Session, None, None]:
    """FastAPI dependency provider for SQLAlchemy sessions."""
    session_factory = get_session_factory()
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def test_postgres_connection() -> tuple[bool, str]:
    """Run a lightweight connection check against PostgreSQL."""
    try:
        engine = get_postgres_engine()
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True, "PostgreSQL connection successful"
    except SQLAlchemyError as exc:
        return False, f"PostgreSQL connection failed: {exc}"
    except Exception as exc:
        return False, f"PostgreSQL connection unavailable: {exc}"
