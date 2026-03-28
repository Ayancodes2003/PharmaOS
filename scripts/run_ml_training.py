"""CLI entrypoint for PHARMA-OS Phase 6 ML training workflows."""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime

from pharma_os.core.settings import get_settings
from pharma_os.ml.orchestration import train_all_use_cases, train_single_use_case
from pharma_os.observability.logging import configure_logging, get_logger

logger = get_logger(__name__)


USE_CASE_CHOICES = ["eligibility", "safety", "recruitment", "all"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Train PHARMA-OS Phase 6 models from Phase 5 feature artifacts"
    )
    parser.add_argument(
        "--feature-run-id",
        required=True,
        help="Feature artifact run id generated in Phase 5",
    )
    parser.add_argument(
        "--training-run-id",
        help="Optional training run id (default: current UTC timestamp)",
    )
    parser.add_argument(
        "--use-case",
        choices=USE_CASE_CHOICES,
        default="all",
        help="Train a single use case or all use cases",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    settings = get_settings()
    configure_logging(settings)

    training_run_id = args.training_run_id or datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")

    try:
        if args.use_case == "all":
            summary = train_all_use_cases(
                feature_run_id=args.feature_run_id,
                training_run_id=training_run_id,
                settings=settings,
            )
            failed = [result.use_case for result in summary.results if not result.trained and result.selected_model == "none"]
            logger.info(
                "phase 6 all-use-case training complete",
                extra={
                    "training_run_id": training_run_id,
                    "feature_run_id": args.feature_run_id,
                    "result_count": len(summary.results),
                    "failed_use_cases": failed,
                },
            )
            return 0

        result = train_single_use_case(
            use_case=args.use_case,
            feature_run_id=args.feature_run_id,
            training_run_id=training_run_id,
            settings=settings,
        )
        logger.info(
            "phase 6 single-use-case training complete",
            extra={
                "training_run_id": training_run_id,
                "feature_run_id": args.feature_run_id,
                "use_case": args.use_case,
                "selected_model": result.selected_model,
            },
        )
        return 0
    except Exception as exc:
        logger.exception("phase 6 training failed", extra={"error": str(exc)})
        return 1


if __name__ == "__main__":
    sys.exit(main())
