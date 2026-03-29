"""Patient API routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from pharma_os.api.dependencies import get_patient_repository
from pharma_os.api.schemas.responses import PaginatedPayload, PaginationMeta, SuccessResponse
from pharma_os.core.exceptions import NotFoundError
from pharma_os.db.repositories import PatientRepository
from pharma_os.db.schemas.patient import PatientReadDTO

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("/{patient_id}", response_model=SuccessResponse[PatientReadDTO], status_code=status.HTTP_200_OK)
def get_patient(
    patient_id: str,
    repo: PatientRepository = Depends(get_patient_repository),
) -> SuccessResponse[PatientReadDTO]:
    """Retrieve a single patient by UUID or external patient ID."""
    patient = None
    try:
        patient = repo.get(UUID(patient_id))
    except ValueError:
        patient = repo.get_by_external_patient_id(patient_id)

    if patient is None:
        raise NotFoundError("Patient not found", details={"patient_id": patient_id})

    return SuccessResponse(message="patient retrieved", data=PatientReadDTO.model_validate(patient))


@router.get("", response_model=SuccessResponse[PaginatedPayload[PatientReadDTO]], status_code=status.HTTP_200_OK)
def list_patients(
    condition: str | None = Query(default=None, description="Filter by primary condition (contains match)"),
    active_only: bool = Query(default=False, description="Only active patients"),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    repo: PatientRepository = Depends(get_patient_repository),
) -> SuccessResponse[PaginatedPayload[PatientReadDTO]]:
    """List patients with optional condition and active status filters."""
    if condition:
        items = repo.list_by_condition(condition, limit=limit, offset=offset)
    elif active_only:
        items = repo.list_active(limit=limit, offset=offset)
    else:
        items = repo.list(limit=limit, offset=offset)

    dto_items = [PatientReadDTO.model_validate(item) for item in items]
    payload = PaginatedPayload[PatientReadDTO](
        items=dto_items,
        pagination=PaginationMeta(limit=limit, offset=offset, count=len(dto_items)),
    )
    return SuccessResponse(message="patients listed", data=payload)
