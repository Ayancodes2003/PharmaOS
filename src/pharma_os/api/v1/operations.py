"""Operational metadata and artifact status routes."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, Query, status

from pharma_os.api.dependencies import get_app_settings
from pharma_os.api.schemas.operations import (
    ExportManifestPayload,
    ExportManifestSummaryItem,
    ModelArtifactStatus,
    PipelineRunSummaryItem,
    ServiceMetadataPayload,
)
from pharma_os.api.schemas.responses import PaginatedPayload, PaginationMeta, SuccessResponse
from pharma_os.core.settings import Settings
from pharma_os.ml.registry import LocalModelRegistry

router = APIRouter(prefix="/operations", tags=["operations"])


@router.get(
    "/service-metadata",
    response_model=SuccessResponse[ServiceMetadataPayload],
    status_code=status.HTTP_200_OK,
)
def get_service_metadata(
    settings: Settings = Depends(get_app_settings),
) -> SuccessResponse[ServiceMetadataPayload]:
    """Return basic service metadata useful for operational inspection."""
    provider = settings.llm_provider
    payload = ServiceMetadataPayload(
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
        api_prefix=settings.api_v1_prefix,
        llm_provider=provider,
        llm_model=settings.llm_model,
        llm_stub_mode=not bool(provider and settings.llm_api_key),
    )
    return SuccessResponse(message="service metadata retrieved", data=payload)


@router.get(
    "/model-artifacts",
    response_model=SuccessResponse[list[ModelArtifactStatus]],
    status_code=status.HTTP_200_OK,
)
def list_model_artifact_status(
    settings: Settings = Depends(get_app_settings),
) -> SuccessResponse[list[ModelArtifactStatus]]:
    """Return availability and latest run metadata for model artifacts."""
    registry = LocalModelRegistry(settings)
    statuses: list[ModelArtifactStatus] = []

    for use_case in ("eligibility", "safety", "recruitment"):
        try:
            run_id = registry.resolve_training_run_id(use_case=use_case)
            statuses.append(
                ModelArtifactStatus(
                    use_case=use_case,
                    available=True,
                    latest_training_run_id=run_id,
                )
            )
        except Exception as exc:
            statuses.append(
                ModelArtifactStatus(
                    use_case=use_case,
                    available=False,
                    detail=str(exc),
                )
            )

    return SuccessResponse(message="model artifact status listed", data=statuses)


@router.get(
    "/pipeline-runs",
    response_model=SuccessResponse[PaginatedPayload[PipelineRunSummaryItem]],
    status_code=status.HTTP_200_OK,
)
def list_pipeline_runs(
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    settings: Settings = Depends(get_app_settings),
) -> SuccessResponse[PaginatedPayload[PipelineRunSummaryItem]]:
    """List persisted pipeline run summary artifacts from reports storage."""
    run_dir = Path(settings.reports_path) / "pipeline_runs"
    if not run_dir.exists():
        payload = PaginatedPayload[PipelineRunSummaryItem](
            items=[],
            pagination=PaginationMeta(limit=limit, offset=offset, count=0),
        )
        return SuccessResponse(message="no pipeline runs found", data=payload)

    all_files = sorted(
        [item for item in run_dir.glob("*_summary.json") if item.is_file()],
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )

    selected = all_files[offset : offset + limit]
    items: list[PipelineRunSummaryItem] = []

    for path in selected:
        run_id = path.stem.replace("_summary", "")
        try:
            content = json.loads(path.read_text(encoding="utf-8"))
            run_id = content.get("run_id", run_id)
        except Exception:
            pass

        items.append(
            PipelineRunSummaryItem(
                run_id=run_id,
                file_name=path.name,
                updated_at=datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc),
                path=str(path),
            )
        )

    payload = PaginatedPayload[PipelineRunSummaryItem](
        items=items,
        pagination=PaginationMeta(limit=limit, offset=offset, count=len(items)),
    )
    return SuccessResponse(message="pipeline run summaries listed", data=payload)


@router.get(
    "/exports/manifests",
    response_model=SuccessResponse[PaginatedPayload[ExportManifestSummaryItem]],
    status_code=status.HTTP_200_OK,
)
def list_export_manifests(
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    settings: Settings = Depends(get_app_settings),
) -> SuccessResponse[PaginatedPayload[ExportManifestSummaryItem]]:
    """List persisted Phase 10 export manifest artifacts."""
    reports_dir = Path(settings.artifact_root) / "reports" / "phase10"
    if not reports_dir.exists():
        payload = PaginatedPayload[ExportManifestSummaryItem](
            items=[],
            pagination=PaginationMeta(limit=limit, offset=offset, count=0),
        )
        return SuccessResponse(message="no export manifests found", data=payload)

    all_files = sorted(
        [item for item in reports_dir.glob("phase10_export_manifest_*.json") if item.is_file()],
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    selected = all_files[offset : offset + limit]
    items: list[ExportManifestSummaryItem] = []

    for path in selected:
        run_id = path.stem.replace("phase10_export_manifest_", "")
        items.append(
            ExportManifestSummaryItem(
                export_run_id=run_id,
                file_name=path.name,
                updated_at=datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc),
                path=str(path),
            )
        )

    payload = PaginatedPayload[ExportManifestSummaryItem](
        items=items,
        pagination=PaginationMeta(limit=limit, offset=offset, count=len(items)),
    )
    return SuccessResponse(message="export manifests listed", data=payload)


@router.get(
    "/exports/manifests/{export_run_id}",
    response_model=SuccessResponse[ExportManifestPayload],
    status_code=status.HTTP_200_OK,
)
def get_export_manifest(
    export_run_id: str,
    settings: Settings = Depends(get_app_settings),
) -> SuccessResponse[ExportManifestPayload]:
    """Return one Phase 10 export manifest by export run id."""
    path = Path(settings.artifact_root) / "reports" / "phase10" / f"phase10_export_manifest_{export_run_id}.json"
    if not path.exists():
        payload = ExportManifestPayload(manifest={})
        return SuccessResponse(message="export manifest not found", data=payload)

    payload_raw = json.loads(path.read_text(encoding="utf-8"))
    payload = ExportManifestPayload(manifest=payload_raw)
    return SuccessResponse(message="export manifest retrieved", data=payload)
