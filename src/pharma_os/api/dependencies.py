"""Shared FastAPI dependency helpers."""

from functools import lru_cache
from collections.abc import Generator

from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from sqlalchemy.orm import Session

from pharma_os.agents.orchestration import AgentDispatcher, AgentExecutor
from pharma_os.agents.persistence import TraceStore
from pharma_os.core.settings import Settings, get_settings
from pharma_os.db.mongo import get_mongo_database
from pharma_os.db.repositories import (
    AdverseEventRepository,
    DrugExposureRepository,
    PatientRepository,
    RecruitmentRepository,
    TrialRepository,
)
from pharma_os.db.postgres import get_db_session
from pharma_os.services.prediction_services import (
    EligibilityPredictionService,
    RecruitmentRankingService,
    SafetyPredictionService,
)


def get_app_settings() -> Settings:
    """Dependency provider for typed runtime settings."""
    return get_settings()


def get_postgres_session_dependency() -> Generator[Session, None, None]:
    """Dependency provider for PostgreSQL session."""
    yield from get_db_session()


def get_mongo_database_dependency() -> AsyncIOMotorDatabase:
    """Dependency provider for MongoDB database handle."""
    return get_mongo_database()


def get_patient_repository(
    session: Session = Depends(get_postgres_session_dependency),
) -> PatientRepository:
    """Dependency provider for patient repository."""
    return PatientRepository(session)


def get_trial_repository(
    session: Session = Depends(get_postgres_session_dependency),
) -> TrialRepository:
    """Dependency provider for trial repository."""
    return TrialRepository(session)


def get_adverse_event_repository(
    session: Session = Depends(get_postgres_session_dependency),
) -> AdverseEventRepository:
    """Dependency provider for adverse event repository."""
    return AdverseEventRepository(session)


def get_drug_exposure_repository(
    session: Session = Depends(get_postgres_session_dependency),
) -> DrugExposureRepository:
    """Dependency provider for drug exposure repository."""
    return DrugExposureRepository(session)


def get_recruitment_repository(
    session: Session = Depends(get_postgres_session_dependency),
) -> RecruitmentRepository:
    """Dependency provider for recruitment repository."""
    return RecruitmentRepository(session)


def get_eligibility_prediction_service(
    session: Session = Depends(get_postgres_session_dependency),
    settings: Settings = Depends(get_app_settings),
) -> EligibilityPredictionService:
    """Dependency provider for eligibility inference service."""
    return EligibilityPredictionService(session=session, settings=settings)


def get_safety_prediction_service(
    session: Session = Depends(get_postgres_session_dependency),
    settings: Settings = Depends(get_app_settings),
) -> SafetyPredictionService:
    """Dependency provider for safety inference service."""
    return SafetyPredictionService(session=session, settings=settings)


def get_recruitment_ranking_service(
    session: Session = Depends(get_postgres_session_dependency),
    settings: Settings = Depends(get_app_settings),
) -> RecruitmentRankingService:
    """Dependency provider for recruitment ranking service."""
    return RecruitmentRankingService(session=session, settings=settings)


@lru_cache(maxsize=1)
def _cached_agent_dispatcher() -> AgentDispatcher:
    """Singleton-like dispatcher for route-level agent execution."""
    return AgentDispatcher(get_settings())


def get_agent_dispatcher() -> AgentDispatcher:
    """Dependency provider for agent dispatcher."""
    return _cached_agent_dispatcher()


def get_agent_executor(
    dispatcher: AgentDispatcher = Depends(get_agent_dispatcher),
) -> AgentExecutor:
    """Dependency provider for agent executor with trace persistence."""
    return AgentExecutor(dispatcher=dispatcher, trace_store=TraceStore())
