"""Research summarization agent for trial and literature synthesis."""

from __future__ import annotations

import logging
import time
from typing import Any

from pharma_os.agents.base import (
    BaseAgent,
    ExecutionContext,
    ResearchSummarizerRequest,
    ResearchSummaryResult,
)
from pharma_os.agents.llm.provider import Message
from pharma_os.agents.prompts import PromptRegistry

logger = logging.getLogger(__name__)


class ResearchSummarizerAgent(BaseAgent):
    """Agent for research synthesis and document summarization."""

    def __init__(
        self,
        llm_provider: Any,
        prompt_registry: PromptRegistry,
    ):
        """Initialize research summarizer agent.

        Args:
            llm_provider: LLM provider instance
            prompt_registry: Prompt registry for system prompts
        """
        super().__init__(llm_provider)
        self.prompt_registry = prompt_registry

    async def execute(
        self,
        request: ResearchSummarizerRequest,
        context: ExecutionContext,
    ) -> ResearchSummaryResult:
        """Execute research summarization.

        Summarizes trial information, criteria documents, and research context
        to produce structured research summary with key takeaways.

        Args:
            request: Research summarization request
            context: Execution context with session and settings

        Returns:
            ResearchSummaryResult with structured research summary
        """
        start_time = time.time()

        try:
            # Determine context type and retrieve relevant information
            context_summary = ""
            document_references = []

            if request.context_type == "trial" and request.trial_id:
                context_summary, document_references = await self._summarize_trial_context(
                    request.trial_id,
                    context,
                )
            elif request.context_type == "literature" and request.query:
                context_summary, document_references = await self._summarize_literature_context(
                    request.query,
                    context,
                )
            elif request.context_type == "disease" and request.query:
                context_summary, document_references = await self._summarize_disease_context(
                    request.query,
                )
            elif request.context_type == "drug" and request.query:
                context_summary, document_references = await self._summarize_drug_context(
                    request.query,
                )
            else:
                context_summary = "Research context not specified or invalid."

            # Get system prompt
            system_prompt = self.prompt_registry.get_prompt_or_default(
                "research_summarizer",
                "You are a clinical research summarizer.",
            )

            # Prepare analysis messages
            messages = []
            messages.append(
                Message(
                    "user",
                    f"Context: {context_summary}",
                )
            )
            if request.query:
                messages.append(Message("user", f"Summarize in context of this query: {request.query}"))

            # Call LLM for synthesis
            synthesis_text = await self.llm_provider.complete(
                messages=messages,
                system_prompt=system_prompt,
                temperature=0.6,  # Lower temperature for research accuracy
                max_tokens=2000,
            )

            # Extract key points
            key_points = self._extract_key_points(context_summary, synthesis_text.content)

            # Generate answer if query provided
            answer = None
            if request.query:
                answer = synthesis_text.content or self._default_query_answer(request.query, context_summary)

            # Build result
            result = ResearchSummaryResult(
                trace_id=context.trace_id,
                execution_time_ms=(time.time() - start_time) * 1000,
                success=True,
                context_summary=context_summary or synthesis_text.content or "Research context summarized.",
                key_points=key_points,
                research_question=request.query,
                answer=answer,
                document_references=document_references,
                extensibility_note="This research layer is extensible for RAG integration and broader literature indexing.",
            )

            return result

        except Exception as e:
            logger.error(f"Error in research summarization: {e}")
            execution_time_ms = (time.time() - start_time) * 1000
            return ResearchSummaryResult(
                trace_id=context.trace_id,
                execution_time_ms=execution_time_ms,
                success=False,
                error=str(e),
            )

    async def _summarize_trial_context(
        self,
        trial_id: str,
        context: ExecutionContext,
    ) -> tuple[str, list[str]]:
        """Summarize trial-specific research context.

        Args:
            trial_id: Trial UUID or trial code
            context: Execution context

        Returns:
            Tuple of (context_summary, document_references)
        """
        trial_data = await context.invoke_tool(
            "trial_lookup",
            {
                "session": context.session,
                "trial_id": trial_id,
                "trial_code": trial_id,
            },
        )
        trial = trial_data.get("trial") if trial_data else None

        if not trial:
            return f"Trial not found: {trial_id}", []

        # Build trial context
        summary_parts = [
            f"Trial: {trial.trial_code} - {trial.title}",
            f"Indication: {trial.indication}",
            f"Phase: {trial.phase}",
            f"Status: {trial.status}",
            f"Sponsor: {trial.sponsor}",
            f"Study Summary: {trial.study_summary or 'No summary available'}",
            f"Recruitment: {trial.enrolled_count}/{trial.recruitment_target or 'N/A'} enrolled",
        ]

        if trial.inclusion_criteria_ref:
            summary_parts.append(f"Inclusion Criteria Ref: {trial.inclusion_criteria_ref}")

        if trial.exclusion_criteria_ref:
            summary_parts.append(f"Exclusion Criteria Ref: {trial.exclusion_criteria_ref}")

        summary = "\n".join(summary_parts)

        # Build document references
        refs = [trial.trial_code]
        if trial.inclusion_criteria_ref:
            refs.append(f"criteria:{trial.inclusion_criteria_ref}")
        if trial.exclusion_criteria_ref:
            refs.append(f"criteria:{trial.exclusion_criteria_ref}")

        doc_data = await context.invoke_tool(
            "document_retrieval",
            {
                "session": context.session,
                "trial_id": trial_id,
                "document_type": "trial_criteria",
            },
        )
        if doc_data and doc_data.get("documents"):
            refs.extend([f"doc:{doc.get('reference')}" for doc in doc_data["documents"] if doc.get("reference")])

        return summary, refs

    async def _summarize_literature_context(
        self,
        query: str,
        context: ExecutionContext,
    ) -> tuple[str, list[str]]:
        """Summarize literature research context.

        Args:
            query: Research query
            context: Execution context

        Returns:
            Tuple of (context_summary, document_references)
        """
        # This is a stub ready for RAG integration
        summary = (
            f"Literature search context for: {query}\n"
            f"Document retrieval layer is operational and ready for RAG integration.\n"
            f"Future: Full-text search, vector similarity, relevance ranking will be available."
        )

        refs = [f"query:{query}"]

        return summary, refs

    async def _summarize_disease_context(self, query: str) -> tuple[str, list[str]]:
        """Summarize disease-related research context.

        Args:
            query: Disease query

        Returns:
            Tuple of (context_summary, document_references)
        """
        # Stub for disease context
        summary = (
            f"Disease context: {query}\n"
            f"Disease-specific research framework is in place.\n"
            f"Extensible for literature integration and clinical guidelines."
        )

        refs = [f"disease:{query}"]

        return summary, refs

    async def _summarize_drug_context(self, query: str) -> tuple[str, list[str]]:
        """Summarize drug-related research context.

        Args:
            query: Drug query

        Returns:
            Tuple of (context_summary, document_references)
        """
        # Stub for drug context
        summary = (
            f"Drug context: {query}\n"
            f"Drug-specific research framework is operational.\n"
            f"Extensible for pharmacology data, interactions, and pharmacovigilance integration."
        )

        refs = [f"drug:{query}"]

        return summary, refs

    def _extract_key_points(self, context: str, synthesis: str | None = None) -> list[str]:
        """Extract key points from context and synthesis.

        Args:
            context: Context summary
            synthesis: LLM synthesis output

        Returns:
            List of key points
        """
        key_points = []

        # Extract from context
        if "indication" in context.lower():
            lines = context.split("\n")
            for line in lines:
                if "indication" in line.lower() or "phase" in line.lower() or "status" in line.lower():
                    key_points.append(line.strip())

        # Extract from synthesis if available
        if synthesis:
            # Simple heuristic: split by sentences and take first 3-5
            sentences = [s.strip() for s in synthesis.split(".") if s.strip()]
            key_points.extend(sentences[:3])

        return key_points[:5]  # Return top 5

    def _default_query_answer(self, query: str, context: str) -> str:
        """Generate default answer if LLM unavailable.

        Args:
            query: Research query
            context: Research context

        Returns:
            Default answer string
        """
        return (
            f"Query: {query}\n"
            f"Available context: {context[:200]}\n"
            f"Research framework is operational. Full LLM synthesis available when API key configured."
        )
