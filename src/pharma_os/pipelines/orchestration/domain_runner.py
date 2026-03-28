"""Domain-level orchestration for ingestion, validation, preprocessing, and stage outputs."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from pharma_os.core.settings import Settings
from pharma_os.features.handoff import build_feature_ready_dataset
from pharma_os.observability.logging import get_logger
from pharma_os.pipelines.common.contracts import (
    DomainPipelineResult,
    FileFormat,
    PipelineArtifact,
    PipelineDomain,
    ValidationReport,
)
from pharma_os.pipelines.common.io import write_json, write_stage_dataset
from pharma_os.pipelines.common.quality import dataset_quality_summary
from pharma_os.pipelines.ingestion.readers import ingest_domain_dataset
from pharma_os.pipelines.orchestration.config import DOMAIN_PIPELINE_CONFIGS
from pharma_os.pipelines.validation import validate_and_enforce

logger = get_logger(__name__)


class DomainPipelineRunner:
    """Single-domain deterministic pipeline runner."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def run(
        self,
        *,
        domain: PipelineDomain,
        source_path: Path,
        run_id: str,
        file_format: FileFormat | None = None,
    ) -> DomainPipelineResult:
        """Run full pipeline stages for a structured domain dataset."""
        started_at = datetime.now(UTC)

        if domain not in DOMAIN_PIPELINE_CONFIGS:
            raise NotImplementedError(
                f"Structured pipeline not implemented for domain '{domain.value}'. "
                "Unstructured ingestion extension points are reserved for a later phase."
            )

        config = DOMAIN_PIPELINE_CONFIGS[domain]
        logger.info("pipeline domain start", extra={"domain": domain.value, "run_id": run_id})

        raw_df = ingest_domain_dataset(domain, source_path, file_format=file_format)
        validation_report = validate_and_enforce(raw_df, config.validation_spec)

        processed_df = config.preprocessor(raw_df)
        validate_and_enforce(processed_df, config.validation_spec)

        load_ready_df = self._build_load_ready(domain, processed_df)
        feature_ready_df = build_feature_ready_dataset(domain, load_ready_df)
        finished_at = datetime.now(UTC)

        artifacts = self._persist_stage_artifacts(
            domain=domain,
            run_id=run_id,
            raw_df=raw_df,
            processed_df=processed_df,
            load_ready_df=load_ready_df,
            feature_ready_df=feature_ready_df,
            validation_report=validation_report,
            started_at=started_at,
            finished_at=finished_at,
        )

        logger.info(
            "pipeline domain success",
            extra={"domain": domain.value, "run_id": run_id, "rows": len(load_ready_df.index)},
        )

        return DomainPipelineResult(
            domain=domain,
            run_id=run_id,
            started_at=started_at,
            finished_at=finished_at,
            success=True,
            validation=validation_report,
            artifacts=artifacts,
            message="Pipeline completed successfully",
        )

    def _build_load_ready(self, domain: PipelineDomain, processed_df: pd.DataFrame) -> pd.DataFrame:
        """Build load-ready dataset with stable ordering and domain-specific contracts."""
        load_ready_df = processed_df.copy()

        if domain == PipelineDomain.PATIENTS:
            load_ready_df = load_ready_df.sort_values(by=["external_patient_id"], kind="stable")
        elif domain == PipelineDomain.TRIALS:
            load_ready_df = load_ready_df.sort_values(by=["trial_code"], kind="stable")
        elif domain == PipelineDomain.ADVERSE_EVENTS:
            load_ready_df = load_ready_df.sort_values(
                by=["patient_external_id", "event_date"],
                kind="stable",
            )
        elif domain == PipelineDomain.DRUG_EXPOSURES:
            load_ready_df = load_ready_df.sort_values(
                by=["patient_external_id", "drug_name", "start_date"],
                kind="stable",
            )

        return load_ready_df.reset_index(drop=True)

    def _persist_stage_artifacts(
        self,
        *,
        domain: PipelineDomain,
        run_id: str,
        raw_df: pd.DataFrame,
        processed_df: pd.DataFrame,
        load_ready_df: pd.DataFrame,
        feature_ready_df: pd.DataFrame,
        validation_report: ValidationReport,
        started_at: datetime,
        finished_at: datetime,
    ) -> list[PipelineArtifact]:
        """Persist stage outputs and metadata summary artifacts."""
        artifacts: list[PipelineArtifact] = []

        stage_payloads = {
            "raw": (self.settings.data_raw_path, raw_df),
            "processed": (self.settings.data_processed_path, processed_df),
            "load_ready": (self.settings.data_load_ready_path, load_ready_df),
            "feature_ready": (self.settings.data_feature_ready_path, feature_ready_df),
        }

        for stage_name, (base_path, stage_df) in stage_payloads.items():
            stage_path = Path(base_path) / domain.value / f"{run_id}.csv"
            write_stage_dataset(stage_df, stage_path)
            artifacts.append(
                PipelineArtifact(
                    stage=stage_name,
                    domain=domain,
                    path=stage_path,
                    row_count=len(stage_df.index),
                )
            )

        metadata_path = Path(self.settings.reports_path) / "pipeline_runs" / f"{run_id}_{domain.value}.json"
        write_json(
            {
                "domain": domain.value,
                "run_id": run_id,
                "started_at": started_at.isoformat(),
                "finished_at": finished_at.isoformat(),
                "validation": validation_report.to_dict(),
                "quality": {
                    "raw": dataset_quality_summary(raw_df),
                    "processed": dataset_quality_summary(processed_df),
                    "load_ready": dataset_quality_summary(load_ready_df),
                    "feature_ready": dataset_quality_summary(feature_ready_df),
                },
            },
            metadata_path,
        )

        artifacts.append(
            PipelineArtifact(
                stage="metadata",
                domain=domain,
                path=metadata_path,
                row_count=1,
            )
        )

        return artifacts
