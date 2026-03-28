"""Validation specifications and reusable quality gate utilities."""

from pharma_os.pipelines.validation.base import ValidationSpec, validate_and_enforce
from pharma_os.pipelines.validation.domains import (
    ADVERSE_EVENTS_VALIDATION_SPEC,
    DRUG_EXPOSURES_VALIDATION_SPEC,
    PATIENTS_VALIDATION_SPEC,
    TRIALS_VALIDATION_SPEC,
)

__all__ = [
    "ValidationSpec",
    "validate_and_enforce",
    "PATIENTS_VALIDATION_SPEC",
    "TRIALS_VALIDATION_SPEC",
    "ADVERSE_EVENTS_VALIDATION_SPEC",
    "DRUG_EXPOSURES_VALIDATION_SPEC",
]
