"""CLI entrypoint for Phase 5 feature engineering and analytics mart generation."""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime

from pharma_os.core.settings import get_settings
from pharma_os.features.engineering.runner import run_phase5_feature_analytics
from pharma_os.observability.logging import configure_logging, get_logger

logger = get_logger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate PHARMA-OS Phase 5 features and analytics marts from feature-ready datasets"
    )
    parser.add_argument(
        "--run-id",
        help="Pipeline run id from Phase 4 artifacts (default: current UTC timestamp format)",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    settings = get_settings()
    configure_logging(settings)

    run_id = args.run_id or datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")

    try:
        result = run_phase5_feature_analytics(run_id=run_id, settings=settings)
    except FileNotFoundError as exc:
        logger.error(
            "phase 5 source artifact missing",
            extra={"run_id": run_id, "error": str(exc)},
        )
        return 1

    logger.info(
        "phase 5 generation completed",
        extra={
            "run_id": result["run_id"],
            "manifest_path": result["manifest_path"],
        },
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
