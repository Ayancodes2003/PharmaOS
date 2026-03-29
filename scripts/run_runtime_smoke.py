"""Runtime smoke checks for PHARMA-OS startup dependencies and API probes."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

import httpx

from pharma_os.core.settings import get_settings
from pharma_os.db.mongo import close_mongo, initialize_mongo, test_mongo_connection
from pharma_os.db.postgres import close_postgres, initialize_postgres, test_postgres_connection
from pharma_os.observability.logging import configure_logging, get_logger
from pharma_os.pipelines.common.io import ensure_directory

logger = get_logger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run PHARMA-OS runtime smoke checks")
    parser.add_argument(
        "--check-api",
        action="store_true",
        help="Also probe API health/readiness endpoints",
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL used when --check-api is enabled",
    )
    return parser


def _ensure_runtime_directories() -> list[str]:
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
    return [str(path) for path in paths]


async def _probe_api(base_url: str, api_prefix: str) -> tuple[bool, str]:
    async with httpx.AsyncClient(timeout=5.0) as client:
        health_url = f"{base_url}{api_prefix}/system/health"
        readiness_url = f"{base_url}{api_prefix}/system/readiness"

        health_response = await client.get(health_url)
        if health_response.status_code != 200:
            return False, f"health probe failed: {health_response.status_code}"

        readiness_response = await client.get(readiness_url)
        if readiness_response.status_code not in (200, 503):
            return False, f"readiness probe failed: {readiness_response.status_code}"

    return True, "api probes successful"


async def _run() -> int:
    args = build_parser().parse_args()

    settings = get_settings()
    configure_logging(settings)

    created_paths = _ensure_runtime_directories()
    logger.info("runtime directories ensured", extra={"count": len(created_paths)})

    initialize_postgres(settings)
    await initialize_mongo(settings)

    pg_ok, pg_detail = test_postgres_connection()
    mongo_ok, mongo_detail = await test_mongo_connection()

    logger.info(
        "dependency smoke checks completed",
        extra={
            "postgresql": {"ok": pg_ok, "detail": pg_detail},
            "mongodb": {"ok": mongo_ok, "detail": mongo_detail},
        },
    )

    dependencies_ok = pg_ok and mongo_ok
    api_ok = True

    if args.check_api:
        api_ok, api_detail = await _probe_api(args.base_url, settings.api_v1_prefix)
        logger.info("api smoke check completed", extra={"ok": api_ok, "detail": api_detail})

    await close_mongo()
    close_postgres()

    return 0 if dependencies_ok and api_ok else 1


def main() -> int:
    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.exception("runtime smoke failed", extra={"error": str(exc)})
        return 1


if __name__ == "__main__":
    sys.exit(main())
