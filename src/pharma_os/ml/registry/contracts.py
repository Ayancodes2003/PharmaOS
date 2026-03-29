"""Model artifact registry contracts for Phase 7 inference services."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ModelProvenance:
    """Traceable model provenance metadata for inference and audit workflows."""

    use_case: str
    training_run_id: str
    model_name: str
    model_version: str
    label_source_type: str
    target_mode: str
    weak_supervision: bool
    target_summary: dict[str, Any]
    feature_columns: list[str]
    excluded_columns: list[str]


@dataclass(slots=True)
class LoadedModelBundle:
    """In-memory model/config object and metadata loaded from local artifacts."""

    use_case: str
    training_run_id: str
    artifact_kind: str
    model: Any
    feature_columns: list[str]
    excluded_columns: list[str]
    metadata: dict[str, Any]
    provenance: ModelProvenance
