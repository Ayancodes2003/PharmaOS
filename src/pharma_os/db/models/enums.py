"""Domain enumerations for PHARMA-OS structured entities."""

from __future__ import annotations

from enum import Enum


class PatientSex(str, Enum):
    """Patient sex category used for demographic stratification."""

    FEMALE = "female"
    MALE = "male"
    INTERSEX = "intersex"
    OTHER = "other"
    UNKNOWN = "unknown"


class EnrollmentStatus(str, Enum):
    """Patient enrollment state in the PHARMA-OS platform context."""

    CANDIDATE = "candidate"
    ENROLLED = "enrolled"
    SCREEN_FAILED = "screen_failed"
    WITHDRAWN = "withdrawn"
    COMPLETED = "completed"


class TrialPhase(str, Enum):
    """Clinical trial development phase."""

    PHASE_1 = "phase_1"
    PHASE_2 = "phase_2"
    PHASE_3 = "phase_3"
    PHASE_4 = "phase_4"
    EARLY_PHASE = "early_phase"
    NOT_APPLICABLE = "not_applicable"


class TrialStatus(str, Enum):
    """Operational status of a trial."""

    PLANNING = "planning"
    RECRUITING = "recruiting"
    ACTIVE_NOT_RECRUITING = "active_not_recruiting"
    COMPLETED = "completed"
    TERMINATED = "terminated"
    SUSPENDED = "suspended"


class AdverseEventSeverity(str, Enum):
    """Clinical severity grading for adverse events."""

    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    LIFE_THREATENING = "life_threatening"
    DEATH = "death"


class AdverseEventOutcome(str, Enum):
    """Patient outcome from the adverse event report."""

    RESOLVED = "resolved"
    RESOLVING = "resolving"
    ONGOING = "ongoing"
    FATAL = "fatal"
    UNKNOWN = "unknown"


class SafetyRiskClass(str, Enum):
    """Safety model output classes."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class ActorType(str, Enum):
    """Actor category for audit logging."""

    SYSTEM = "system"
    USER = "user"
    SERVICE = "service"
    AGENT = "agent"
