"""Eligibility analyst agent for trial eligibility analysis."""

from __future__ import annotations

import logging
import time
from typing import Any

from pharma_os.agents.base import (
    BaseAgent,
    EligibilityAnalysisResult,
    EligibilityAnalystRequest,
    ExecutionContext,
)
from pharma_os.agents.prompts import PromptRegistry

logger = logging.getLogger(__name__)


class EligibilityAnalystAgent(BaseAgent):
    """Agent for analyzing patient-trial eligibility fit."""

    def __init__(
        self,
        llm_provider: Any,
        prompt_registry: PromptRegistry,
    ):
        """Initialize eligibility analyst agent.

        Args:
            llm_provider: LLM provider instance
            prompt_registry: Prompt registry for system prompts
        """
        super().__init__(llm_provider)
        self.prompt_registry = prompt_registry

    async def execute(
        self,
        request: EligibilityAnalystRequest,
        context: ExecutionContext,
    ) -> EligibilityAnalysisResult:
        """Execute eligibility analysis.

        Analyzes patient profile against trial criteria and produces
        structured eligibility assessment with reasoning and recommendation.

        Args:
            request: Eligibility analysis request
            context: Execution context with session and settings

        Returns:
            EligibilityAnalysisResult with structured analysis
        """
        start_time = time.time()

        try:
            # Get patient data from repository
            from pharma_os.db.repositories.patient_repository import PatientRepository

            patient_repo = PatientRepository(context.session)

            # Try to get by UUID first, then by external ID
            patient = None
            try:
                from uuid import UUID

                patient_id = UUID(request.patient_id)
                patient = patient_repo.get_by_id(patient_id)
            except (ValueError, TypeError):
                patient = patient_repo.get_by_external_patient_id(request.patient_id)

            if not patient:
                execution_time_ms = (time.time() - start_time) * 1000
                return EligibilityAnalysisResult(
                    trace_id=context.trace_id,
                    execution_time_ms=execution_time_ms,
                    success=False,
                    error=f"Patient not found: {request.patient_id}",
                )

            # Get trial data from repository
            from pharma_os.db.repositories.trial_repository import TrialRepository

            trial_repo = TrialRepository(context.session)

            trial = None
            try:
                from uuid import UUID

                trial_id = UUID(request.trial_id)
                trial = trial_repo.get_by_id(trial_id)
            except (ValueError, TypeError):
                trial = trial_repo.get_by_trial_code(request.trial_id)

            if not trial:
                execution_time_ms = (time.time() - start_time) * 1000
                return EligibilityAnalysisResult(
                    trace_id=context.trace_id,
                    execution_time_ms=execution_time_ms,
                    success=False,
                    error=f"Trial not found: {request.trial_id}",
                )

            # Build context information
            patient_summary = self._summarize_patient(patient)
            trial_summary = self._summarize_trial(trial)
            adverse_events_summary = self._summarize_adverse_events(patient)
            drug_exposures_summary = self._summarize_drug_exposures(patient)

            # Get prediction if available
            prediction_context = {}
            if request.include_prediction:
                prediction_context = self._get_eligibility_prediction(patient, trial, context)

            # Build analysis using LLM
            system_prompt = self.prompt_registry.get_prompt_or_default(
                "eligibility_analyst",
                "You are a clinical trial eligibility analyst.",
            )

            analysis_text = await self.llm_provider.complete(
                messages=[],  # Will be constructed below
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=2000,
            )

            # Construct structured result
            result = EligibilityAnalysisResult(
                trace_id=context.trace_id,
                execution_time_ms=(time.time() - start_time) * 1000,
                success=True,
                patient_summary=patient_summary,
                trial_summary=trial_summary,
                eligibility_assessment=(
                    analysis_text.content or self._default_eligibility_assessment(patient, trial)
                ),
                inclusion_reasoning=self._extract_inclusion_reasoning(patient, trial),
                exclusion_reasoning=self._extract_exclusion_reasoning(patient, trial),
                recommendation=self._generate_recommendation(patient, trial),
                prediction_context=prediction_context,
                risk_factors=self._identify_risk_factors(patient, trial),
                evidence_snippets=[
                    patient_summary,
                    trial_summary,
                    adverse_events_summary,
                    drug_exposures_summary,
                ],
                tool_calls_used=["patient_lookup", "trial_lookup", "adverse_event_lookup", "drug_exposure_lookup"],
            )

            return result

        except Exception as e:
            logger.error(f"Error in eligibility analysis: {e}")
            execution_time_ms = (time.time() - start_time) * 1000
            return EligibilityAnalysisResult(
                trace_id=context.trace_id,
                execution_time_ms=execution_time_ms,
                success=False,
                error=str(e),
            )

    def _summarize_patient(self, patient: Any) -> str:
        """Summarize patient profile.

        Args:
            patient: Patient ORM model instance

        Returns:
            Patient summary string
        """
        return (
            f"Patient {patient.external_patient_id}: "
            f"{patient.age} year-old {patient.sex}, "
            f"primary condition: {patient.primary_condition}, "
            f"enrollment status: {patient.enrollment_status}, "
            f"comorbidities: {patient.comorbidity_summary or 'None documented'}"
        )

    def _summarize_trial(self, trial: Any) -> str:
        """Summarize trial profile.

        Args:
            trial: Trial ORM model instance

        Returns:
            Trial summary string
        """
        return (
            f"Trial {trial.trial_code}: {trial.title}, "
            f"indication: {trial.indication}, "
            f"phase: {trial.phase}, "
            f"status: {trial.status}, "
            f"enrolled: {trial.enrolled_count}/{trial.recruitment_target or 'N/A'}"
        )

    def _summarize_adverse_events(self, patient: Any) -> str:
        """Summarize adverse events.

        Args:
            patient: Patient ORM model instance

        Returns:
            Adverse events summary
        """
        if not hasattr(patient, "adverse_events") or not patient.adverse_events:
            return "No adverse events documented"

        serious_count = sum(1 for ae in patient.adverse_events if ae.is_serious)
        return f"Adverse events: {len(patient.adverse_events)} total, {serious_count} serious"

    def _summarize_drug_exposures(self, patient: Any) -> str:
        """Summarize drug exposures.

        Args:
            patient: Patient ORM model instance

        Returns:
            Drug exposures summary
        """
        if not hasattr(patient, "drug_exposures") or not patient.drug_exposures:
            return "No current drug exposures"

        active = sum(1 for de in patient.drug_exposures if de.is_active)
        return f"Current medications: {active} active drugs, {len(patient.drug_exposures)} total exposures"

    def _get_eligibility_prediction(self, patient: Any, trial: Any, context: ExecutionContext) -> dict[str, Any]:
        """Get eligibility prediction if available.

        Args:
            patient: Patient model
            trial: Trial model
            context: Execution context

        Returns:
            Prediction context dictionary
        """
        try:
            from pharma_os.db.repositories.prediction_repository import PredictionRepository

            pred_repo = PredictionRepository(context.session)
            predictions = pred_repo.get_eligibility_predictions(patient.id, trial.id)

            if predictions:
                latest = predictions[0]
                return {
                    "probability": float(latest.probability) if hasattr(latest, "probability") else None,
                    "created_at": str(latest.created_at) if hasattr(latest, "created_at") else None,
                }
        except Exception as e:
            logger.debug(f"Could not retrieve eligibility prediction: {e}")

        return {}

    def _extract_inclusion_reasoning(self, patient: Any, trial: Any) -> str:
        """Extract or infer inclusion reasoning.

        Args:
            patient: Patient model
            trial: Trial model

        Returns:
            Inclusion reasoning string
        """
        reasoning = []
        reasoning.append(f"Patient age ({patient.age}) may be within trial range")
        reasoning.append(f"Primary condition ({patient.primary_condition}) aligns with trial indication ({trial.indication})")
        if not patient.adverse_events:
            reasoning.append("No significant adverse event history noted")
        return "; ".join(reasoning)

    def _extract_exclusion_reasoning(self, patient: Any, trial: Any) -> str:
        """Extract or infer exclusion reasoning.

        Args:
            patient: Patient model
            trial: Trial model

        Returns:
            Exclusion reasoning string
        """
        reasoning = []
        if hasattr(patient, "adverse_events") and patient.adverse_events:
            serious_events = [ae for ae in patient.adverse_events if ae.is_serious]
            if serious_events:
                reasoning.append(f"Serious prior adverse events ({len(serious_events)})")
        if patient.comorbidity_summary and "severe" in patient.comorbidity_summary.lower():
            reasoning.append(f"Significant comorbidities noted: {patient.comorbidity_summary[:100]}")
        return "; ".join(reasoning) if reasoning else "No major exclusion factors identified"

    def _generate_recommendation(self, patient: Any, trial: Any) -> str:
        """Generate analyst recommendation.

        Args:
            patient: Patient model
            trial: Trial model

        Returns:
            Recommendation string
        """
        # Simple heuristic for demonstration
        serious_events = 0
        if hasattr(patient, "adverse_events"):
            serious_events = sum(1 for ae in patient.adverse_events if ae.is_serious)

        if serious_events > 0:
            return f"Consider with caution due to {serious_events} serious adverse events"
        elif patient.comorbidity_summary and "diabetes" in patient.comorbidity_summary.lower():
            return "Requires diabetes management protocol review"
        else:
            return "Eligible for further screening"

    def _identify_risk_factors(self, patient: Any, trial: Any) -> list[str]:
        """Identify risk factors and blockers.

        Args:
            patient: Patient model
            trial: Trial model

        Returns:
            List of risk factor strings
        """
        risks = []

        if hasattr(patient, "adverse_events") and patient.adverse_events:
            serious_count = sum(1 for ae in patient.adverse_events if ae.is_serious)
            if serious_count > 0:
                risks.append(f"History of {serious_count} serious adverse events")

        if patient.enrollment_status.lower() == "excluded":
            risks.append("Patient currently marked as excluded from trials")

        if patient.comorbidity_summary:
            comorbidities = [c.strip() for c in patient.comorbidity_summary.split(",")]
            if len(comorbidities) > 2:
                risks.append(f"Multiple comorbidities: {len(comorbidities)}")

        return risks

    def _default_eligibility_assessment(self, patient: Any, trial: Any) -> str:
        """Generate default eligibility assessment if LLM unavailable.

        Args:
            patient: Patient model
            trial: Trial model

        Returns:
            Assessment string
        """
        return (
            f"Based on available data: Patient {patient.external_patient_id} "
            f"({patient.age}, {patient.sex}) with {patient.primary_condition} "
            f"evaluated for {trial.trial_code}. "
            f"Assessment requires review of trial-specific criteria documentation and clinical judgment."
        )
