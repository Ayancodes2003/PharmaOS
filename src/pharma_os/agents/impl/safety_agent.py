"""Safety investigation agent for adverse event analysis."""

from __future__ import annotations

import logging
from typing import Any

from pharma_os.agents.base import AgentBase, SafetyInvestigationResult
from pharma_os.agents.core.context import AgentExecutionContext
from pharma_os.agents.core.result_builders import SafetyResultBuilder


logger = logging.getLogger(__name__)


class SafetyAgent(AgentBase):
    """Agent for investigating patient safety and adverse events."""

    def __init__(self):
        """Initialize safety agent."""
        super().__init__()
        self.agent_type = "safety_investigation"

    def execute(self, context: AgentExecutionContext) -> SafetyInvestigationResult:
        """Execute safety investigation.

        Args:
            context: Execution context with patient and event data

        Returns:
            Safety investigation result
        """
        logger.info(f"Starting safety investigation (Trace: {context.trace_id})")

        builder = SafetyResultBuilder(context)

        try:
            # Extract patient data
            patient_data = context.get_input_data("patient")
            if not patient_data:
                return builder.build_result(
                    success=False,
                    error="No patient data provided in context",
                )

            # Extract event data
            event_data = context.get_input_data("event")
            if not event_data:
                return builder.build_result(
                    success=False,
                    error="No event data provided in context",
                )

            # Generate summaries
            patient_summary = self._summarize_patient(patient_data)
            safety_context = self._build_safety_context(patient_data, event_data)

            # Perform risk assessment
            risk_assessment = self._assess_risk(patient_data, event_data)

            # Identify suspicious patterns
            suspicious_patterns = self._identify_patterns(patient_data, event_data)

            # Extract recent events
            recent_events = self._extract_recent_events(event_data)

            # Check for drug interactions
            drug_interactions = self._check_drug_interactions(patient_data)

            # Generate safety recommendation
            recommendation = self._generate_safety_recommendation(
                risk_assessment, suspicious_patterns
            )

            logger.info(f"Safety investigation completed: Risk Level = {risk_assessment}")

            return builder.build_result(
                success=True,
                patient_summary=patient_summary,
                safety_context=safety_context,
                risk_assessment=risk_assessment,
                recommendation=recommendation,
                suspicious_patterns=suspicious_patterns,
                recent_events=recent_events,
                drug_interactions=drug_interactions,
            )

        except Exception as e:
            logger.error(f"Safety investigation failed: {str(e)}", exc_info=True)
            return builder.build_result(
                success=False,
                error=f"Investigation failed: {str(e)}",
            )

    def _summarize_patient(self, patient_data: dict[str, Any]) -> str:
        """Summarize patient information.

        Args:
            patient_data: Patient data dictionary

        Returns:
            Patient summary
        """
        parts = []

        if "patient_id" in patient_data:
            parts.append(f"ID: {patient_data['patient_id']}")

        if "age" in patient_data:
            parts.append(f"Age: {patient_data['age']}")

        if "gender" in patient_data:
            parts.append(f"Gender: {patient_data['gender']}")

        if "medical_history" in patient_data:
            history = patient_data["medical_history"]
            if isinstance(history, list):
                parts.append(f"Conditions: {len(history)}")
            else:
                parts.append(f"History: {history}")

        return " | ".join(parts) if parts else "Limited patient data"

    def _build_safety_context(
        self, patient_data: dict[str, Any], event_data: dict[str, Any]
    ) -> str:
        """Build safety context from patient and event data.

        Args:
            patient_data: Patient data
            event_data: Event data

        Returns:
            Safety context description
        """
        parts = []

        if "event_type" in event_data:
            parts.append(f"Event Type: {event_data['event_type']}")

        if "event_date" in event_data:
            parts.append(f"Date: {event_data['event_date']}")

        if "severity" in event_data:
            parts.append(f"Severity: {event_data['severity']}")

        if "current_medications" in patient_data:
            meds = patient_data["current_medications"]
            if isinstance(meds, list):
                parts.append(f"Active Medications: {len(meds)}")

        if "allergies" in patient_data:
            allergies = patient_data["allergies"]
            if isinstance(allergies, list) and allergies:
                parts.append(f"Known Allergies: {len(allergies)}")

        return " | ".join(parts) if parts else "Limited event context"

    def _assess_risk(
        self, patient_data: dict[str, Any], event_data: dict[str, Any]
    ) -> str:
        """Assess risk level based on data.

        Args:
            patient_data: Patient data
            event_data: Event data

        Returns:
            Risk level (LOW, MODERATE, HIGH, CRITICAL)
        """
        risk_score = 0

        # Severity escalation
        if "severity" in event_data:
            severity = event_data["severity"].lower()
            if severity == "critical":
                risk_score += 3
            elif severity == "severe":
                risk_score += 2
            elif severity == "moderate":
                risk_score += 1

        # Multiple comorbidities
        if "medical_history" in patient_data:
            history = patient_data["medical_history"]
            if isinstance(history, list) and len(history) > 3:
                risk_score += 1

        # Polypharmacy
        if "current_medications" in patient_data:
            meds = patient_data["current_medications"]
            if isinstance(meds, list) and len(meds) > 5:
                risk_score += 1

        # Known allergies
        if "allergies" in patient_data:
            allergies = patient_data["allergies"]
            if isinstance(allergies, list) and allergies:
                risk_score += 1

        # Assign risk level
        if risk_score >= 4:
            return "CRITICAL"
        elif risk_score >= 3:
            return "HIGH"
        elif risk_score >= 1:
            return "MODERATE"
        else:
            return "LOW"

    def _identify_patterns(
        self, patient_data: dict[str, Any], event_data: dict[str, Any]
    ) -> list[str]:
        """Identify suspicious patterns in data.

        Args:
            patient_data: Patient data
            event_data: Event data

        Returns:
            List of suspicious patterns
        """
        patterns = []

        # Check for repeated events
        if "event_history" in event_data:
            history = event_data["event_history"]
            if isinstance(history, list) and len(history) > 2:
                patterns.append(f"Recurring events ({len(history)} occurrences)")

        # Check for unusual medication combinations
        if "current_medications" in patient_data:
            meds = patient_data["current_medications"]
            if isinstance(meds, list) and len(meds) > 8:
                patterns.append("Unusual polymedication pattern")

        # Check for temporal relationships
        if "event_date" in event_data and "medication_start_date" in event_data:
            if event_data["event_date"] == event_data["medication_start_date"]:
                patterns.append("Event temporal correlation with drug initiation")

        # Check for high-risk drug combinations
        if "current_medications" in patient_data:
            meds = patient_data["current_medications"]
            if isinstance(meds, list):
                if any(med in meds for med in ["warfarin", "aspirin"]):
                    if any(med in meds for med in ["NSAIDs", "ibuprofen"]):
                        patterns.append("High-risk drug combination detected")

        return patterns

    def _extract_recent_events(self, event_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract recent adverse events.

        Args:
            event_data: Event data

        Returns:
            List of recent event dictionaries
        """
        events = []

        # Main event
        if "event_type" in event_data:
            events.append(
                {
                    "type": event_data.get("event_type"),
                    "date": event_data.get("event_date"),
                    "severity": event_data.get("severity", "Unknown"),
                }
            )

        # Historical events
        if "event_history" in event_data:
            history = event_data["event_history"]
            if isinstance(history, list):
                for hist_event in history[:5]:  # Limit to 5 most recent
                    if isinstance(hist_event, dict):
                        events.append(hist_event)

        return events

    def _check_drug_interactions(self, patient_data: dict[str, Any]) -> list[str]:
        """Check for potential drug interactions.

        Args:
            patient_data: Patient data

        Returns:
            List of interaction concerns
        """
        interactions = []

        if "current_medications" not in patient_data:
            return interactions

        meds = patient_data["current_medications"]
        if not isinstance(meds, list):
            return interactions

        # Define known interaction pairs
        interaction_pairs = [
            (["warfarin", "aspirin"], "Increased bleeding risk"),
            (["metformin", "contrast_dye"], "Risk of acute kidney injury"),
            (["ace_inhibitors", "potassium_supplements"], "Hyperkalemia risk"),
            (
                ["antidepressants", "tramadol"],
                "Increased serotonin syndrome risk",
            ),
        ]

        # Check for interactions
        for drug_pair, concern in interaction_pairs:
            if all(any(drug in med.lower() for med in meds) for drug in drug_pair):
                interactions.append(concern)

        return interactions

    def _generate_safety_recommendation(
        self, risk_assessment: str, patterns: list[str]
    ) -> str:
        """Generate safety recommendation.

        Args:
            risk_assessment: Risk level
            patterns: List of suspicious patterns

        Returns:
            Safety recommendation
        """
        if risk_assessment == "CRITICAL":
            return (
                "URGENT: Immediate clinical evaluation required. "
                "Consider hospitalization if not already admitted."
            )
        elif risk_assessment == "HIGH":
            rec = "Close monitoring recommended. "
            if patterns:
                rec += f"Investigate {len(patterns)} identified pattern(s). "
            rec += "Consider medication review with pharmacist."
            return rec
        elif risk_assessment == "MODERATE":
            return "Standard monitoring appropriate. Document findings."
        else:
            return "Continue routine monitoring. No immediate action required."
