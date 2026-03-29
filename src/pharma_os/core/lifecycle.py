"""Application lifecycle management for startup and shutdown orchestration."""

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

from pharma_os.core.exceptions import DatabaseConnectionError
from pharma_os.core.settings import get_settings
from pharma_os.db.mongo import close_mongo, initialize_mongo, test_mongo_connection
from pharma_os.db.postgres import close_postgres, initialize_postgres, test_postgres_connection
from pharma_os.observability.logging import configure_logging, get_logger
from pharma_os.pipelines.common.io import ensure_directory

logger = get_logger(__name__)


def _ensure_runtime_directories() -> None:
    """Create expected runtime directories for data and artifacts."""
    settings = get_settings()
    paths = [
        settings.artifact_root,
        settings.model_registry_path,
        settings.metrics_path,
        settings.reports_path,
        settings.data_raw_path,
        settings.data_processed_path,
        settings.data_load_ready_path,
        settings.data_feature_ready_path,
        settings.data_feature_store_path,
        settings.data_analytics_marts_path,
        settings.phase5_reports_path,
        settings.phase6_reports_path,
        settings.phase7_reports_path,
    ]
    for path in paths:
        ensure_directory(path)


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

    _ensure_runtime_directories()

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
