"""Prediction services for Phase 7 model loading, inference, and persistence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

import numpy as np
from sqlalchemy.orm import Session

from pharma_os.core.settings import Settings
from pharma_os.db.models.enums import ActorType, SafetyRiskClass
from pharma_os.db.repositories import (
    AuditLogRepository,
    EligibilityPredictionRepository,
    RecruitmentRepository,
    SafetyPredictionRepository,
)
from pharma_os.ml.inference.contracts import (
    EligibilityInferenceRequest,
    EligibilityInferenceResult,
    InferenceProvenance,
    RecruitmentInferenceRequest,
    RecruitmentInferenceResult,
    RecruitmentRankingItem,
    SafetyInferenceRequest,
    SafetyInferenceResult,
)
from pharma_os.ml.inference.feature_prep import (
    prepare_eligibility_features_for_inference,
    prepare_recruitment_features_for_inference,
    prepare_safety_features_for_inference,
)
from pharma_os.ml.registry import LocalModelRegistry


@dataclass(slots=True)
class _ServiceDeps:
    eligibility_repo: EligibilityPredictionRepository
    safety_repo: SafetyPredictionRepository
    recruitment_repo: RecruitmentRepository
    audit_repo: AuditLogRepository


class EligibilityPredictionService:
    """Service for model-driven patient-trial eligibility predictions."""

    def __init__(self, *, session: Session, settings: Settings, registry: LocalModelRegistry | None = None) -> None:
        self.session = session
        self.settings = settings
        self.registry = registry or LocalModelRegistry(settings)
        self.deps = _ServiceDeps(
            eligibility_repo=EligibilityPredictionRepository(session),
            safety_repo=SafetyPredictionRepository(session),
            recruitment_repo=RecruitmentRepository(session),
            audit_repo=AuditLogRepository(session),
        )

    def predict(
        self,
        *,
        request: EligibilityInferenceRequest,
        training_run_id: str | None = None,
    ) -> EligibilityInferenceResult:
        bundle = self.registry.load_bundle(use_case="eligibility", training_run_id=training_run_id)
        features, snapshot = prepare_eligibility_features_for_inference(request=request, bundle=bundle)

        proba = _predict_probability(bundle.model, features)
        predicted_eligible = bool(proba >= 0.5)
        confidence = float(max(proba, 1.0 - proba))

        provenance = _to_provenance(bundle)
        persisted_id: UUID | None = None

        if request.persist_prediction:
            if request.patient.id is None or request.trial.id is None:
                raise ValueError("Persistence requested but patient.id or trial.id is missing in request payload")

            created = self.deps.eligibility_repo.create(
                patient_id=request.patient.id,
                trial_id=request.trial.id,
                model_name=provenance.model_name,
                model_version=provenance.model_version,
                predicted_eligible=predicted_eligible,
                eligibility_probability=proba,
                confidence=confidence,
                rationale_summary=_eligibility_rationale(features.iloc[0].to_dict()),
                feature_snapshot={
                    "feature_vector": features.iloc[0].to_dict(),
                    "engineered_snapshot": snapshot,
                    "provenance": provenance.model_dump(),
                },
                inference_timestamp=datetime.now(UTC),
            )
            persisted_id = created.id

            self._write_audit(
                action_type="eligibility_prediction_created",
                entity_type="eligibility_prediction",
                entity_id=str(created.id),
                trace_id=request.trace_id,
                payload_summary="Eligibility inference persisted",
                metadata_json={
                    "patient_id": str(request.patient.id),
                    "trial_id": str(request.trial.id),
                    "predicted_eligible": predicted_eligible,
                    "eligibility_probability": proba,
                    "model_version": provenance.model_version,
                    "training_run_id": provenance.training_run_id,
                },
            )
            self.session.commit()

        return EligibilityInferenceResult(
            patient_external_id=request.patient.external_patient_id,
            trial_code=request.trial.trial_code,
            predicted_eligible=predicted_eligible,
            eligibility_probability=proba,
            confidence=confidence,
            persisted_prediction_id=persisted_id,
            provenance=provenance,
        )

    def _write_audit(
        self,
        *,
        action_type: str,
        entity_type: str,
        entity_id: str | None,
        trace_id: str | None,
        payload_summary: str,
        metadata_json: dict[str, object],
    ) -> None:
        self.deps.audit_repo.create(
            actor_type=ActorType.SERVICE,
            actor_id="phase7.inference.eligibility",
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            payload_summary=payload_summary,
            metadata_json=metadata_json,
            trace_id=trace_id,
            occurred_at=datetime.now(UTC),
        )


class SafetyPredictionService:
    """Service for model-driven patient safety risk predictions."""

    def __init__(self, *, session: Session, settings: Settings, registry: LocalModelRegistry | None = None) -> None:
        self.session = session
        self.settings = settings
        self.registry = registry or LocalModelRegistry(settings)
        self.deps = _ServiceDeps(
            eligibility_repo=EligibilityPredictionRepository(session),
            safety_repo=SafetyPredictionRepository(session),
            recruitment_repo=RecruitmentRepository(session),
            audit_repo=AuditLogRepository(session),
        )

    def predict(
        self,
        *,
        request: SafetyInferenceRequest,
        training_run_id: str | None = None,
    ) -> SafetyInferenceResult:
        bundle = self.registry.load_bundle(use_case="safety", training_run_id=training_run_id)
        features, snapshot = prepare_safety_features_for_inference(request=request, bundle=bundle)

        risk_score = _predict_probability(bundle.model, features)
        risk_class = _risk_class_from_score(risk_score)
        confidence = float(max(risk_score, 1.0 - risk_score))

        provenance = _to_provenance(bundle)
        persisted_id: UUID | None = None

        if request.persist_prediction:
            if request.patient.id is None:
                raise ValueError("Persistence requested but patient.id is missing in request payload")

            created = self.deps.safety_repo.create(
                patient_id=request.patient.id,
                drug_exposure_id=request.drug_exposure_id,
                model_name=provenance.model_name,
                model_version=provenance.model_version,
                risk_class=risk_class,
                risk_score=risk_score,
                confidence=confidence,
                explanation_summary=_safety_explanation(features.iloc[0].to_dict()),
                feature_snapshot={
                    "feature_vector": features.iloc[0].to_dict(),
                    "engineered_snapshot": snapshot,
                    "provenance": provenance.model_dump(),
                },
                inference_timestamp=datetime.now(UTC),
            )
            persisted_id = created.id

            self.deps.audit_repo.create(
                actor_type=ActorType.SERVICE,
                actor_id="phase7.inference.safety",
                action_type="safety_prediction_created",
                entity_type="safety_prediction",
                entity_id=str(created.id),
                payload_summary="Safety inference persisted",
                metadata_json={
                    "patient_id": str(request.patient.id),
                    "drug_name": request.drug_name,
                    "risk_class": risk_class.value,
                    "risk_score": risk_score,
                    "model_version": provenance.model_version,
                    "training_run_id": provenance.training_run_id,
                },
                trace_id=request.trace_id,
                occurred_at=datetime.now(UTC),
            )
            self.session.commit()

        return SafetyInferenceResult(
            patient_external_id=request.patient.external_patient_id,
            drug_name=request.drug_name,
            risk_class=risk_class.value,
            risk_score=risk_score,
            confidence=confidence,
            persisted_prediction_id=persisted_id,
            provenance=provenance,
        )


class RecruitmentRankingService:
    """Service for score-based recruitment ranking inference and optional persistence."""

    def __init__(self, *, session: Session, settings: Settings, registry: LocalModelRegistry | None = None) -> None:
        self.session = session
        self.settings = settings
        self.registry = registry or LocalModelRegistry(settings)
        self.deps = _ServiceDeps(
            eligibility_repo=EligibilityPredictionRepository(session),
            safety_repo=SafetyPredictionRepository(session),
            recruitment_repo=RecruitmentRepository(session),
            audit_repo=AuditLogRepository(session),
        )

    def rank(
        self,
        *,
        request: RecruitmentInferenceRequest,
        training_run_id: str | None = None,
    ) -> RecruitmentInferenceResult:
        bundle = self.registry.load_bundle(use_case="recruitment", training_run_id=training_run_id)
        _, snapshots = prepare_recruitment_features_for_inference(request=request, bundle=bundle)

        ranked_rows = _rank_rows_from_snapshot_rows(snapshots)
        if request.top_k is not None:
            ranked_rows = ranked_rows[: request.top_k]

        ranking_run_id = uuid4() if request.persist_prediction else None
        provenance = _to_provenance(bundle)
        items: list[RecruitmentRankingItem] = []

        for index, row in enumerate(ranked_rows, start=1):
            item = RecruitmentRankingItem(
                patient_external_id=str(row["external_patient_id"]),
                ranking_score=float(row["ranking_score"]),
                urgency_score=float(row["urgency_score"]),
                fit_score=float(row["fit_score"]),
                exclusion_risk_score=float(row["exclusion_risk_score"]),
                rank_position=index,
            )
            items.append(item)

        if request.persist_prediction:
            if request.trial.id is None:
                raise ValueError("Persistence requested but trial.id is missing in request payload")

            by_external_id = {candidate.patient.external_patient_id: candidate.patient for candidate in request.candidates}

            for item in items:
                patient_payload = by_external_id.get(item.patient_external_id)
                if patient_payload is None or patient_payload.id is None:
                    raise ValueError(
                        "Persistence requested but one or more candidate patient ids are missing in request payload"
                    )

                created = self.deps.recruitment_repo.create(
                    patient_id=patient_payload.id,
                    trial_id=request.trial.id,
                    ranking_run_id=ranking_run_id,
                    ranking_score=item.ranking_score,
                    urgency_score=item.urgency_score,
                    fit_score=item.fit_score,
                    exclusion_risk_score=item.exclusion_risk_score,
                    rank_position=item.rank_position,
                    model_version=provenance.model_version,
                    generated_at=datetime.now(UTC),
                )
                item.persisted_ranking_id = created.id

            self.deps.audit_repo.create(
                actor_type=ActorType.SERVICE,
                actor_id="phase7.inference.recruitment",
                action_type="recruitment_ranking_created",
                entity_type="recruitment_ranking_run",
                entity_id=str(ranking_run_id),
                payload_summary="Recruitment ranking inference persisted",
                metadata_json={
                    "trial_id": str(request.trial.id),
                    "trial_code": request.trial.trial_code,
                    "ranking_run_id": str(ranking_run_id),
                    "ranked_candidates": len(items),
                    "model_version": provenance.model_version,
                    "training_run_id": provenance.training_run_id,
                    "score_based_only": True,
                },
                trace_id=request.trace_id,
                occurred_at=datetime.now(UTC),
            )
            self.session.commit()

        return RecruitmentInferenceResult(
            trial_code=request.trial.trial_code,
            ranking_run_id=ranking_run_id,
            items=items,
            provenance=provenance,
        )


def _predict_probability(model: object, features) -> float:
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(features)
        if getattr(proba, "ndim", 0) == 2 and proba.shape[1] >= 2:
            return _clip01(float(proba[0][1]))
    if hasattr(model, "decision_function"):
        value = np.asarray(model.decision_function(features)).ravel()[0]
        probability = 1.0 / (1.0 + float(np.exp(-value)))
        return _clip01(probability)

    prediction = np.asarray(model.predict(features)).ravel()[0]
    return _clip01(float(prediction))


def _to_provenance(bundle) -> InferenceProvenance:
    return InferenceProvenance(
        use_case=bundle.provenance.use_case,
        model_name=bundle.provenance.model_name,
        model_version=bundle.provenance.model_version,
        training_run_id=bundle.provenance.training_run_id,
        label_source_type=bundle.provenance.label_source_type,
        target_mode=bundle.provenance.target_mode,
        weak_supervision=bundle.provenance.weak_supervision,
        feature_schema_columns=bundle.provenance.feature_columns,
    )


def _risk_class_from_score(score: float) -> SafetyRiskClass:
    if score < 0.30:
        return SafetyRiskClass.LOW
    if score < 0.60:
        return SafetyRiskClass.MODERATE
    if score < 0.80:
        return SafetyRiskClass.HIGH
    return SafetyRiskClass.CRITICAL


def _clip01(value: float) -> float:
    return float(max(0.0, min(1.0, value)))


def _eligibility_rationale(feature_row: dict[str, object]) -> str:
    fit_component = float(feature_row.get("trial_fit_score_component", 0) or 0)
    serious_events = int(feature_row.get("serious_event_count", 0) or 0)
    return (
        f"Fit component={fit_component:.2f}; serious_event_count={serious_events}; "
        "eligibility decision is model-assisted using current trial and patient context."
    )


def _safety_explanation(feature_row: dict[str, object]) -> str:
    risk_component = float(feature_row.get("safety_risk_component", 0) or 0)
    severe_count = int(feature_row.get("severe_event_count", 0) or 0)
    return (
        f"Safety risk component={risk_component:.2f}; severe_event_count={severe_count}; "
        "risk class derived from model probability thresholds."
    )


def _rank_rows_from_snapshot_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    if not rows:
        return []

    frame = np.array([float(row.get("ranking_score_component", 0) or 0) for row in rows], dtype=float)
    min_score = float(frame.min())
    max_score = float(frame.max())
    spread = max_score - min_score

    normalized: list[dict[str, object]] = []
    for row in rows:
        ranking_component = float(row.get("ranking_score_component", 0) or 0)
        urgency_raw = float(row.get("urgency_proxy", 0) or 0)
        fit_raw = float(row.get("condition_fit", 0) or 0)
        exclusion_raw = float(row.get("exclusion_risk_signal", 0) or 0)

        if spread <= 1e-8:
            ranking_score = 1.0
        else:
            ranking_score = (ranking_component - min_score) / spread
        urgency_score = min(max(urgency_raw / 3.0, 0.0), 1.0)
        fit_score = min(max(fit_raw, 0.0), 1.0)
        exclusion_risk_score = min(max(exclusion_raw / 3.0, 0.0), 1.0)

        normalized.append(
            {
                "external_patient_id": str(row.get("external_patient_id")),
                "ranking_score": ranking_score,
                "urgency_score": urgency_score,
                "fit_score": fit_score,
                "exclusion_risk_score": exclusion_risk_score,
            }
        )

    return sorted(normalized, key=lambda item: float(item["ranking_score"]), reverse=True)
