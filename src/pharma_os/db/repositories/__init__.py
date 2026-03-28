"""Canonical repository exports for PHARMA-OS persistence layer."""

from pharma_os.db.repositories.adverse_event_repository import AdverseEventRepository
from pharma_os.db.repositories.audit_log_repository import AuditLogRepository
from pharma_os.db.repositories.base import BaseRepository
from pharma_os.db.repositories.drug_exposure_repository import DrugExposureRepository
from pharma_os.db.repositories.patient_repository import PatientRepository
from pharma_os.db.repositories.prediction_repository import (
    EligibilityPredictionRepository,
    SafetyPredictionRepository,
)
from pharma_os.db.repositories.recruitment_repository import RecruitmentRepository
from pharma_os.db.repositories.trial_repository import TrialRepository

__all__ = [
    "BaseRepository",
    "PatientRepository",
    "TrialRepository",
    "AdverseEventRepository",
    "DrugExposureRepository",
    "EligibilityPredictionRepository",
    "SafetyPredictionRepository",
    "RecruitmentRepository",
    "AuditLogRepository",
]
