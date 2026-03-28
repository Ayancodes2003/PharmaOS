"""Top-level orchestration runners for structured ingestion pipelines."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from pharma_os.core.settings import Settings, get_settings
from pharma_os.observability.logging import get_logger
from pharma_os.pipelines.common.contracts import (
    DomainPipelineResult,
    FileFormat,
    PipelineDomain,
    PipelineRunSummary,
)
from pharma_os.pipelines.common.io import write_json
from pharma_os.pipelines.orchestration.config import SUPPORTED_STRUCTURED_DOMAINS
from pharma_os.pipelines.orchestration.domain_runner import DomainPipelineRunner

logger = get_logger(__name__)


def run_domain_pipeline(
    *,
    domain: PipelineDomain,
    source_path: Path,
    run_id: str | None = None,
    file_format: FileFormat | None = None,
    settings: Settings | None = None,
) -> DomainPipelineResult:
    """Run pipeline for a single domain."""
    runtime_settings = settings or get_settings()
    runner = DomainPipelineRunner(runtime_settings)
    effective_run_id = run_id or datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return runner.run(domain=domain, source_path=source_path, run_id=effective_run_id, file_format=file_format)


def run_all_domain_pipelines(
    *,
    source_paths: dict[PipelineDomain, Path],
    run_id: str | None = None,
    fail_fast: bool = False,
    settings: Settings | None = None,
) -> PipelineRunSummary:
    """Run all supported structured pipelines with consolidated run summary."""
    runtime_settings = settings or get_settings()
    runner = DomainPipelineRunner(runtime_settings)
    effective_run_id = run_id or datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")

    started_at = datetime.now(UTC)
    results: list[DomainPipelineResult] = []

    logger.info(
        "pipeline batch start",
        extra={"run_id": effective_run_id, "domains": [domain.value for domain in source_paths.keys()]},
    )

    for domain in SUPPORTED_STRUCTURED_DOMAINS:
        if domain not in source_paths:
            logger.warning("domain source path missing", extra={"domain": domain.value, "run_id": effective_run_id})
            continue

        try:
            result = runner.run(
                domain=domain,
                source_path=source_paths[domain],
                run_id=effective_run_id,
                file_format=None,
            )
            results.append(result)
        except Exception as exc:
            logger.exception(
                "pipeline domain failure",
                extra={"domain": domain.value, "run_id": effective_run_id, "error": str(exc)},
            )
            failed_result = DomainPipelineResult(
                domain=domain,
                run_id=effective_run_id,
                started_at=started_at,
                finished_at=datetime.now(UTC),
                success=False,
                validation=_empty_validation(domain),
                artifacts=[],
                message=str(exc),
            )
            results.append(failed_result)
            if fail_fast:
                break

    summary = PipelineRunSummary(
        run_id=effective_run_id,
        started_at=started_at,
        finished_at=datetime.now(UTC),
        results=results,
    )

    summary_path = Path(runtime_settings.reports_path) / "pipeline_runs" / f"{effective_run_id}_summary.json"
    write_json(summary.to_dict(), summary_path)

    logger.info(
        "pipeline batch complete",
        extra={
            "run_id": effective_run_id,
            "succeeded_domains": summary.succeeded_domains,
            "failed_domains": summary.failed_domains,
            "summary_path": str(summary_path),
        },
    )

    return summary


def _empty_validation(domain: PipelineDomain) -> object:
    from pharma_os.pipelines.common.contracts import ValidationReport

    return ValidationReport(
        domain=domain,
        passed=False,
        row_count=0,
        required_columns=[],
        missing_columns=[],
        unexpected_columns=[],
        duplicate_count=0,
        issues=[],
    )
