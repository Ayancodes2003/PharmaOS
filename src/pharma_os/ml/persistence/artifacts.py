"""Model, metrics, and metadata artifact writers for Phase 6."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.pipeline import Pipeline

from pharma_os.core.settings import Settings
from pharma_os.ml.contracts import TrainingArtifactSet
from pharma_os.pipelines.common.io import ensure_directory, write_json


def persist_classification_training_artifacts(
    *,
    use_case: str,
    training_run_id: str,
    model_name: str,
    model: Pipeline,
    evaluations: dict[str, Any],
    feature_columns: list[str],
    target_summary: dict[str, Any],
    extra_metadata: dict[str, Any],
    feature_importance_df: pd.DataFrame,
    settings: Settings,
) -> TrainingArtifactSet:
    """Persist full artifact set for a trained classification use case."""
    model_dir = ensure_directory(Path(settings.model_registry_path) / use_case / training_run_id)
    metrics_dir = ensure_directory(Path(settings.metrics_path) / use_case / training_run_id)
    reports_dir = ensure_directory(Path(settings.phase6_reports_path) / use_case / training_run_id)

    model_artifact_path = model_dir / f"{model_name}.joblib"
    joblib.dump(model, model_artifact_path)

    metrics_json_path = write_json(
        {
            "use_case": use_case,
            "training_run_id": training_run_id,
            "model_name": model_name,
            "target_summary": target_summary,
            "evaluations": evaluations,
        },
        metrics_dir / "metrics.json",
    )

    metrics_rows: list[dict[str, Any]] = []
    confusion_rows: list[dict[str, Any]] = []
    for candidate_name, split_payload in evaluations.items():
        for split_name, payload in split_payload.items():
            metrics = payload.get("metrics", {})
            metrics_row = {"model_name": candidate_name, "split": split_name}
            metrics_row.update({str(key): float(value) for key, value in metrics.items()})
            metrics_rows.append(metrics_row)

            matrix = payload.get("confusion_matrix", {})
            confusion_rows.append(
                {
                    "model_name": candidate_name,
                    "split": split_name,
                    "tn": int(matrix.get("tn", 0)),
                    "fp": int(matrix.get("fp", 0)),
                    "fn": int(matrix.get("fn", 0)),
                    "tp": int(matrix.get("tp", 0)),
                }
            )

    metrics_csv_path = metrics_dir / "metrics.csv"
    pd.DataFrame(metrics_rows).to_csv(metrics_csv_path, index=False)

    confusion_matrix_path = metrics_dir / "confusion_matrix.csv"
    pd.DataFrame(confusion_rows).to_csv(confusion_matrix_path, index=False)

    feature_manifest_path = reports_dir / "feature_manifest.csv"
    pd.DataFrame({"feature_name": feature_columns}).to_csv(feature_manifest_path, index=False)

    importance_path = reports_dir / "feature_importance.csv"
    feature_importance_df.to_csv(importance_path, index=False)

    metadata_path = write_json(
        {
            "use_case": use_case,
            "training_run_id": training_run_id,
            "model_name": model_name,
            "target_summary": target_summary,
            "extra_metadata": extra_metadata,
            "model_artifact_path": str(model_artifact_path),
            "metrics_json_path": str(metrics_json_path),
            "metrics_csv_path": str(metrics_csv_path),
            "confusion_matrix_path": str(confusion_matrix_path),
            "feature_manifest_path": str(feature_manifest_path),
            "feature_importance_path": str(importance_path),
        },
        reports_dir / "training_metadata.json",
    )

    return TrainingArtifactSet(
        model_artifact_path=str(model_artifact_path),
        metrics_json_path=str(metrics_json_path),
        metrics_csv_path=str(metrics_csv_path),
        confusion_matrix_path=str(confusion_matrix_path),
        feature_manifest_path=str(feature_manifest_path),
        metadata_path=str(metadata_path),
    )


def persist_recruitment_ranking_artifacts(
    *,
    training_run_id: str,
    ranking_config: dict[str, Any],
    summary_payload: dict[str, Any],
    settings: Settings,
) -> TrainingArtifactSet:
    """Persist deterministic score-based recruitment ranking artifacts."""
    use_case = "recruitment"
    model_dir = ensure_directory(Path(settings.model_registry_path) / use_case / training_run_id)
    metrics_dir = ensure_directory(Path(settings.metrics_path) / use_case / training_run_id)
    reports_dir = ensure_directory(Path(settings.phase6_reports_path) / use_case / training_run_id)

    model_artifact_path = write_json(ranking_config, model_dir / "ranking_config.json")
    metrics_json_path = write_json(summary_payload, metrics_dir / "metrics.json")

    metrics_csv_path = metrics_dir / "metrics.csv"
    pd.DataFrame([summary_payload]).to_csv(metrics_csv_path, index=False)

    confusion_matrix_path = metrics_dir / "confusion_matrix.csv"
    pd.DataFrame([{"tn": 0, "fp": 0, "fn": 0, "tp": 0}]).to_csv(confusion_matrix_path, index=False)

    feature_manifest_path = reports_dir / "feature_manifest.csv"
    pd.DataFrame(
        {"feature_name": ["condition_fit", "urgency_proxy", "enrollment_ready_flag", "exclusion_risk_signal"]}
    ).to_csv(feature_manifest_path, index=False)

    metadata_path = write_json(
        {
            "use_case": use_case,
            "training_run_id": training_run_id,
            "mode": "score_based",
            "ranking_config_path": str(model_artifact_path),
            "metrics_json_path": str(metrics_json_path),
            "metrics_csv_path": str(metrics_csv_path),
        },
        reports_dir / "training_metadata.json",
    )

    return TrainingArtifactSet(
        model_artifact_path=str(model_artifact_path),
        metrics_json_path=str(metrics_json_path),
        metrics_csv_path=str(metrics_csv_path),
        confusion_matrix_path=str(confusion_matrix_path),
        feature_manifest_path=str(feature_manifest_path),
        metadata_path=str(metadata_path),
    )
