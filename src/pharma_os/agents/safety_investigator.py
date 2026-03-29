"""Safety investigator agent for adverse event and safety analysis."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta
from typing import Any

from pharma_os.agents.base import (
    BaseAgent,
    ExecutionContext,
    SafetyInvestigationResult,
    SafetyInvestigatorRequest,
)
from pharma_os.agents.prompts import PromptRegistry

logger = logging.getLogger(__name__)


class SafetyInvestigatorAgent(BaseAgent):
    """Agent for analyzing patient safety and adverse event patterns."""

    def __init__(
        self,
        llm_provider: Any,
        prompt_registry: PromptRegistry,
    ):
        """Initialize safety investigator agent.

        Args:
            llm_provider: LLM provider instance
            prompt_registry: Prompt registry for system prompts
        """
        super().__init__(llm_provider)
        self.prompt_registry = prompt_registry

    async def execute(
        self,
        request: SafetyInvestigatorRequest,
        context: ExecutionContext,
    ) -> SafetyInvestigationResult:
        """Execute safety investigation.

        Analyzes adverse event history, drug exposures, and safety patterns
        to produce structured safety assessment.

        Args:
            request: Safety investigation request
            context: Execution context with session and settings

        Returns:
            SafetyInvestigationResult with structured safety analysis
        """
        start_time = time.time()

        try:
            # Get patient data
            from pharma_os.db.repositories.patient_repository import PatientRepository

            patient_repo = PatientRepository(context.session)

            patient = None
            try:
                from uuid import UUID

                patient_id = UUID(request.patient_id)
                patient = patient_repo.get_by_id(patient_id)
            except (ValueError, TypeError):
                patient = patient_repo.get_by_external_patient_id(request.patient_id)

            if not patient:
                execution_time_ms = (time.time() - start_time) * 1000
                return SafetyInvestigationResult(
                    trace_id=context.trace_id,
                    execution_time_ms=execution_time_ms,
                    success=False,
                    error=f"Patient not found: {request.patient_id}",
                )

            # Get adverse events
            patient_summary = self._summarize_patient(patient)
            recent_events = self._extract_recent_events(patient)
            event_context = self._summarize_adverse_events(patient)
            drug_context = self._summarize_drug_exposures(patient, request.drug_name)

            # Get safety prediction if available
            prediction_context = {}
            if request.include_prediction:
                prediction_context = self._get_safety_prediction(patient, context)

            # Build analysis using LLM
            system_prompt = self.prompt_registry.get_prompt_or_default(
                "safety_investigator",
                "You are a clinical safety investigator.",
            )

            analysis_text = await self.llm_provider.complete(
                messages=[],
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=2000,
            )

            # Identify suspicious patterns
            suspicious = self._identify_suspicious_patterns(patient, request.drug_name)
            drug_interactions = self._identify_drug_interactions(patient, request.drug_name)

            # Build result
            result = SafetyInvestigationResult(
                trace_id=context.trace_id,
                execution_time_ms=(time.time() - start_time) * 1000,
                success=True,
                patient_summary=patient_summary,
                safety_context=event_context + " " + drug_context,
                risk_assessment=(
                    analysis_text.content or self._default_risk_assessment(patient, request.drug_name)
                ),
                suspicious_patterns=suspicious,
                recommendation=self._generate_safety_recommendation(patient, suspicious),
                prediction_context=prediction_context,
                recent_events=recent_events,
                drug_interaction_concerns=drug_interactions,
                tool_calls_used=["patient_lookup", "adverse_event_lookup", "drug_exposure_lookup"],
            )

            return result

        except Exception as e:
            logger.error(f"Error in safety investigation: {e}")
            execution_time_ms = (time.time() - start_time) * 1000
            return SafetyInvestigationResult(
                trace_id=context.trace_id,
                execution_time_ms=execution_time_ms,
                success=False,
                error=str(e),
            )

    def _summarize_patient(self, patient: Any) -> str:
        """Summarize patient profile for safety context.

        Args:
            patient: Patient ORM model instance

        Returns:
            Patient summary string
        """
        return (
            f"Patient {patient.external_patient_id}: "
            f"{patient.age} year-old {patient.sex}, "
            f"primary condition: {patient.primary_condition}, "
            f"comorbidities: {patient.comorbidity_summary or 'None documented'}"
        )

    def _extract_recent_events(self, patient: Any) -> list[dict[str, Any]]:
        """Extract recent adverse events with summary.

        Args:
            patient: Patient ORM model instance

        Returns:
            List of recent event dictionaries
        """
        events = []
        if not hasattr(patient, "adverse_events") or not patient.adverse_events:
            return events

        # Sort by date and get last 10
        sorted_events = sorted(
            patient.adverse_events,
            key=lambda x: x.event_date,
            reverse=True,
        )[:10]

        for ae in sorted_events:
            event_dict = {
                "event_type": ae.event_type if hasattr(ae, "event_type") else "Unknown",
                "date": str(ae.event_date) if hasattr(ae, "event_date") else None,
                "severity": ae.severity.value if hasattr(ae, "severity") else "Unknown",
                "is_serious": ae.is_serious if hasattr(ae, "is_serious") else False,
                "description": ae.description if hasattr(ae, "description") else None,
            }
            events.append(event_dict)

        return events

    def _summarize_adverse_events(self, patient: Any) -> str:
        """Summarize adverse event history.

        Args:
            patient: Patient ORM model instance

        Returns:
            Adverse events summary
        """
        if not hasattr(patient, "adverse_events") or not patient.adverse_events:
            return "No adverse events documented."

        serious_count = sum(1 for ae in patient.adverse_events if ae.is_serious)
        total_count = len(patient.adverse_events)

        # Get events from last 90 days
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        recent_count = sum(
            1 for ae in patient.adverse_events if ae.event_date >= cutoff_date.date()
        )

        summary = f"Adverse event history: {total_count} total events, {serious_count} serious, {recent_count} in last 90 days."

        # Get most common event types
        event_types = {}
        for ae in patient.adverse_events:
            event_type = ae.event_type if hasattr(ae, "event_type") else "Unknown"
            event_types[event_type] = event_types.get(event_type, 0) + 1

        if event_types:
            top_types = sorted(event_types.items(), key=lambda x: x[1], reverse=True)[:3]
            summary += f" Most common: {', '.join([f'{count}x {et}' for et, count in top_types])}."

        return summary

    def _summarize_drug_exposures(self, patient: Any, drug_name: str | None = None) -> str:
        """Summarize drug exposures, optionally filtered.

        Args:
            patient: Patient ORM model instance
            drug_name: Optional specific drug to filter on

        Returns:
            Drug exposures summary
        """
        if not hasattr(patient, "drug_exposures") or not patient.drug_exposures:
            return "No documented drug exposures."

        if drug_name:
            exposures = [de for de in patient.drug_exposures if drug_name.lower() in de.drug_name.lower()]
            if not exposures:
                return f"No exposures found for drug: {drug_name}"

            active = sum(1 for de in exposures if de.is_active)
            return f"Drug {drug_name}: {active} active exposure(s), {len(exposures)} total."
        else:
            active = sum(1 for de in patient.drug_exposures if de.is_active)
            return f"Current medications: {active} active drugs, {len(patient.drug_exposures)} total exposures."

    def _get_safety_prediction(self, patient: Any, context: ExecutionContext) -> dict[str, Any]:
        """Get safety prediction if available.

        Args:
            patient: Patient model
            context: Execution context

        Returns:
            Prediction context dictionary
        """
        try:
            from pharma_os.db.repositories.prediction_repository import PredictionRepository

            pred_repo = PredictionRepository(context.session)
            predictions = pred_repo.get_safety_predictions(patient.id)

            if predictions:
                latest = predictions[0]
                return {
                    "risk_probability": float(latest.risk_probability) if hasattr(latest, "risk_probability") else None,
                    "risk_class": latest.risk_class if hasattr(latest, "risk_class") else None,
                    "created_at": str(latest.created_at) if hasattr(latest, "created_at") else None,
                }
        except Exception as e:
            logger.debug(f"Could not retrieve safety prediction: {e}")

        return {}

    def _identify_suspicious_patterns(self, patient: Any, drug_name: str | None = None) -> list[str]:
        """Identify suspicious patterns in adverse events.

        Args:
            patient: Patient model
            drug_name: Optional specific drug to focus on

        Returns:
            List of suspicious pattern strings
        """
        patterns = []

        if not hasattr(patient, "adverse_events") or not patient.adverse_events:
            return patterns

        # Count serious events
        serious_events = [ae for ae in patient.adverse_events if ae.is_serious]
        if len(serious_events) > 3:
            patterns.append(f"Multiple serious adverse events ({len(serious_events)})")

        # Check for clustering
        if len(patient.adverse_events) > 5:
            sorted_events = sorted(patient.adverse_events, key=lambda x: x.event_date)
            # Check for 3+ events within 30 days
            for i in range(len(sorted_events) - 2):
                date_diff = (sorted_events[i + 2].event_date - sorted_events[i].event_date).days
                if date_diff <= 30:
                    patterns.append(f"Clustering of {3} events within 30 days (dates: {sorted_events[i].event_date} to {sorted_events[i + 2].event_date})")
                    break  # Only report once

        # Check for specific event type recurrence
        event_types = {}
        for ae in patient.adverse_events:
            event_type = ae.event_type if hasattr(ae, "event_type") else "Unknown"
            event_types[event_type] = event_types.get(event_type, 0) + 1

        for event_type, count in event_types.items():
            if count > 2:
                patterns.append(f"Recurrent event type: {event_type} ({count} occurrences)")

        return patterns

    def _identify_drug_interactions(self, patient: Any, drug_name: str | None = None) -> list[str]:
        """Identify potential drug interactions or cumulative toxicity.

        Args:
            patient: Patient model
            drug_name: Optional specific drug to focus on

        Returns:
            List of interaction concern strings
        """
        concerns = []

        if not hasattr(patient, "drug_exposures") or not patient.drug_exposures:
            return concerns

        active_drugs = [de for de in patient.drug_exposures if de.is_active]

        if len(active_drugs) > 5:
            concerns.append(f"Polypharmacy: {len(active_drugs)} active concurrent medications")

        # Check for specific drug/comorbidity interactions
        if drug_name:
            if "anticoagulant" in drug_name.lower() and patient.comorbidity_summary:
                if "kidney" in patient.comorbidity_summary.lower() or "renal" in patient.comorbidity_summary.lower():
                    concerns.append("Anticoagulant with renal impairment: dose monitoring needed")

        return concerns

    def _generate_safety_recommendation(self, patient: Any, suspicious_patterns: list[str]) -> str:
        """Generate safety recommendation.

        Args:
            patient: Patient model
            suspicious_patterns: List of identified suspicious patterns

        Returns:
            Recommendation string
        """
        if not suspicious_patterns:
            return "Monitor per standard safety protocols; no acute concerns identified."

        if any("serious" in p.lower() for p in suspicious_patterns):
            return "Recommend enhanced monitoring and causal assessment for serious events."

        if any("cluster" in p.lower() for p in suspicious_patterns):
            return "Recommend investigation of event clustering; consider temporal relationship analysis."

        return f"Recommend review of identified patterns: {'; '.join(suspicious_patterns[:2])}"

    def _default_risk_assessment(self, patient: Any, drug_name: str | None = None) -> str:
        """Generate default risk assessment if LLM unavailable.

        Args:
            patient: Patient model
            drug_name: Optional specific drug

        Returns:
            Risk assessment string
        """
        base = f"Safety assessment for patient {patient.external_patient_id} "
        if drug_name:
            base += f"regarding {drug_name} exposure. "
        else:
            base += "based on clinical history. "

        base += (
            "Assessment based on available adverse event records, drug exposure history, "
            "and clinical context. Clinical judgment and pharmacovigilance protocols recommended."
        )

        return base
