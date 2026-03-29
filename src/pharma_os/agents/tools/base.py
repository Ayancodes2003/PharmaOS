"""Tool implementations for agent use."""

from __future__ import annotations

import logging
from uuid import UUID
from typing import Any

from pharma_os.agents.base.tools import Tool, ToolResult

logger = logging.getLogger(__name__)


class PatientLookupTool(Tool):
    """Tool for looking up patient information."""

    def get_name(self) -> str:
        """Get tool name."""
        return "patient_lookup"

    def get_description(self) -> str:
        """Get tool description."""
        return "Retrieve patient profile information by ID or external ID (demographics, condition, enrollment status)"

    async def execute(self, args: dict[str, Any]) -> ToolResult:
        """Execute patient lookup.

        Args:
            args: Must contain 'patient_id' or 'external_patient_id'

        Returns:
            ToolResult with patient data
        """
        try:
            from pharma_os.db.repositories.patient_repository import PatientRepository

            session = args.get("session")
            if not session:
                return ToolResult(success=False, error="session is required")

            # Get patient_id or external_patient_id from args
            patient_id = args.get("patient_id")
            external_patient_id = args.get("external_patient_id")

            if not patient_id and not external_patient_id:
                return ToolResult(
                    success=False,
                    error="Must provide patient_id or external_patient_id",
                )

            patient_repo = PatientRepository(session)
            patient = None
            if patient_id:
                try:
                    patient = patient_repo.get(UUID(str(patient_id)))
                except (ValueError, TypeError):
                    patient = patient_repo.get_by_external_patient_id(str(patient_id))
            if not patient and external_patient_id:
                patient = patient_repo.get_by_external_patient_id(str(external_patient_id))

            if not patient:
                return ToolResult(success=False, error="Patient not found")

            return ToolResult(
                success=True,
                data={
                    "patient": patient,
                },
                message=f"Patient lookup for {patient.external_patient_id}",
            )

        except Exception as e:
            logger.error(f"Error in patient_lookup: {e}")
            return ToolResult(success=False, error=str(e))


class TrialLookupTool(Tool):
    """Tool for looking up trial information."""

    def get_name(self) -> str:
        """Get tool name."""
        return "trial_lookup"

    def get_description(self) -> str:
        """Get tool description."""
        return "Retrieve trial information by ID or trial code (title, indication, phase, status, criteria references)"

    async def execute(self, args: dict[str, Any]) -> ToolResult:
        """Execute trial lookup.

        Args:
            args: Must contain 'trial_id' or 'trial_code'

        Returns:
            ToolResult with trial data
        """
        try:
            from pharma_os.db.repositories.trial_repository import TrialRepository

            session = args.get("session")
            if not session:
                return ToolResult(success=False, error="session is required")

            trial_id = args.get("trial_id")
            trial_code = args.get("trial_code")

            if not trial_id and not trial_code:
                return ToolResult(
                    success=False,
                    error="Must provide trial_id or trial_code",
                )

            trial_repo = TrialRepository(session)
            trial = None
            if trial_id:
                try:
                    trial = trial_repo.get(UUID(str(trial_id)))
                except (ValueError, TypeError):
                    trial = trial_repo.get_by_trial_code(str(trial_id))
            if not trial and trial_code:
                trial = trial_repo.get_by_trial_code(str(trial_code))

            if not trial:
                return ToolResult(success=False, error="Trial not found")

            return ToolResult(
                success=True,
                data={
                    "trial": trial,
                },
                message=f"Trial lookup for {trial.trial_code}",
            )

        except Exception as e:
            logger.error(f"Error in trial_lookup: {e}")
            return ToolResult(success=False, error=str(e))


class AdverseEventLookupTool(Tool):
    """Tool for looking up adverse events."""

    def get_name(self) -> str:
        """Get tool name."""
        return "adverse_event_lookup"

    def get_description(self) -> str:
        """Get tool description."""
        return "Retrieve adverse events for a patient (event type, date, severity, seriousness)"

    async def execute(self, args: dict[str, Any]) -> ToolResult:
        """Execute adverse event lookup.

        Args:
            args: Must contain 'patient_id'

        Returns:
            ToolResult with adverse event data
        """
        try:
            from pharma_os.db.repositories.adverse_event_repository import AdverseEventRepository

            session = args.get("session")
            if not session:
                return ToolResult(success=False, error="session is required")

            patient_id = args.get("patient_id")
            limit = args.get("limit", 20)

            if not patient_id:
                return ToolResult(
                    success=False,
                    error="Must provide patient_id",
                )

            adverse_event_repo = AdverseEventRepository(session)
            events = adverse_event_repo.list_by_patient(UUID(str(patient_id)), limit=int(limit))

            return ToolResult(
                success=True,
                data={
                    "patient_id": patient_id,
                    "events": events,
                    "serious_count": sum(1 for event in events if event.is_serious),
                    "event_count": len(events),
                },
                message=f"Adverse events for patient {patient_id}",
            )

        except Exception as e:
            logger.error(f"Error in adverse_event_lookup: {e}")
            return ToolResult(success=False, error=str(e))


