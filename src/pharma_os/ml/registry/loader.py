"""Local artifact-driven model loader for Phase 7 inference workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from pharma_os.core.settings import Settings
from pharma_os.ml.registry.contracts import LoadedModelBundle, ModelProvenance
from pharma_os.pipelines.common.io import read_dataset


class LocalModelRegistry:
    """Load trained artifacts from filesystem-backed Phase 6 outputs."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def resolve_training_run_id(self, *, use_case: str, training_run_id: str | None = None) -> str:
        """Resolve explicit training run id or pick latest available run for a use case."""
        if training_run_id:
            return training_run_id

        use_case_dir = Path(self.settings.phase6_reports_path) / use_case
        if not use_case_dir.exists():
            raise FileNotFoundError(f"No training report directory found for use case '{use_case}': {use_case_dir}")

        candidates = [item for item in use_case_dir.iterdir() if item.is_dir()]
        if not candidates:
            raise FileNotFoundError(f"No training runs found for use case '{use_case}'")

        latest = max(candidates, key=lambda item: item.stat().st_mtime)
        return latest.name

    def load_bundle(
        self,
        *,
        use_case: str,
        training_run_id: str | None = None,
    ) -> LoadedModelBundle:
        """Load model/config bundle for a use case with full provenance metadata."""
        effective_run_id = self.resolve_training_run_id(use_case=use_case, training_run_id=training_run_id)
        metadata = self._read_training_metadata(use_case=use_case, training_run_id=effective_run_id)

        if use_case in {"eligibility", "safety"}:
            return self._load_classification_bundle(
                use_case=use_case,
                training_run_id=effective_run_id,
                metadata=metadata,
            )

        if use_case == "recruitment":
            return self._load_recruitment_bundle(
                training_run_id=effective_run_id,
                metadata=metadata,
            )

        raise ValueError(f"Unsupported use case for registry loading: {use_case}")

    def _load_classification_bundle(
        self,
        *,
        use_case: str,
        training_run_id: str,
        metadata: dict[str, Any],
    ) -> LoadedModelBundle:
        model_artifact_path = Path(str(metadata["model_artifact_path"]))
        if not model_artifact_path.exists():
            raise FileNotFoundError(f"Model artifact missing: {model_artifact_path}")

        model = joblib.load(model_artifact_path)

        feature_manifest_path = Path(str(metadata["feature_manifest_path"]))
        feature_columns = self._read_feature_columns(feature_manifest_path)

        excluded_columns_path = metadata.get("excluded_columns_path")
        excluded_columns: list[str] = []
        if excluded_columns_path:
            excluded_df = read_dataset(Path(str(excluded_columns_path)))
            excluded_columns = [str(value) for value in excluded_df["column_name"].tolist()]

        target_summary = metadata.get("target_summary", {})
        model_name = str(metadata.get("model_name", model_artifact_path.stem))

        provenance = ModelProvenance(
            use_case=use_case,
            training_run_id=training_run_id,
            model_name=model_name,
            model_version=training_run_id,
            label_source_type=str(target_summary.get("label_source_type", "unknown")),
            target_mode=str(target_summary.get("target_mode", "unknown")),
            weak_supervision=bool(target_summary.get("weak_supervision", False)),
            target_summary=target_summary,
            feature_columns=feature_columns,
            excluded_columns=excluded_columns,
        )

        return LoadedModelBundle(
            use_case=use_case,
            training_run_id=training_run_id,
            artifact_kind="classification_model",
            model=model,
            feature_columns=feature_columns,
            excluded_columns=excluded_columns,
            metadata=metadata,
            provenance=provenance,
        )

    def _load_recruitment_bundle(
        self,
        *,
        training_run_id: str,
        metadata: dict[str, Any],
    ) -> LoadedModelBundle:
        model_artifact_path = Path(str(metadata["ranking_config_path"]))
        if not model_artifact_path.exists():
            raise FileNotFoundError(f"Ranking config artifact missing: {model_artifact_path}")

        ranking_config = self._read_json(model_artifact_path)

        target_summary = metadata.get("target_summary", {})
        feature_manifest_path_raw = metadata.get("feature_manifest_path")
        feature_columns = []
        if feature_manifest_path_raw is not None:
            feature_manifest_path = Path(str(feature_manifest_path_raw))
            feature_columns = self._read_feature_columns(feature_manifest_path)

        provenance = ModelProvenance(
            use_case="recruitment",
            training_run_id=training_run_id,
            model_name="score_based_prioritizer",
            model_version=training_run_id,
            label_source_type=str(target_summary.get("label_source_type", "deterministic_score")),
            target_mode=str(target_summary.get("target_mode", "score_only")),
            weak_supervision=bool(target_summary.get("weak_supervision", False)),
            target_summary=target_summary,
            feature_columns=feature_columns,
            excluded_columns=[],
        )

        return LoadedModelBundle(
            use_case="recruitment",
            training_run_id=training_run_id,
            artifact_kind="score_config",
            model=ranking_config,
            feature_columns=feature_columns,
            excluded_columns=[],
            metadata=metadata,
            provenance=provenance,
        )

    def _read_training_metadata(self, *, use_case: str, training_run_id: str) -> dict[str, Any]:
        metadata_path = Path(self.settings.phase6_reports_path) / use_case / training_run_id / "training_metadata.json"
        if not metadata_path.exists():
            raise FileNotFoundError(f"Training metadata not found: {metadata_path}")
        return self._read_json(metadata_path)

    def _read_feature_columns(self, path: Path) -> list[str]:
        if not path.exists():
            return []
        frame = pd.read_csv(path)
        if "feature_name" not in frame.columns:
            return []
        return [str(value) for value in frame["feature_name"].tolist()]

    def _read_json(self, path: Path) -> dict[str, Any]:
        import json

        return json.loads(path.read_text(encoding="utf-8"))
