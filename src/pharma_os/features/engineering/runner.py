"""Phase 5 orchestration for feature engineering and analytics marts."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from pharma_os.analytics.exports.metadata import summarize_collection
from pharma_os.analytics.exports.writers import write_named_dataset, write_run_manifest
from pharma_os.analytics.marts import (
    build_adverse_event_monitoring_mart,
    build_model_monitoring_support_mart,
    build_patient_screening_funnel_mart,
    build_recruitment_kpis_mart,
    build_trial_eligibility_mart,
)
from pharma_os.core.settings import Settings
from pharma_os.features.engineering.common import read_stage_dataset
from pharma_os.features.engineering.eligibility import build_eligibility_features
from pharma_os.features.engineering.recruitment import build_recruitment_features
from pharma_os.features.engineering.safety import build_safety_features
from pharma_os.observability.logging import get_logger
from pharma_os.pipelines.common.io import ensure_directory, write_json

logger = get_logger(__name__)


def run_phase5_feature_analytics(*, run_id: str, settings: Settings) -> dict[str, Any]:
    """Generate feature datasets, analytics marts, and metadata for a pipeline run."""
    started_at = datetime.now(UTC)

    patients_df = read_stage_dataset(settings.data_feature_ready_path, "patients", run_id)
    trials_df = read_stage_dataset(settings.data_feature_ready_path, "trials", run_id)
    adverse_events_df = read_stage_dataset(settings.data_feature_ready_path, "adverse_events", run_id)
    drug_exposures_df = read_stage_dataset(settings.data_feature_ready_path, "drug_exposures", run_id)

    logger.info("phase 5: feature engineering start", extra={"run_id": run_id})

    eligibility_features = build_eligibility_features(
        patients_df=patients_df,
        trials_df=trials_df,
        adverse_events_df=adverse_events_df,
        drug_exposures_df=drug_exposures_df,
    )
    safety_features = build_safety_features(
        patients_df=patients_df,
        adverse_events_df=adverse_events_df,
        drug_exposures_df=drug_exposures_df,
    )
    recruitment_features = build_recruitment_features(
        patients_df=patients_df,
        trials_df=trials_df,
        adverse_events_df=adverse_events_df,
        drug_exposures_df=drug_exposures_df,
    )

    logger.info(
        "phase 5: feature engineering complete",
        extra={
            "run_id": run_id,
            "eligibility_rows": len(eligibility_features.index),
            "safety_rows": len(safety_features.index),
            "recruitment_rows": len(recruitment_features.index),
        },
    )

    patient_screening_funnel_mart = build_patient_screening_funnel_mart(
        eligibility_features=eligibility_features,
    )
    trial_eligibility_mart = build_trial_eligibility_mart(
        eligibility_features=eligibility_features,
    )
    adverse_event_monitoring_mart = build_adverse_event_monitoring_mart(
        adverse_events_df=adverse_events_df,
        safety_features=safety_features,
    )
    recruitment_kpis_mart = build_recruitment_kpis_mart(
        recruitment_features=recruitment_features,
    )
    model_monitoring_support_mart = build_model_monitoring_support_mart(
        eligibility_features=eligibility_features,
        safety_features=safety_features,
        recruitment_features=recruitment_features,
    )

    feature_outputs = {
        "eligibility_features": eligibility_features,
        "safety_features": safety_features,
        "recruitment_features": recruitment_features,
    }
    analytics_outputs = {
        "patient_screening_funnel": patient_screening_funnel_mart,
        "trial_eligibility": trial_eligibility_mart,
        "adverse_event_monitoring": adverse_event_monitoring_mart,
        "recruitment_kpis": recruitment_kpis_mart,
        "model_monitoring_support": model_monitoring_support_mart,
    }

    feature_output_paths = _write_output_group(
        output_root=settings.data_feature_store_path,
        run_id=run_id,
        outputs=feature_outputs,
    )
    mart_output_paths = _write_output_group(
        output_root=settings.data_analytics_marts_path,
        run_id=run_id,
        outputs=analytics_outputs,
    )

    reports_dir = Path(settings.phase5_reports_path)
    ensure_directory(reports_dir)

    feature_summary = summarize_collection(feature_outputs)
    analytics_summary = summarize_collection(analytics_outputs)

    feature_summary_path = write_json(
        feature_summary,
        reports_dir / f"feature_summary_{run_id}.json",
    )
    analytics_summary_path = write_json(
        analytics_summary,
        reports_dir / f"analytics_summary_{run_id}.json",
    )

    finished_at = datetime.now(UTC)
    manifest = {
        "run_id": run_id,
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "source_stage": "feature_ready",
        "feature_outputs": {name: str(path) for name, path in feature_output_paths.items()},
        "analytics_outputs": {name: str(path) for name, path in mart_output_paths.items()},
        "feature_summary_path": str(feature_summary_path),
        "analytics_summary_path": str(analytics_summary_path),
        "feature_row_counts": {
            name: int(len(df.index)) for name, df in feature_outputs.items()
        },
        "analytics_row_counts": {
            name: int(len(df.index)) for name, df in analytics_outputs.items()
        },
    }

    manifest_path = write_run_manifest(
        output_dir=reports_dir,
        run_id=run_id,
        payload=manifest,
    )

    logger.info("phase 5: generation complete", extra={"run_id": run_id, "manifest": str(manifest_path)})
    return {
        "run_id": run_id,
        "manifest_path": str(manifest_path),
        "feature_output_paths": {name: str(path) for name, path in feature_output_paths.items()},
        "analytics_output_paths": {name: str(path) for name, path in mart_output_paths.items()},
    }


def _write_output_group(
    *,
    output_root: Path,
    run_id: str,
    outputs: dict[str, pd.DataFrame],
) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for name, frame in outputs.items():
        paths[name] = write_named_dataset(
            output_dir=output_root,
            name=name,
            run_id=run_id,
            df=frame,
        )
    return paths
