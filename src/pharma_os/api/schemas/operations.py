"""Operational and artifact status API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from typing import Literal

from pydantic import BaseModel


class ModelArtifactStatus(BaseModel):
    """Current artifact availability for one model use case."""

    use_case: str
    available: bool
    latest_training_run_id: str | None = None
    detail: str | None = None


class PipelineRunSummaryItem(BaseModel):
    """Minimal view of a persisted pipeline run summary artifact."""

    run_id: str
    file_name: str
    updated_at: datetime
    path: str


class ServiceMetadataPayload(BaseModel):
    """Basic service metadata payload for ops endpoints."""

    app_name: str
    version: str
    environment: str
    api_prefix: str
    llm_provider: str | None
    llm_model: str | None
    llm_stub_mode: bool


class ExportManifestSummaryItem(BaseModel):
    """Minimal Phase 10 export manifest summary entry."""

    export_run_id: str
    file_name: str
    updated_at: datetime
    path: str


class ExportManifestPayload(BaseModel):
    """Phase 10 export manifest payload."""

    manifest: dict[str, Any]
