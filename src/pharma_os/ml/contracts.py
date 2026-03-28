"""Core contracts for Phase 6 training and evaluation orchestration."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(slots=True)
class TargetPreparationResult:
    """Result of explicit target loading or conservative derivation."""

    target_name: str
    target_mode: str
    y: list[int] | list[float]
    dropped_feature_columns: list[str]
    positive_ratio: float
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ModelEvaluation:
    """Normalized model evaluation payload."""

    model_name: str
    split: str
    metrics: dict[str, float]
    confusion_matrix: dict[str, int]


@dataclass(slots=True)
class TrainingArtifactSet:
    """Paths and metadata for all generated artifacts of a training run."""

    model_artifact_path: str
    metrics_json_path: str
    metrics_csv_path: str
    confusion_matrix_path: str
    feature_manifest_path: str
    metadata_path: str


@dataclass(slots=True)
class UseCaseTrainingResult:
    """Single use case training result summary."""

    use_case: str
    training_run_id: str
    feature_run_id: str
    trained: bool
    selected_model: str
    target_mode: str
    row_count: int
    artifacts: TrainingArtifactSet | None
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class TrainingRunSummary:
    """Top-level summary across all use cases."""

    training_run_id: str
    feature_run_id: str
    started_at: datetime
    finished_at: datetime
    results: list[UseCaseTrainingResult]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["started_at"] = self.started_at.astimezone(UTC).isoformat()
        payload["finished_at"] = self.finished_at.astimezone(UTC).isoformat()
        return payload
