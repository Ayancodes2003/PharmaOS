"""Prediction inference API routes."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from pharma_os.api.dependencies import (
    get_eligibility_prediction_service,
    get_postgres_session_dependency,
    get_recruitment_ranking_service,
    get_safety_prediction_service,
)
from pharma_os.api.schemas.responses import PaginatedPayload, PaginationMeta, SuccessResponse
from pharma_os.core.exceptions import ValidationError
from pharma_os.db.repositories import RecruitmentRepository
from pharma_os.ml.inference.contracts import (
    EligibilityInferenceRequest,
    EligibilityInferenceResult,
    RecruitmentInferenceRequest,
    RecruitmentInferenceResult,
    RecruitmentRankingItem,
    SafetyInferenceRequest,
    SafetyInferenceResult,
)
from pharma_os.services.prediction_services import (
    EligibilityPredictionService,
    RecruitmentRankingService,
    SafetyPredictionService,
)
from sqlalchemy.orm import Session

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.post(
    "/eligibility",
    response_model=SuccessResponse[EligibilityInferenceResult],
    status_code=status.HTTP_200_OK,
)
def run_eligibility_prediction(
    request: EligibilityInferenceRequest,
    training_run_id: str | None = Query(default=None),
    service: EligibilityPredictionService = Depends(get_eligibility_prediction_service),
) -> SuccessResponse[EligibilityInferenceResult]:
    """Run trial eligibility inference for one patient-trial context."""
    try:
        result = service.predict(request=request, training_run_id=training_run_id)
        return SuccessResponse(message="eligibility prediction generated", data=result)
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


@router.post(
    "/safety",
    response_model=SuccessResponse[SafetyInferenceResult],
    status_code=status.HTTP_200_OK,
)
def run_safety_prediction(
    request: SafetyInferenceRequest,
    training_run_id: str | None = Query(default=None),
    service: SafetyPredictionService = Depends(get_safety_prediction_service),
) -> SuccessResponse[SafetyInferenceResult]:
    """Run safety risk inference for one patient-drug context."""
    try:
        result = service.predict(request=request, training_run_id=training_run_id)
        return SuccessResponse(message="safety prediction generated", data=result)
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


@router.post(
    "/recruitment",
    response_model=SuccessResponse[RecruitmentInferenceResult],
    status_code=status.HTTP_200_OK,
)
def run_recruitment_ranking(
    request: RecruitmentInferenceRequest,
    training_run_id: str | None = Query(default=None),
    service: RecruitmentRankingService = Depends(get_recruitment_ranking_service),
) -> SuccessResponse[RecruitmentInferenceResult]:
    """Run score-based recruitment ranking for trial candidates."""
    try:
        result = service.rank(request=request, training_run_id=training_run_id)
        return SuccessResponse(message="recruitment ranking generated", data=result)
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


@router.get(
    "/recruitment/{trial_id}/latest",
    response_model=SuccessResponse[PaginatedPayload[RecruitmentRankingItem]],
    status_code=status.HTTP_200_OK,
)
def get_latest_recruitment_ranking(
    trial_id: UUID,
    top_n: int = Query(default=20, ge=1, le=200),
    session: Session = Depends(get_postgres_session_dependency),
) -> SuccessResponse[PaginatedPayload[RecruitmentRankingItem]]:
    """Get latest persisted recruitment ranking output for a trial."""
    repo = RecruitmentRepository(session)
    latest_run_id = repo.latest_run_id_for_trial(trial_id)
    if latest_run_id is None:
        payload = PaginatedPayload[RecruitmentRankingItem](
            items=[],
            pagination=PaginationMeta(limit=top_n, offset=0, count=0),
        )
        return SuccessResponse(message="no recruitment ranking found", data=payload)

    rows = repo.top_candidates_for_trial_run(trial_id, latest_run_id, top_n=top_n)
    items = [
        RecruitmentRankingItem(
            patient_external_id=row.patient.external_patient_id,
            ranking_score=float(row.ranking_score),
            urgency_score=float(row.urgency_score),
            fit_score=float(row.fit_score),
            exclusion_risk_score=float(row.exclusion_risk_score),
            rank_position=row.rank_position,
            persisted_ranking_id=row.id,
        )
        for row in rows
    ]

    payload = PaginatedPayload[RecruitmentRankingItem](
        items=items,
        pagination=PaginationMeta(limit=top_n, offset=0, count=len(items)),
    )
    return SuccessResponse(message="latest recruitment ranking retrieved", data=payload)
