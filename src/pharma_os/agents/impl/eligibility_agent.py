"""Eligibility assessment agent for clinical trial matching."""

from __future__ import annotations

import logging
from typing import Any

from pharma_os.agents.base import AgentBase, EligibilityAnalysisResult
from pharma_os.agents.core.context import AgentExecutionContext
from pharma_os.agents.core.result_builders import EligibilityResultBuilder


logger = logging.getLogger(__name__)


class EligibilityAgent(AgentBase):
    """Agent for analyzing patient eligibility for clinical trials."""

    def __init__(self):
        """Initialize eligibility agent."""
        super().__init__()
        self.agent_type = "eligibility_assessment"

    def execute(self, context: AgentExecutionContext) -> EligibilityAnalysisResult:
        """Execute eligibility assessment.

        Args:
            context: Execution context with patient and trial data

        Returns:
            Eligibility analysis result
        """
        logger.info(f"Starting eligibility assessment (Trace: {context.trace_id})")

        builder = EligibilityResultBuilder(context)

        try:
            # Extract patient data
            patient_data = context.get_input_data("patient")
            if not patient_data:
                return builder.build_result(
                    success=False,
                    error="No patient data provided in context",
                )

            # Extract trial data
            trial_data = context.get_input_data("trial")
            if not trial_data:
                return builder.build_result(
                    success=False,
                    error="No trial data provided in context",
                )

            # Generate summaries
            patient_summary = self._summarize_patient(patient_data)
            trial_summary = self._summarize_trial(trial_data)

            # Perform eligibility assessment
            assessment, inclusion_reasoning, exclusion_reasoning = (
                self._assess_eligibility(patient_data, trial_data)
            )

            # Identify risk factors
            risk_factors = self._identify_risk_factors(patient_data, trial_data)

            # Generate recommendation
            recommendation = self._generate_recommendation(
                assessment, risk_factors
            )

            # Gather evidence
            evidence = self._gather_evidence(patient_data, trial_data)

            logger.info(f"Eligibility assessment completed: {assessment}")

            return builder.build_result(
                success=True,
                patient_summary=patient_summary,
                trial_summary=trial_summary,
                assessment=assessment,
                inclusion_reasoning=inclusion_reasoning,
                exclusion_reasoning=exclusion_reasoning,
                recommendation=recommendation,
                risk_factors=risk_factors,
                evidence=evidence,
            )

        except Exception as e:
            logger.error(f"Eligibility assessment failed: {str(e)}", exc_info=True)
            return builder.build_result(
                success=False,
                error=f"Assessment failed: {str(e)}",
            )

    def _summarize_patient(self, patient_data: dict[str, Any]) -> str:
        """Summarize patient information.

        Args:
            patient_data: Patient data dictionary

        Returns:
            Patient summary
        """
        parts = []

        if "age" in patient_data:
            parts.append(f"Age: {patient_data['age']}")

        if "gender" in patient_data:
            parts.append(f"Gender: {patient_data['gender']}")

        if "medical_history" in patient_data:
            conditions = patient_data["medical_history"]
            if isinstance(conditions, list):
                parts.append(f"Medical History: {', '.join(conditions)}")
            else:
                parts.append(f"Medical History: {conditions}")

        if "current_medications" in patient_data:
            meds = patient_data["current_medications"]
            if isinstance(meds, list):
                parts.append(f"Current Medications: {', '.join(meds)}")
            else:
                parts.append(f"Current Medications: {meds}")

        if "allergies" in patient_data:
            allergies = patient_data["allergies"]
            if isinstance(allergies, list):
                parts.append(f"Allergies: {', '.join(allergies)}")
            else:
                parts.append(f"Allergies: {allergies}")

        return " | ".join(parts) if parts else "Minimal patient data available"

    def _summarize_trial(self, trial_data: dict[str, Any]) -> str:
        """Summarize trial information.

        Args:
            trial_data: Trial data dictionary

        Returns:
            Trial summary
        """
        parts = []

        if "trial_name" in trial_data:
            parts.append(f"Trial: {trial_data['trial_name']}")

        if "phase" in trial_data:
            parts.append(f"Phase: {trial_data['phase']}")

        if "condition" in trial_data:
            parts.append(f"Condition: {trial_data['condition']}")

        if "inclusion_criteria" in trial_data:
            criteria = trial_data["inclusion_criteria"]
            if isinstance(criteria, list):
                parts.append(f"Inclusion: {len(criteria)} criteria")
            else:
                parts.append("Inclusion: specified")

        if "exclusion_criteria" in trial_data:
            criteria = trial_data["exclusion_criteria"]
            if isinstance(criteria, list):
                parts.append(f"Exclusion: {len(criteria)} criteria")
            else:
                parts.append("Exclusion: specified")

        return " | ".join(parts) if parts else "Minimal trial data available"

    def _assess_eligibility(
        self, patient_data: dict[str, Any], trial_data: dict[str, Any]
    ) -> tuple[str, str, str]:
        """Assess patient eligibility for trial.

        Args:
            patient_data: Patient data
            trial_data: Trial data

        Returns:
            Tuple of (assessment, inclusion_reasoning, exclusion_reasoning)
        """
        inclusion_reasoning = "Patient meets the following criteria:"
        exclusion_reasoning = "Potential exclusionary factors:"

        # Simple eligibility logic based on available data
        is_eligible = True
        reasons = []

        # Check age if specified
        if "age" in patient_data and "age_range" in trial_data:
            age = patient_data["age"]
            age_range = trial_data["age_range"]
            min_age, max_age = age_range.get("min", 0), age_range.get("max", 150)

            if min_age <= age <= max_age:
                inclusion_reasoning += f" - Age {age} is within range ({min_age}-{max_age})"
            else:
                is_eligible = False
                reasons.append(f"Age {age} outside trial range ({min_age}-{max_age})")

        # Check for medication conflicts
        if "current_medications" in patient_data:
            patient_meds = patient_data["current_medications"]
            if isinstance(patient_meds, list):
                if "contraindicated_drugs" in trial_data:
                    contraindicated = trial_data["contraindicated_drugs"]
                    conflicts = set(patient_meds) & set(contraindicated)
                    if conflicts:
                        is_eligible = False
                        reasons.append(
                            f"Medication conflicts: {', '.join(conflicts)}"
                        )

        if reasons:
            exclusion_reasoning += " " + " | ".join(reasons)

        assessment = "ELIGIBLE" if is_eligible else "NOT ELIGIBLE"
        return assessment, inclusion_reasoning, exclusion_reasoning

    def _identify_risk_factors(
        self, patient_data: dict[str, Any], trial_data: dict[str, Any]
    ) -> list[str]:
        """Identify potential risk factors.

        Args:
            patient_data: Patient data
            trial_data: Trial data

        Returns:
            List of risk factors
        """
        risk_factors = []

        # Check for pre-existing conditions
        if "medical_history" in patient_data:
            history = patient_data["medical_history"]
            if isinstance(history, list):
                if len(history) > 2:
                    risk_factors.append(
                        f"Multiple comorbidities ({len(history)} conditions)"
                    )
            if isinstance(history, str) and "severe" in history.lower():
                risk_factors.append("History of severe conditions")

        # Check for allergies
        if "allergies" in patient_data:
            allergies = patient_data["allergies"]
            if isinstance(allergies, list) and allergies:
                risk_factors.append(f"Known allergies: {len(allergies)}")

        # Check for polypharmacy
        if "current_medications" in patient_data:
            meds = patient_data["current_medications"]
            if isinstance(meds, list) and len(meds) > 5:
                risk_factors.append(f"Polypharmacy ({len(meds)} medications)")

        return risk_factors

    def _generate_recommendation(self, assessment: str, risk_factors: list[str]) -> str:
        """Generate analyst recommendation.

        Args:
            assessment: Eligibility assessment
            risk_factors: List of risk factors

        Returns:
            Recommendation text
        """
        if assessment == "ELIGIBLE":
            if not risk_factors:
                return "Patient is suitable for trial enrollment with no significant concerns."
            else:
                return (
                    f"Patient is eligible but has {len(risk_factors)} risk factor(s) "
                    "that should be discussed with the investigator."
                )
        else:
            return "Patient does not meet eligibility criteria for this trial."

    def _gather_evidence(
        self, patient_data: dict[str, Any], trial_data: dict[str, Any]
    ) -> list[str]:
        """Gather supporting evidence from data.

        Args:
            patient_data: Patient data
            trial_data: Trial data

        Returns:
            List of evidence snippets
        """
        evidence = []

        if "recent_labs" in patient_data:
            evidence.append(f"Recent lab results: {patient_data['recent_labs']}")

        if "diagnostic_tests" in patient_data:
            tests = patient_data["diagnostic_tests"]
            if isinstance(tests, list):
                evidence.append(f"Diagnostic tests performed: {len(tests)}")

        if "trial_sponsor" in trial_data:
            evidence.append(f"Trial sponsored by: {trial_data['trial_sponsor']}")

        if "enrollment_target" in trial_data:
            evidence.append(f"Target enrollment: {trial_data['enrollment_target']}")

        return evidence
