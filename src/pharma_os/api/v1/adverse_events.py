"""Adverse event API routes."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from pharma_os.api.dependencies import get_adverse_event_repository
from pharma_os.api.schemas.responses import PaginatedPayload, PaginationMeta, SuccessResponse
from pharma_os.core.exceptions import NotFoundError
from pharma_os.db.models.enums import AdverseEventSeverity
from pharma_os.db.repositories import AdverseEventRepository
from pharma_os.db.schemas.adverse_event import AdverseEventReadDTO

router = APIRouter(prefix="/adverse-events", tags=["adverse-events"])


@router.get("/{event_id}", response_model=SuccessResponse[AdverseEventReadDTO], status_code=status.HTTP_200_OK)
def get_adverse_event(
    event_id: UUID,
    repo: AdverseEventRepository = Depends(get_adverse_event_repository),
) -> SuccessResponse[AdverseEventReadDTO]:
    """Retrieve an adverse event by ID."""
    event = repo.get(event_id)
    if event is None:
        raise NotFoundError("Adverse event not found", details={"event_id": str(event_id)})

    return SuccessResponse(message="adverse event retrieved", data=AdverseEventReadDTO.model_validate(event))


@router.get("", response_model=SuccessResponse[PaginatedPayload[AdverseEventReadDTO]], status_code=status.HTTP_200_OK)
def list_adverse_events(
    patient_id: UUID | None = Query(default=None),
    serious_only: bool = Query(default=False),
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    severity: AdverseEventSeverity | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    repo: AdverseEventRepository = Depends(get_adverse_event_repository),
) -> SuccessResponse[PaginatedPayload[AdverseEventReadDTO]]:
    """List adverse events with patient and time-window filters."""
    if patient_id is not None:
        items = repo.list_by_patient(patient_id, limit=limit, offset=offset)
    elif serious_only:
        items = repo.list_serious(limit=limit, offset=offset)
    elif start is not None and end is not None:
        items = repo.list_by_date_window(start=start, end=end, severity=severity, limit=limit, offset=offset)
    else:
        items = repo.list(limit=limit, offset=offset)

    dto_items = [AdverseEventReadDTO.model_validate(item) for item in items]
    payload = PaginatedPayload[AdverseEventReadDTO](
        items=dto_items,
        pagination=PaginationMeta(limit=limit, offset=offset, count=len(dto_items)),
    )
    return SuccessResponse(message="adverse events listed", data=payload)
