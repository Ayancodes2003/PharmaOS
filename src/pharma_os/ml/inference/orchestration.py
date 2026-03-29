"""Inference orchestration helpers for single and multi-use-case execution."""

from __future__ import annotations

from sqlalchemy.orm import Session

from pharma_os.core.settings import Settings
from pharma_os.ml.inference.contracts import (
    EligibilityInferenceRequest,
    MultiUseCaseInferenceSummary,
    RecruitmentInferenceRequest,
    SafetyInferenceRequest,
)
from pharma_os.ml.registry import LocalModelRegistry
from pharma_os.services.prediction_services import (
    EligibilityPredictionService,
    RecruitmentRankingService,
    SafetyPredictionService,
)


def run_eligibility_inference(
    *,
    session: Session,
    settings: Settings,
    request: EligibilityInferenceRequest,
    training_run_id: str | None = None,
):
    registry = LocalModelRegistry(settings)
    service = EligibilityPredictionService(session=session, settings=settings, registry=registry)
    return service.predict(request=request, training_run_id=training_run_id)


def run_safety_inference(
    *,
    session: Session,
    settings: Settings,
    request: SafetyInferenceRequest,
    training_run_id: str | None = None,
):
    registry = LocalModelRegistry(settings)
    service = SafetyPredictionService(session=session, settings=settings, registry=registry)
    return service.predict(request=request, training_run_id=training_run_id)


def run_recruitment_inference(
    *,
    session: Session,
    settings: Settings,
    request: RecruitmentInferenceRequest,
    training_run_id: str | None = None,
):
    registry = LocalModelRegistry(settings)
    service = RecruitmentRankingService(session=session, settings=settings, registry=registry)
    return service.rank(request=request, training_run_id=training_run_id)


def run_all_inference_use_cases(
    *,
    session: Session,
    settings: Settings,
    eligibility_request: EligibilityInferenceRequest | None = None,
    safety_request: SafetyInferenceRequest | None = None,
    recruitment_request: RecruitmentInferenceRequest | None = None,
    training_run_id: str | None = None,
    trace_id: str | None = None,
) -> MultiUseCaseInferenceSummary:
    """Run available use-case inference requests and return one summary payload."""
    summary = MultiUseCaseInferenceSummary(trace_id=trace_id)

    if eligibility_request is not None:
        summary.eligibility = run_eligibility_inference(
            session=session,
            settings=settings,
            request=eligibility_request,
            training_run_id=training_run_id,
        )

    if safety_request is not None:
        summary.safety = run_safety_inference(
            session=session,
            settings=settings,
            request=safety_request,
            training_run_id=training_run_id,
        )

    if recruitment_request is not None:
        summary.recruitment = run_recruitment_inference(
            session=session,
            settings=settings,
            request=recruitment_request,
            training_run_id=training_run_id,
        )

    return summary
