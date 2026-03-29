"""Trial API routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from pharma_os.api.dependencies import get_trial_repository
from pharma_os.api.schemas.responses import PaginatedPayload, PaginationMeta, SuccessResponse
from pharma_os.core.exceptions import NotFoundError
from pharma_os.db.repositories import TrialRepository
from pharma_os.db.schemas.trial import TrialReadDTO

router = APIRouter(prefix="/trials", tags=["trials"])


@router.get("/{trial_id}", response_model=SuccessResponse[TrialReadDTO], status_code=status.HTTP_200_OK)
def get_trial(
    trial_id: str,
    repo: TrialRepository = Depends(get_trial_repository),
) -> SuccessResponse[TrialReadDTO]:
    """Retrieve a single trial by UUID or trial code."""
    trial = None
    try:
        trial = repo.get(UUID(trial_id))
    except ValueError:
        trial = repo.get_by_trial_code(trial_id)

    if trial is None:
        raise NotFoundError("Trial not found", details={"trial_id": trial_id})

    return SuccessResponse(message="trial retrieved", data=TrialReadDTO.model_validate(trial))


@router.get("", response_model=SuccessResponse[PaginatedPayload[TrialReadDTO]], status_code=status.HTTP_200_OK)
def list_trials(
    indication: str | None = Query(default=None, description="Filter by trial indication (contains match)"),
    recruiting_only: bool = Query(default=False, description="Only recruiting trials"),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    repo: TrialRepository = Depends(get_trial_repository),
) -> SuccessResponse[PaginatedPayload[TrialReadDTO]]:
    """List trials with optional indication and recruiting filters."""
    if indication:
        items = repo.list_by_indication(indication, limit=limit, offset=offset)
    elif recruiting_only:
        items = repo.list_recruiting(limit=limit, offset=offset)
    else:
        items = repo.list(limit=limit, offset=offset)

    dto_items = [TrialReadDTO.model_validate(item) for item in items]
    payload = PaginatedPayload[TrialReadDTO](
        items=dto_items,
        pagination=PaginationMeta(limit=limit, offset=offset, count=len(dto_items)),
    )
    return SuccessResponse(message="trials listed", data=payload)
