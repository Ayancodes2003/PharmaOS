"""Tool registry and initialization."""

from __future__ import annotations

from pharma_os.agents.base.tools import ToolRegistry
from pharma_os.agents.tools.base import (
    AdverseEventLookupTool,
    DocumentRetrievalTool,
    DrugExposureLookupTool,
    PatientLookupTool,
    PredictionLookupTool,
    TrialLookupTool,
)


def create_default_tool_registry() -> ToolRegistry:
    """Create registry with all default tools.

    Returns:
        ToolRegistry with all tools registered
    """
    registry = ToolRegistry()
    registry.register(PatientLookupTool())
    registry.register(TrialLookupTool())
    registry.register(AdverseEventLookupTool())
    registry.register(DrugExposureLookupTool())
    registry.register(PredictionLookupTool())
    registry.register(DocumentRetrievalTool())
    return registry


__all__ = [
    "PatientLookupTool",
    "TrialLookupTool",
    "AdverseEventLookupTool",
    "DrugExposureLookupTool",
    "PredictionLookupTool",
    "DocumentRetrievalTool",
    "create_default_tool_registry",
]
