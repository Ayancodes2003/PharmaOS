"""Consistent tool execution layer."""

from __future__ import annotations

import logging
import time
from typing import Any

from pharma_os.agents.core.context import AgentExecutionContext, ToolInvocationRecord

logger = logging.getLogger(__name__)


class ToolExecutor:
    """Consistent tool executor for all agents."""

    def __init__(self, context: AgentExecutionContext):
        """Initialize tool executor.

        Args:
            context: Execution context
        """
        self.context = context
        self.session = context.session  # Cached for tool calls
        self.settings = context.settings

    async def execute_patient_lookup(self, patient_id: str) -> dict[str, Any] | None:
        """Look up patient by ID or external ID.

        Args:
            patient_id: Patient UUID or external ID

        Returns:
            Patient data dict or None if not found
        """
        start_time = time.time()
        try:
            from pharma_os.db.repositories.patient_repository import PatientRepository

            repo = PatientRepository(self.session)

            # Try UUID first, then external ID
            patient = None
            try:
                from uuid import UUID

                patient_uuid = UUID(patient_id)
                patient = repo.get_by_id(patient_uuid)
            except (ValueError, TypeError):
                patient = repo.get_by_external_patient_id(patient_id)

            elapsed_ms = (time.time() - start_time) * 1000

            if patient:
                self.context.record_tool_call(
                    "patient_lookup",
                    success=True,
                    result_summary=f"Patient {patient.external_patient_id}",
                    execution_time_ms=elapsed_ms,
                )
                return self._patient_to_dict(patient)
            else:
                self.context.record_tool_call(
                    "patient_lookup",
                    success=False,
                    error=f"Patient not found: {patient_id}",
                    execution_time_ms=elapsed_ms,
                )
                return None

        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            error_msg = str(e)
            self.context.record_tool_call(
                "patient_lookup",
                success=False,
                error=error_msg,
                execution_time_ms=elapsed_ms,
            )
            self.context.record_error(error_msg)
            return None

    async def execute_trial_lookup(self, trial_id: str) -> dict[str, Any] | None:
        """Look up trial by ID or code.

        Args:
            trial_id: Trial UUID or trial code

        Returns:
            Trial data dict or None if not found
        """
        start_time = time.time()
        try:
            from pharma_os.db.repositories.trial_repository import TrialRepository

            repo = TrialRepository(self.session)

            trial = None
            try:
                from uuid import UUID

                trial_uuid = UUID(trial_id)
                trial = repo.get_by_id(trial_uuid)
            except (ValueError, TypeError):
                trial = repo.get_by_trial_code(trial_id)

            elapsed_ms = (time.time() - start_time) * 1000

            if trial:
                self.context.record_tool_call(
                    "trial_lookup",
                    success=True,
                    result_summary=f"Trial {trial.trial_code}",
                    execution_time_ms=elapsed_ms,
                )
                return self._trial_to_dict(trial)
            else:
                self.context.record_tool_call(
                    "trial_lookup",
                    success=False,
                    error=f"Trial not found: {trial_id}",
                    execution_time_ms=elapsed_ms,
                )
                return None

        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            error_msg = str(e)
            self.context.record_tool_call(
                "trial_lookup",
                success=False,
                error=error_msg,
                execution_time_ms=elapsed_ms,
            )
            self.context.record_error(error_msg)
            return None

    async def execute_adverse_events_lookup(self, patient_id: str, limit: int = 100) -> list[dict[str, Any]]:
        """Look up adverse events for patient.

        Args:
            patient_id: Patient UUID
            limit: Maximum events to return

        Returns:
            List of adverse event dicts
        """
        start_time = time.time()
        try:
            from uuid import UUID

            from pharma_os.db.repositories.adverse_event_repository import AdverseEventRepository

            repo = AdverseEventRepository(self.session)

            try:
                patient_uuid = UUID(patient_id)
            except (ValueError, TypeError):
                self.context.record_error(f"Invalid patient UUID: {patient_id}")
                return []

            events = repo.list_by_patient(patient_uuid, limit=limit)
            elapsed_ms = (time.time() - start_time) * 1000

            self.context.record_tool_call(
                "adverse_event_lookup",
                success=True,
                result_summary=f"{len(events)} events",
                execution_time_ms=elapsed_ms,
            )

            return [self._adverse_event_to_dict(ae) for ae in events]

        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            error_msg = str(e)
            self.context.record_tool_call(
                "adverse_event_lookup",
                success=False,
                error=error_msg,
                execution_time_ms=elapsed_ms,
            )
            self.context.record_error(error_msg)
            return []

    async def execute_drug_exposures_lookup(self, patient_id: str, limit: int = 100) -> list[dict[str, Any]]:
        """Look up drug exposures for patient.

        Args:
            patient_id: Patient UUID
            limit: Maximum exposures to return

        Returns:
            List of drug exposure dicts
        """
        start_time = time.time()
        try:
            from uuid import UUID

            from pharma_os.db.repositories.drug_exposure_repository import DrugExposureRepository

            repo = DrugExposureRepository(self.session)

            try:
                patient_uuid = UUID(patient_id)
            except (ValueError, TypeError):
                self.context.record_error(f"Invalid patient UUID: {patient_id}")
                return []

            exposures = repo.list_by_patient(patient_uuid, limit=limit)
            elapsed_ms = (time.time() - start_time) * 1000

            self.context.record_tool_call(
                "drug_exposure_lookup",
                success=True,
                result_summary=f"{len(exposures)} exposures",
                execution_time_ms=elapsed_ms,
            )

            return [self._drug_exposure_to_dict(de) for de in exposures]

        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            error_msg = str(e)
            self.context.record_tool_call(
                "drug_exposure_lookup",
                success=False,
                error=error_msg,
                execution_time_ms=elapsed_ms,
            )
            self.context.record_error(error_msg)
            return []

    async def execute_eligibility_prediction_lookup(
        self,
        patient_id: str,
        trial_id: str,
    ) -> dict[str, Any] | None:
        """Look up eligibility prediction.

        Args:
            patient_id: Patient UUID
            trial_id: Trial UUID

        Returns:
            Prediction dict or None
        """
        start_time = time.time()
        try:
            from uuid import UUID

            from pharma_os.db.repositories.prediction_repository import PredictionRepository

            repo = PredictionRepository(self.session)

            try:
                patient_uuid = UUID(patient_id)
                trial_uuid = UUID(trial_id)
            except (ValueError, TypeError):
                return None

            predictions = repo.get_eligibility_predictions(patient_uuid, trial_uuid)
            elapsed_ms = (time.time() - start_time) * 1000

            if predictions:
                latest = predictions[0]
                self.context.record_tool_call(
                    "eligibility_prediction_lookup",
                    success=True,
                    result_summary="Prediction found",
                    execution_time_ms=elapsed_ms,
                )
                return {
                    "probability": float(latest.probability) if hasattr(latest, "probability") else None,
                    "created_at": str(latest.created_at) if hasattr(latest, "created_at") else None,
                }
            else:
                self.context.record_tool_call(
                    "eligibility_prediction_lookup",
                    success=True,
                    result_summary="No predictions",
                    execution_time_ms=elapsed_ms,
                )
                return None

        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            error_msg = str(e)
            logger.debug(f"Eligibility prediction lookup error: {error_msg}")
            return None

    @staticmethod
    def _patient_to_dict(patient: Any) -> dict[str, Any]:
        """Convert patient model to dict."""
        return {
            "id": str(patient.id),
            "external_patient_id": patient.external_patient_id,
            "age": patient.age,
            "sex": str(patient.sex),
            "primary_condition": patient.primary_condition,
            "diagnosis_code": patient.diagnosis_code,
            "comorbidity_summary": patient.comorbidity_summary,
            "enrollment_status": str(patient.enrollment_status),
            "is_active": patient.is_active,
        }

    @staticmethod
    def _trial_to_dict(trial: Any) -> dict[str, Any]:
        """Convert trial model to dict."""
        return {
            "id": str(trial.id),
            "trial_code": trial.trial_code,
            "title": trial.title,
            "indication": trial.indication,
            "phase": str(trial.phase),
            "status": str(trial.status),
            "sponsor": trial.sponsor,
            "inclusion_criteria_ref": trial.inclusion_criteria_ref,
            "exclusion_criteria_ref": trial.exclusion_criteria_ref,
            "recruitment_target": trial.recruitment_target,
            "enrolled_count": trial.enrolled_count,
        }

    @staticmethod
    def _adverse_event_to_dict(ae: Any) -> dict[str, Any]:
        """Convert adverse event model to dict."""
        return {
            "event_type": ae.event_type if hasattr(ae, "event_type") else None,
            "event_date": str(ae.event_date) if hasattr(ae, "event_date") else None,
            "severity": ae.severity.value if hasattr(ae, "severity") else None,
            "is_serious": ae.is_serious if hasattr(ae, "is_serious") else False,
            "description": ae.description if hasattr(ae, "description") else None,
        }

    @staticmethod
    def _drug_exposure_to_dict(de: Any) -> dict[str, Any]:
        """Convert drug exposure model to dict."""
        return {
            "drug_name": de.drug_name if hasattr(de, "drug_name") else None,
            "start_date": str(de.start_date) if hasattr(de, "start_date") else None,
            "end_date": str(de.end_date) if hasattr(de, "end_date") else None,
            "is_active": de.is_active if hasattr(de, "is_active") else False,
            "route": de.route if hasattr(de, "route") else None,
        }
