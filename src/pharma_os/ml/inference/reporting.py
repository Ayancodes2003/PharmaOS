"""Inference result reporting utilities for Phase 7 operational traceability."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel

from pharma_os.core.settings import Settings
from pharma_os.pipelines.common.io import ensure_directory, write_json


def persist_inference_summary(
    *,
    settings: Settings,
    use_case: str,
    payload: BaseModel,
    trace_id: str | None,
) -> Path:
    """Persist inference output summary for operations and audit workflows."""
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    suffix = trace_id or "no-trace"
    output_dir = ensure_directory(Path(settings.phase7_reports_path) / use_case)
    path = output_dir / f"inference_{ts}_{suffix}.json"
    write_json(payload.model_dump(mode="json"), path)
    return path
