"""Canonical database layer exports for PHARMA-OS."""

from collections.abc import Callable
from typing import Any

from pharma_os.db.models import (
    AdverseEvent,
    AuditLog,
    Base,
    DrugExposure,
    EligibilityPrediction,
    Patient,
    RecruitmentRanking,
    SafetyPrediction,
    Trial,
    target_metadata,
)


def _unavailable(*_: Any, **__: Any) -> Any:
    raise ModuleNotFoundError(
        "MongoDB collection access requires optional dependency 'motor'. "
        "Install project dependencies in the active virtual environment."
    )


try:
    from pharma_os.db.mongo_collections import (
        COLLECTIONS,
        MongoCollectionNames,
        get_agent_memory_collection,
        get_agent_traces_collection,
        get_clinical_notes_collection,
        get_literature_chunks_collection,
        get_trial_criteria_docs_collection,
    )
except ModuleNotFoundError:
    COLLECTIONS = None
    MongoCollectionNames = None
    get_agent_memory_collection: Callable[..., Any] = _unavailable
    get_agent_traces_collection: Callable[..., Any] = _unavailable
    get_clinical_notes_collection: Callable[..., Any] = _unavailable
    get_literature_chunks_collection: Callable[..., Any] = _unavailable
    get_trial_criteria_docs_collection: Callable[..., Any] = _unavailable

__all__ = [
    "Base",
    "target_metadata",
    "Patient",
    "Trial",
    "AdverseEvent",
    "DrugExposure",
    "EligibilityPrediction",
    "SafetyPrediction",
    "RecruitmentRanking",
    "AuditLog",
    "MongoCollectionNames",
    "COLLECTIONS",
    "get_clinical_notes_collection",
    "get_trial_criteria_docs_collection",
    "get_literature_chunks_collection",
    "get_agent_memory_collection",
    "get_agent_traces_collection",
]
