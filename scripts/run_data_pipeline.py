"""CLI entrypoint for PHARMA-OS structured data pipelines."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pharma_os.core.settings import Settings, get_settings
from pharma_os.observability.logging import configure_logging, get_logger
from pharma_os.pipelines.common.contracts import PipelineDomain
from pharma_os.pipelines.orchestration.config import SUPPORTED_STRUCTURED_DOMAINS
from pharma_os.pipelines.orchestration.runner import run_all_domain_pipelines, run_domain_pipeline

logger = get_logger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run PHARMA-OS data ingestion/preprocessing pipelines")
    parser.add_argument(
        "--domain",
        choices=[domain.value for domain in SUPPORTED_STRUCTURED_DOMAINS],
        help="Run a single domain pipeline",
    )
    parser.add_argument("--source", help="Source file path for single-domain run")
    parser.add_argument("--run-id", help="Optional deterministic run identifier")
    parser.add_argument("--fail-fast", action="store_true", help="Stop on first failed domain")

    parser.add_argument("--patients-source", help="Source file for patients domain")
    parser.add_argument("--trials-source", help="Source file for trials domain")
    parser.add_argument("--adverse-events-source", help="Source file for adverse events domain")
    parser.add_argument("--drug-exposures-source", help="Source file for drug exposures domain")

    return parser


def _default_source_for_domain(domain: PipelineDomain, settings: Settings) -> Path:
    """Resolve configured default source path for a domain."""
    if domain == PipelineDomain.PATIENTS and settings.patients_source_path is not None:
        return settings.patients_source_path
    if domain == PipelineDomain.TRIALS and settings.trials_source_path is not None:
        return settings.trials_source_path
    if domain == PipelineDomain.ADVERSE_EVENTS and settings.adverse_events_source_path is not None:
        return settings.adverse_events_source_path
    if domain == PipelineDomain.DRUG_EXPOSURES and settings.drug_exposures_source_path is not None:
        return settings.drug_exposures_source_path
    return settings.data_source_path / f"{domain.value}.csv"


def parse_source_map(args: argparse.Namespace, settings: Settings) -> dict[PipelineDomain, Path]:
    source_map: dict[PipelineDomain, Path] = {}

    if args.patients_source:
        source_map[PipelineDomain.PATIENTS] = Path(args.patients_source)
    else:
        source_map[PipelineDomain.PATIENTS] = _default_source_for_domain(PipelineDomain.PATIENTS, settings)

    if args.trials_source:
        source_map[PipelineDomain.TRIALS] = Path(args.trials_source)
    else:
        source_map[PipelineDomain.TRIALS] = _default_source_for_domain(PipelineDomain.TRIALS, settings)

    if args.adverse_events_source:
        source_map[PipelineDomain.ADVERSE_EVENTS] = Path(args.adverse_events_source)
    else:
        source_map[PipelineDomain.ADVERSE_EVENTS] = _default_source_for_domain(
            PipelineDomain.ADVERSE_EVENTS,
            settings,
        )

    if args.drug_exposures_source:
        source_map[PipelineDomain.DRUG_EXPOSURES] = Path(args.drug_exposures_source)
    else:
        source_map[PipelineDomain.DRUG_EXPOSURES] = _default_source_for_domain(
            PipelineDomain.DRUG_EXPOSURES,
            settings,
        )

    return source_map


def _validate_source_exists(path: Path, domain: PipelineDomain) -> None:
    """Raise a clear error when a configured source file does not exist."""
    if path.exists():
        return
    raise FileNotFoundError(
        f"Source file not found for domain '{domain.value}': {path}. "
        "Provide --source/--<domain>-source or configure *_SOURCE_PATH in .env."
    )


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    settings = get_settings()
    configure_logging(settings)

    if args.domain:
        domain = PipelineDomain(args.domain)
        source_path = Path(args.source) if args.source else _default_source_for_domain(domain, settings)
        _validate_source_exists(source_path, domain)
        result = run_domain_pipeline(
            domain=domain,
            source_path=source_path,
            run_id=args.run_id,
            settings=settings,
        )
        logger.info("domain pipeline completed", extra={"domain": domain.value, "success": result.success})
        return 0 if result.success else 1

    source_map = parse_source_map(args, settings)
    for domain, path in source_map.items():
        _validate_source_exists(path, domain)

    summary = run_all_domain_pipelines(
        source_paths=source_map,
        run_id=args.run_id,
        fail_fast=args.fail_fast,
        settings=settings,
    )
    return 0 if summary.failed_domains == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
