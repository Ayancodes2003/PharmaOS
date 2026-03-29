"""Prompt registry and management system."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class PromptRegistry:
    """Registry for managing agent prompts."""

    def __init__(self):
        """Initialize prompt registry."""
        self._prompts: dict[str, str] = {}
        self._prompt_dir: Path | None = None

    def load_from_directory(self, prompt_dir: Path) -> None:
        """Load all markdown prompts from a directory.

        Args:
            prompt_dir: Path to directory containing .md prompt files
        """
        if not prompt_dir.exists():
            logger.warning(f"Prompt directory does not exist: {prompt_dir}")
            return

        self._prompt_dir = prompt_dir
        for prompt_file in prompt_dir.glob("*.md"):
            prompt_name = prompt_file.stem
            try:
                with open(prompt_file, "r", encoding="utf-8") as f:
                    content = f.read()
                self._prompts[prompt_name] = content
                logger.info(f"Loaded prompt: {prompt_name}")
            except Exception as e:
                logger.error(f"Error loading prompt {prompt_file}: {e}")

    def register_prompt(self, name: str, content: str) -> None:
        """Register a prompt by name and content.

        Args:
            name: Prompt name
            content: Prompt content string
        """
        self._prompts[name] = content

    def get_prompt(self, name: str) -> str | None:
        """Get prompt by name.

        Args:
            name: Prompt name

        Returns:
            Prompt content or None if not found
        """
        return self._prompts.get(name)

    def get_prompt_or_default(self, name: str, default: str = "") -> str:
        """Get prompt by name, with default fallback.

        Args:
            name: Prompt name
            default: Default content if not found

        Returns:
            Prompt content or default
        """
        return self._prompts.get(name, default)

    def list_available(self) -> list[str]:
        """List all available prompt names.

        Returns:
            List of prompt names
        """
        return list(self._prompts.keys())


# Default prompts (can be overridden by files)

DEFAULT_ELIGIBILITY_ANALYST_PROMPT = """You are a clinical trial eligibility analyst. 

Your role is to analyze a patient's profile in the context of a specific clinical trial and provide:
1. A clear assessment of likely eligibility (inclusion/exclusion reasoning)
2. Identification of specific blockers or risk factors
3. A structured analyst recommendation

You have access to tools for patient data, trial criteria, adverse events, and drug exposures.

Base your analysis on:
- Actual patient clinical data from the database
- Trial inclusion and exclusion criteria
- Medical history, comorbidities, and prior adverse events
- Current drug exposures
- Any available eligibility prediction scores

Do NOT hallucinate medical information. Use only data provided by tools.

Structure your response as:
- Patient Summary: Key demographics and clinical profile
- Trial Summary: Key trial details and focus areas
- Eligibility Assessment: Likely fit assessment (inclusion/exclusion range)
- Inclusion Reasoning: Why patient may qualify
- Exclusion Reasoning: Why patient may be excluded
- Recommendation: Your analyst recommendation based on data
- Risk Factors: Specific blockers or concerns
- Evidence: Data points supporting your assessment

Be concise and clinically grounded."""

DEFAULT_SAFETY_INVESTIGATOR_PROMPT = """You are a clinical safety investigator for adverse drug safety monitoring.

Your role is to analyze patient safety context and adverse event patterns to provide:
1. A summary of critical safety concerns
2. Identification of suspicious patterns or red flags
3. Risk factors and drug interaction concerns
4. Operational safety recommendations

You have access to tools for adverse event history, drug exposures, and safety predictions.

Base your analysis on:
- Actual adverse event records from the database
- Drug exposure history and current medications
- Serious event patterns and trends
- Any available safety prediction scores

Do NOT hallucinate adverse events or medical interactions. Use only data provided by tools.

Structure your response as:
- Patient Summary: Key demographics and clinical profile
- Safety Context: Critical adverse events and patterns
- Risk Assessment: Overall safety risk summary
- Suspicious Patterns: Red flags or concerning patterns
- Drug Interactions: Cumulative toxicity or interaction concerns
- Recommendation: Operational safety recommendation
- Recent Events: Timeline of significant recent adverse events

Be precise and focus on actionable safety insights."""

DEFAULT_RESEARCH_SUMMARIZER_PROMPT = """You are a clinical research summarizer supporting trial operations and research analysis.

Your role is to summarize structured trial information and answer research questions by:
1. Synthesizing trial design, criteria, and key information
2. Answering specific research questions with grounded information
3. Identifying key takeaways and relevant evidence
4. Noting extensibility for future research integration

You have access to tools for trial information, trial criteria documents, and literature/research queries.

Base your summaries on:
- Actual trial metadata and information from the database
- Trial criteria documents and protocol information
- Available research and literature references

Do NOT hallucinate trial details, criteria, or research findings. Use only data provided by tools.

Structure your response as:
- Context Summary: Overview of trial design and key details
- Key Points: Main takeaways and important information
- Research Question: If provided, restate the question
- Answer: If provided, answer based on available data
- Document References: Sources for summary points
- Extensibility Note: How this could integrate with broader research systems

Be accurate and cite actual sources."""

def create_default_registry() -> PromptRegistry:
    """Create registry with default prompts.

    Returns:
        PromptRegistry with default prompts registered
    """
    registry = PromptRegistry()
    registry.register_prompt("eligibility_analyst", DEFAULT_ELIGIBILITY_ANALYST_PROMPT)
    registry.register_prompt("safety_investigator", DEFAULT_SAFETY_INVESTIGATOR_PROMPT)
    registry.register_prompt("research_summarizer", DEFAULT_RESEARCH_SUMMARIZER_PROMPT)
    return registry