class DrugExposureLookupTool(Tool):
    """Tool for looking up drug exposures."""

    def get_name(self) -> str:
        """Get tool name."""
        return "drug_exposure_lookup"

    def get_description(self) -> str:
        """Get tool description."""
        return "Retrieve current and past drug exposures for a patient (drug name, dates, route, status)"

    async def execute(self, args: dict[str, Any]) -> ToolResult:
        """Execute drug exposure lookup.

        Args:
            args: Must contain 'patient_id'

        Returns:
            ToolResult with drug exposure data
        """
        try:
            from pharma_os.db.repositories.drug_exposure_repository import DrugExposureRepository

            session = args.get("session")
            if not session:
                return ToolResult(success=False, error="session is required")

            patient_id = args.get("patient_id")
            limit = args.get("limit", 20)

            if not patient_id:
                return ToolResult(
                    success=False,
                    error="Must provide patient_id",
                )

            drug_exposure_repo = DrugExposureRepository(session)
            exposures = drug_exposure_repo.list_by_patient(UUID(str(patient_id)), limit=int(limit))

            return ToolResult(
                success=True,
                data={
                    "patient_id": patient_id,
                    "exposures": exposures,
                    "active_count": sum(1 for exposure in exposures if exposure.is_active),
                    "total_count": len(exposures),
                },
                message=f"Drug exposures for patient {patient_id}",
            )

        except Exception as e:
            logger.error(f"Error in drug_exposure_lookup: {e}")
            return ToolResult(success=False, error=str(e))


class PredictionLookupTool(Tool):
    """Tool for looking up prediction outputs."""

    def get_name(self) -> str:
        """Get tool name."""
        return "prediction_lookup"

    def get_description(self) -> str:
        """Get tool description."""
        return "Retrieve model predictions for eligibility, safety, or recruitment (probability, risk class, ranking)"

    async def execute(self, args: dict[str, Any]) -> ToolResult:
        """Execute prediction lookup.

        Args:
            args: Must contain 'prediction_type' (eligibility|safety|recruitment) and 'patient_id' or 'trial_id'

        Returns:
            ToolResult with prediction data
        """
        try:
            from pharma_os.db.repositories.prediction_repository import (
                EligibilityPredictionRepository,
                SafetyPredictionRepository,
            )

            session = args.get("session")
            if not session:
                return ToolResult(success=False, error="session is required")

            prediction_type = args.get("prediction_type")
            patient_id = args.get("patient_id")
            trial_id = args.get("trial_id")
            drug_exposure_id = args.get("drug_exposure_id")

            if not prediction_type:
                return ToolResult(
                    success=False,
                    error="Must provide prediction_type (eligibility|safety|recruitment)",
                )

            if prediction_type == "eligibility" and (not patient_id or not trial_id):
                return ToolResult(
                    success=False,
                    error="Eligibility predictions require patient_id and trial_id",
                )

            prediction_payload: dict[str, Any] | None = None
            if prediction_type == "eligibility":
                repo = EligibilityPredictionRepository(session)
                prediction = repo.latest_for_patient_trial(UUID(str(patient_id)), UUID(str(trial_id)))
                if prediction:
                    prediction_payload = {
                        "probability": float(prediction.probability) if hasattr(prediction, "probability") else None,
                        "inference_timestamp": str(prediction.inference_timestamp)
                        if hasattr(prediction, "inference_timestamp")
                        else None,
                    }
            elif prediction_type == "safety":
                repo = SafetyPredictionRepository(session)
                prediction = repo.latest_for_patient_exposure(
                    UUID(str(patient_id)),
                    UUID(str(drug_exposure_id)) if drug_exposure_id else None,
                )
                if prediction:
                    prediction_payload = {
                        "risk_probability": float(prediction.risk_probability)
                        if hasattr(prediction, "risk_probability")
                        else None,
                        "risk_class": str(prediction.risk_class)
                        if hasattr(prediction, "risk_class")
                        else None,
                        "inference_timestamp": str(prediction.inference_timestamp)
                        if hasattr(prediction, "inference_timestamp")
                        else None,
                    }

            return ToolResult(
                success=True,
                data={
                    "prediction_type": prediction_type,
                    "patient_id": patient_id,
                    "trial_id": trial_id,
                    "prediction": prediction_payload,
                },
                message=f"{prediction_type} prediction lookup",
            )

        except Exception as e:
            logger.error(f"Error in prediction_lookup: {e}")
            return ToolResult(success=False, error=str(e))


class DocumentRetrievalTool(Tool):
    """Tool for document/criteria retrieval (stub, ready for RAG)."""

    def get_name(self) -> str:
        """Get tool name."""
        return "document_retrieval"

    def get_description(self) -> str:
        """Get tool description."""
        return "Retrieve trial criteria documents, literature references, or research documents (extensible for RAG)"

    async def execute(self, args: dict[str, Any]) -> ToolResult:
        """Execute document retrieval.

        Args:
            args: Must contain 'document_type' and 'query' or 'trial_id'

        Returns:
            ToolResult with document data
        """
        try:
            from pharma_os.db.repositories.trial_repository import TrialRepository

            session = args.get("session")
            document_type = args.get("document_type", "trial_criteria")
            trial_id = args.get("trial_id")
            query = args.get("query")

            if not trial_id and not query:
                return ToolResult(
                    success=False,
                    error="Must provide trial_id or query",
                )

            documents: list[dict[str, Any]] = []
            if trial_id and session:
                trial_repo = TrialRepository(session)
                trial = None
                try:
                    trial = trial_repo.get(UUID(str(trial_id)))
                except (ValueError, TypeError):
                    trial = trial_repo.get_by_trial_code(str(trial_id))

                if trial:
                    if trial.inclusion_criteria_ref:
                        documents.append({"type": "inclusion", "reference": trial.inclusion_criteria_ref})
                    if trial.exclusion_criteria_ref:
                        documents.append({"type": "exclusion", "reference": trial.exclusion_criteria_ref})

            return ToolResult(
                success=True,
                data={
                    "document_type": document_type,
                    "documents": documents,
                    "query": query,
                },
                message=f"Document retrieval for {document_type}",
            )

        except Exception as e:
            logger.error(f"Error in document_retrieval: {e}")
            return ToolResult(success=False, error=str(e))
