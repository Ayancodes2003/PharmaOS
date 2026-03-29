"""CLI entrypoint for Phase 10 BI export generation."""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import UTC, datetime

from pharma_os.analytics.exports import BIExportRunner, ExportFormat
from pharma_os.core.settings import get_settings
from pharma_os.db.mongo import close_mongo, get_mongo_database, initialize_mongo
from pharma_os.db.postgres import close_postgres, get_session_factory, initialize_postgres
from pharma_os.observability.logging import configure_logging, get_logger

logger = get_logger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate Phase 10 BI export datasets and manifests",
    )
    parser.add_argument("--phase5-run-id", help="Phase 5 source run id to export (defaults to latest)")
    parser.add_argument("--export-run-id", help="Explicit export run id (defaults to current UTC timestamp)")
    parser.add_argument(
        "--include-parquet",
        action="store_true",
        help="Also emit parquet files in addition to CSV",
    )
    return parser


async def _run() -> int:
    parser = build_parser()
    args = parser.parse_args()

    settings = get_settings()
    configure_logging(settings)

    initialize_postgres(settings)
    await initialize_mongo(settings)

    session_factory = get_session_factory()
    session = session_factory()

    try:
        formats = (ExportFormat.CSV, ExportFormat.PARQUET) if args.include_parquet else (ExportFormat.CSV,)
        export_run_id = args.export_run_id or datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")

        runner = BIExportRunner(settings=settings)
        result = await runner.run(
            session=session,
            mongo_db=get_mongo_database(),
            phase5_run_id=args.phase5_run_id,
            export_run_id=export_run_id,
            formats=formats,
        )

        logger.info("phase 10 export generation complete", extra=result)
        return 0

    except Exception as exc:
        logger.exception("phase 10 export generation failed", exc_info=exc)
        return 1

    finally:
        session.close()
        await close_mongo()
        close_postgres()


def main() -> int:
    return asyncio.run(_run())


if __name__ == "__main__":
    sys.exit(main())
