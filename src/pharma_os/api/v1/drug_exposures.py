"""Drug exposure API routes."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from pharma_os.api.dependencies import get_drug_exposure_repository
from pharma_os.api.schemas.responses import PaginatedPayload, PaginationMeta, SuccessResponse
from pharma_os.core.exceptions import NotFoundError
from pharma_os.db.repositories import DrugExposureRepository
from pharma_os.db.schemas.drug_exposure import DrugExposureReadDTO

router = APIRouter(prefix="/drug-exposures", tags=["drug-exposures"])


@router.get("/{exposure_id}", response_model=SuccessResponse[DrugExposureReadDTO], status_code=status.HTTP_200_OK)
def get_drug_exposure(
    exposure_id: UUID,
    repo: DrugExposureRepository = Depends(get_drug_exposure_repository),
) -> SuccessResponse[DrugExposureReadDTO]:
    """Retrieve a drug exposure by ID."""
    exposure = repo.get(exposure_id)
    if exposure is None:
        raise NotFoundError("Drug exposure not found", details={"exposure_id": str(exposure_id)})

    return SuccessResponse(message="drug exposure retrieved", data=DrugExposureReadDTO.model_validate(exposure))


@router.get("", response_model=SuccessResponse[PaginatedPayload[DrugExposureReadDTO]], status_code=status.HTTP_200_OK)
def list_drug_exposures(
    patient_id: UUID | None = Query(default=None),
    drug_name: str | None = Query(default=None),
    active_only: bool = Query(default=False),
    as_of: date | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    repo: DrugExposureRepository = Depends(get_drug_exposure_repository),
) -> SuccessResponse[PaginatedPayload[DrugExposureReadDTO]]:
    """List drug exposures with patient, active status, and drug-name filters."""
    if patient_id is not None and active_only:
        items = repo.list_active_by_patient(patient_id, as_of=as_of)
    elif patient_id is not None:
        items = repo.list_by_patient(patient_id, limit=limit, offset=offset)
    elif drug_name:
        items = repo.list_by_drug_name(drug_name, limit=limit, offset=offset)
    else:
        items = repo.list(limit=limit, offset=offset)

    dto_items = [DrugExposureReadDTO.model_validate(item) for item in items]
    payload = PaginatedPayload[DrugExposureReadDTO](
        items=dto_items,
        pagination=PaginationMeta(limit=limit, offset=offset, count=len(dto_items)),
    )
    return SuccessResponse(message="drug exposures listed", data=payload)
