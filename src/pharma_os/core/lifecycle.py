"""Application lifecycle management for startup and shutdown orchestration."""

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

from pharma_os.core.exceptions import DatabaseConnectionError
from pharma_os.core.settings import get_settings
from pharma_os.db.mongo import close_mongo, initialize_mongo, test_mongo_connection
from pharma_os.db.postgres import close_postgres, initialize_postgres, test_postgres_connection
from pharma_os.observability.logging import configure_logging, get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def application_lifespan(_: FastAPI) -> Any:
    """Initialize and teardown shared runtime resources."""
    settings = get_settings()
    configure_logging(settings)

    logger.info(
        "application startup initiated",
        extra={
            "app": settings.app_name,
            "version": settings.app_version,
            "environment": settings.app_env,
        },
    )

    initialize_postgres(settings)
    await initialize_mongo(settings)

    pg_ok, pg_detail = test_postgres_connection()
    mongo_ok, mongo_detail = await test_mongo_connection()

    logger.info(
        "database connectivity check completed",
        extra={
            "postgresql": {"status": pg_ok, "detail": pg_detail},
            "mongodb": {"status": mongo_ok, "detail": mongo_detail},
        },
    )

    if not pg_ok or not mongo_ok:
        raise DatabaseConnectionError(
            "Startup dependency check failed",
            details={
                "postgresql": pg_detail,
                "mongodb": mongo_detail,
            },
        )

    logger.info("application startup completed")

    try:
        yield
    finally:
        logger.info("application shutdown initiated")
        await close_mongo()
        close_postgres()
        logger.info("application shutdown completed")
