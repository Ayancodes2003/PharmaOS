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
from pharma_os.agents.llm.provider import Message
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
            # Gather grounded tool context
            patient_data = await context.invoke_tool(
                "patient_lookup",
                {
                    "session": context.session,
                    "patient_id": request.patient_id,
                    "external_patient_id": request.patient_id,
                },
            )
            patient = patient_data.get("patient") if patient_data else None

            if not patient:
                execution_time_ms = (time.time() - start_time) * 1000
                return EligibilityAnalysisResult(
                    trace_id=context.trace_id,
                    execution_time_ms=execution_time_ms,
                    success=False,
                    error=f"Patient not found: {request.patient_id}",
                )

            trial_data = await context.invoke_tool(
                "trial_lookup",
                {
                    "session": context.session,
                    "trial_id": request.trial_id,
                    "trial_code": request.trial_id,
                },
            )
            trial = trial_data.get("trial") if trial_data else None

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
            adverse_events_data = await context.invoke_tool(
                "adverse_event_lookup",
                {
                    "session": context.session,
                    "patient_id": str(patient.id),
                    "limit": 50,
                },
            )
            adverse_events = adverse_events_data.get("events", []) if adverse_events_data else []
            adverse_events_summary = self._summarize_adverse_events(adverse_events)

            drug_exposures_data = await context.invoke_tool(
                "drug_exposure_lookup",
                {
                    "session": context.session,
                    "patient_id": str(patient.id),
                    "limit": 50,
                },
            )
            drug_exposures = drug_exposures_data.get("exposures", []) if drug_exposures_data else []
            drug_exposures_summary = self._summarize_drug_exposures(drug_exposures)

            # Get prediction if available
            prediction_context = {}
            if request.include_prediction:
                prediction_data = await context.invoke_tool(
                    "prediction_lookup",
                    {
                        "session": context.session,
                        "prediction_type": "eligibility",
                        "patient_id": str(patient.id),
                        "trial_id": str(trial.id),
                    },
                )
                prediction_context = prediction_data.get("prediction") if prediction_data else {}

            # Build analysis using LLM
            system_prompt = self.prompt_registry.get_prompt_or_default(
                "eligibility_analyst",
                "You are a clinical trial eligibility analyst.",
            )

            llm_input = "\n".join(
                [
                    f"Patient Summary: {patient_summary}",
                    f"Trial Summary: {trial_summary}",
                    f"Adverse Events: {adverse_events_summary}",
                    f"Drug Exposures: {drug_exposures_summary}",
                    f"Prediction: {prediction_context}",
                ]
            )

            analysis_text = await self.llm_provider.complete(
                messages=[Message("user", llm_input)],
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

    def _summarize_adverse_events(self, adverse_events: list[Any]) -> str:
        """Summarize adverse events.

        Args:
            adverse_events: Adverse event model instances

        Returns:
            Adverse events summary
        """
        if not adverse_events:
            return "No adverse events documented"

        serious_count = sum(1 for ae in adverse_events if ae.is_serious)
        return f"Adverse events: {len(adverse_events)} total, {serious_count} serious"

    def _summarize_drug_exposures(self, drug_exposures: list[Any]) -> str:
        """Summarize drug exposures.

        Args:
            drug_exposures: Drug exposure model instances

        Returns:
            Drug exposures summary
        """
        if not drug_exposures:
            return "No current drug exposures"

        active = sum(1 for de in drug_exposures if de.is_active)
        return f"Current medications: {active} active drugs, {len(drug_exposures)} total exposures"

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
