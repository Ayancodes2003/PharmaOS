"""Research summarization agent for literature analysis."""

from __future__ import annotations

import logging
from typing import Any

from pharma_os.agents.base import AgentBase, ResearchSummaryResult
from pharma_os.agents.core.context import AgentExecutionContext
from pharma_os.agents.core.result_builders import ResearchResultBuilder


logger = logging.getLogger(__name__)


class ResearchAgent(AgentBase):
    """Agent for summarizing and analyzing research literature."""

    def __init__(self):
        """Initialize research agent."""
        super().__init__()
        self.agent_type = "research_summarization"

    def execute(self, context: AgentExecutionContext) -> ResearchSummaryResult:
        """Execute research summarization.

        Args:
            context: Execution context with research data and question

        Returns:
            Research summary result
        """
        logger.info(f"Starting research analysis (Trace: {context.trace_id})")

        builder = ResearchResultBuilder(context)

        try:
            # Extract research question
            research_question = context.get_input_data("research_question")
            if not research_question:
                return builder.build_result(
                    success=False,
                    error="No research question provided in context",
                )

            # Extract documents/context
            documents = context.get_input_data("documents")
            if not documents:
                return builder.build_result(
                    success=False,
                    error="No research documents provided in context",
                )

            # Generate context summary
            context_summary = self._generate_context_summary(documents)

            # Extract key points
            key_points = self._extract_key_points(documents)

            # Generate answer to research question
            answer = self._generate_answer(research_question, documents, key_points)

            # Gather document references
            references = self._gather_references(documents)

            # Generate extensibility note
            extensibility_note = self._generate_extensibility_note(research_question)

            logger.info(f"Research analysis completed for: {research_question}")

            return builder.build_result(
                success=True,
                context_summary=context_summary,
                key_points=key_points,
                research_question=research_question,
                answer=answer,
                document_references=references,
                extensibility_note=extensibility_note,
            )

        except Exception as e:
            logger.error(f"Research analysis failed: {str(e)}", exc_info=True)
            return builder.build_result(
                success=False,
                error=f"Analysis failed: {str(e)}",
            )

    def _generate_context_summary(self, documents: Any) -> str:
        """Generate summary of research context.

        Args:
            documents: Research documents or data

        Returns:
            Context summary
        """
        if isinstance(documents, str):
            # Simple string context
            if len(documents) > 200:
                return documents[:200] + "..."
            return documents

        elif isinstance(documents, list):
            # List of documents
            summary_parts = []

            for i, doc in enumerate(documents[:3]):  # Summarize first 3 docs
                if isinstance(doc, dict):
                    if "title" in doc:
                        summary_parts.append(f"- {doc['title']}")
                    elif "content" in doc:
                        content = doc["content"]
                        preview = content[:100] + "..." if len(content) > 100 else content
                        summary_parts.append(f"- {preview}")
                else:
                    summary_parts.append(f"- {str(doc)[:100]}")

            if summary_parts:
                return (
                    f"Analyzed {len(documents)} document(s):\n"
                    + "\n".join(summary_parts)
                )

        elif isinstance(documents, dict):
            # Dictionary of documents
            parts = []
            for key, value in list(documents.items())[:3]:
                if isinstance(value, str):
                    preview = value[:80] + "..." if len(value) > 80 else value
                    parts.append(f"- {key}: {preview}")
                else:
                    parts.append(f"- {key}: {str(value)[:80]}")
            return (
                f"Analyzed {len(documents)} source(s):\n" + "\n".join(parts)
            )

        return "Research context analyzed"

    def _extract_key_points(self, documents: Any) -> list[str]:
        """Extract key points from research.

        Args:
            documents: Research documents

        Returns:
            List of key points
        """
        key_points = []

        if isinstance(documents, str):
            # Extract sentences that might be key points
            sentences = documents.split(".")
            for sentence in sentences[:3]:  # First 3 sentences
                cleaned = sentence.strip()
                if len(cleaned) > 10:
                    key_points.append(cleaned)

        elif isinstance(documents, list):
            # Extract from list items
            for i, doc in enumerate(documents[:5]):
                if isinstance(doc, dict):
                    if "key_findings" in doc:
                        findings = doc["key_findings"]
                        if isinstance(findings, list):
                            key_points.extend(findings[:2])
                        else:
                            key_points.append(str(findings))
                    elif "summary" in doc:
                        key_points.append(doc["summary"])
                elif isinstance(doc, str):
                    if len(doc) > 50:
                        key_points.append(doc[:100] + "...")

        elif isinstance(documents, dict):
            # Extract from dict values
            for key, value in list(documents.items())[:5]:
                if isinstance(value, str) and len(value) > 30:
                    key_points.append(f"{key}: {value[:80]}")
                elif isinstance(value, list):
                    if value:
                        key_points.append(f"{key}: {len(value)} item(s)")

        return key_points[:5]  # Limit to 5 key points

    def _generate_answer(
        self, question: str, documents: Any, key_points: list[str]
    ) -> str:
        """Generate answer to research question.

        Args:
            question: Research question
            documents: Research documents
            key_points: Extracted key points

        Returns:
            Generated answer
        """
        answer_parts = []

        # Start with context
        answer_parts.append(
            f"Based on the analysis of the provided research materials "
            "addressing the question: '{question}'"
        )

        # Add key findings
        if key_points:
            answer_parts.append(f"\nThe analysis identified {len(key_points)} key points:")
            for point in key_points:
                answer_parts.append(f"• {point}")

        # Add conclusion
        if isinstance(documents, list) and len(documents) > 0:
            answer_parts.append(
                f"\nThese findings are drawn from {len(documents)} research source(s)."
            )
        elif isinstance(documents, dict) and len(documents) > 0:
            answer_parts.append(
                f"\nThese findings are drawn from {len(documents)} research domain(s)."
            )

        answer_parts.append(
            "\nFurther investigation may be warranted for more detailed analysis."
        )

        return "\n".join(answer_parts)

    def _gather_references(self, documents: Any) -> list[str]:
        """Gather reference citations.

        Args:
            documents: Research documents

        Returns:
            List of references
        """
        references = []

        if isinstance(documents, list):
            for i, doc in enumerate(documents):
                if isinstance(doc, dict):
                    if "reference" in doc:
                        references.append(doc["reference"])
                    elif "title" in doc:
                        references.append(f"[{i+1}] {doc['title']}")
                    elif "source" in doc:
                        references.append(f"[{i+1}] {doc['source']}")
                elif isinstance(doc, str):
                    references.append(f"[{i+1}] {doc[:60]}...")

        elif isinstance(documents, dict):
            for key, value in documents.items():
                if isinstance(value, dict) and "citation" in value:
                    references.append(value["citation"])
                else:
                    references.append(f"- {key}")

        return references[:10]  # Limit to 10 references

    def _generate_extensibility_note(self, research_question: str) -> str:
        """Generate note about extensibility for future queries.

        Args:
            research_question: Original research question

        Returns:
            Extensibility note
        """
        return (
            f"This analysis can be extended by: (1) Including additional research domains, "
            f"(2) Incorporating longitudinal data, (3) Cross-referencing with clinical outcomes, "
            f"(4) Applying advanced NLP techniques for deeper literature mining. "
            f"The framework supports iterative refinement for question: '{research_question}'"
        )
