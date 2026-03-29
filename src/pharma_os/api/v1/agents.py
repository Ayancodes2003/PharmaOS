"""Agent orchestration API routes."""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, status

from pharma_os.agents.base import (
    EligibilityAnalysisResult,
    EligibilityAnalystRequest,
    ResearchSummarizerRequest,
    ResearchSummaryResult,
    SafetyInvestigationResult,
    SafetyInvestigatorRequest,
)
from pharma_os.agents.orchestration import AgentExecutor
from pharma_os.api.dependencies import get_agent_executor, get_postgres_session_dependency
from pharma_os.api.schemas.agents import AgentExecutionMetadata, AgentExecutionPayload
from pharma_os.api.schemas.responses import SuccessResponse
from sqlalchemy.orm import Session

router = APIRouter(prefix="/agents", tags=["agents"])


def _ensure_trace_id(trace_id: str | None) -> str:
    return trace_id or str(uuid4())


@router.post(
    "/eligibility-analyst",
    response_model=SuccessResponse[AgentExecutionPayload[EligibilityAnalysisResult]],
    status_code=status.HTTP_200_OK,
)
async def run_eligibility_analyst(
    request: EligibilityAnalystRequest,
    executor: AgentExecutor = Depends(get_agent_executor),
    session: Session = Depends(get_postgres_session_dependency),
) -> SuccessResponse[AgentExecutionPayload[EligibilityAnalysisResult]]:
    """Run grounded trial eligibility analyst agent and persist trace."""
    request.trace_id = _ensure_trace_id(request.trace_id)
    result, metadata = await executor.execute(request, session)

    payload = AgentExecutionPayload[EligibilityAnalysisResult](
        result=result,
        execution=AgentExecutionMetadata(**metadata),
    )
    return SuccessResponse(message="eligibility analyst completed", data=payload)


@router.post(
    "/safety-investigator",
    response_model=SuccessResponse[AgentExecutionPayload[SafetyInvestigationResult]],
    status_code=status.HTTP_200_OK,
)
async def run_safety_investigator(
    request: SafetyInvestigatorRequest,
    executor: AgentExecutor = Depends(get_agent_executor),
    session: Session = Depends(get_postgres_session_dependency),
) -> SuccessResponse[AgentExecutionPayload[SafetyInvestigationResult]]:
    """Run grounded safety signal investigator agent and persist trace."""
    request.trace_id = _ensure_trace_id(request.trace_id)
    result, metadata = await executor.execute(request, session)

    payload = AgentExecutionPayload[SafetyInvestigationResult](
        result=result,
        execution=AgentExecutionMetadata(**metadata),
    )
    return SuccessResponse(message="safety investigator completed", data=payload)


@router.post(
    "/research-summarizer",
    response_model=SuccessResponse[AgentExecutionPayload[ResearchSummaryResult]],
    status_code=status.HTTP_200_OK,
)
async def run_research_summarizer(
    request: ResearchSummarizerRequest,
    executor: AgentExecutor = Depends(get_agent_executor),
    session: Session = Depends(get_postgres_session_dependency),
) -> SuccessResponse[AgentExecutionPayload[ResearchSummaryResult]]:
    """Run grounded research summarization agent and persist trace."""
    request.trace_id = _ensure_trace_id(request.trace_id)
    result, metadata = await executor.execute(request, session)

    payload = AgentExecutionPayload[ResearchSummaryResult](
        result=result,
        execution=AgentExecutionMetadata(**metadata),
    )
    return SuccessResponse(message="research summarizer completed", data=payload)
