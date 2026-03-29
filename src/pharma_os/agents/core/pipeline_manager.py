"""Pipeline manager for orchestrating agent workflows with state management."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from pharma_os.agents.base import AgentBase, AgentResult
from pharma_os.agents.core.context import AgentExecutionContext


logger = logging.getLogger(__name__)


class PipelineStage(Enum):
    """Stages in an agent pipeline."""

    INITIALIZATION = "init"
    EXTRACTION = "extraction"
    ANALYSIS = "analysis"
    INFERENCE = "inference"
    FORMATTING = "formatting"
    COMPLETION = "completion"


@dataclass
class PipelineState:
    """State of a pipeline execution."""

    trace_id: str
    current_stage: PipelineStage
    completed_stages: list[PipelineStage]
    stage_results: dict[PipelineStage, Any]
    errors: list[str]
    total_execution_time_ms: float


class PipelineManager:
    """Manages execution of agent pipelines with state tracking."""

    def __init__(self, context: AgentExecutionContext):
        """Initialize pipeline manager.

        Args:
            context: Execution context
        """
        self.context = context
        self.state = PipelineState(
            trace_id=context.trace_id,
            current_stage=PipelineStage.INITIALIZATION,
            completed_stages=[],
            stage_results={},
            errors=[],
            total_execution_time_ms=0.0,
        )
        self.logger = logger

    def add_stage(
        self,
        stage: PipelineStage,
        agents: list[AgentBase],
        parallel: bool = False,
    ) -> bool:
        """Add a stage with agents to the pipeline.

        Args:
            stage: Pipeline stage
            agents: List of agents for this stage
            parallel: Whether agents should run in parallel

        Returns:
            True if stage succeeded, False if it failed
        """
        self.logger.info(f"Starting pipeline stage: {stage.value}")
        self.state.current_stage = stage

        try:
            if parallel:
                results = self._execute_parallel(agents)
            else:
                results = self._execute_sequential(agents)

            self.state.stage_results[stage] = results
            self.state.completed_stages.append(stage)

            self.logger.info(f"Stage {stage.value} completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Stage {stage.value} failed: {str(e)}")
            self.state.errors.append(f"{stage.value}: {str(e)}")
            return False

    def execute_full_pipeline(
        self,
        stages: dict[PipelineStage, tuple[list[AgentBase], bool]],
    ) -> PipelineState:
        """Execute a full pipeline of stages.

        Args:
            stages: Dictionary of stage -> (agents, parallel_flag)

        Returns:
            Final pipeline state
        """
        import time

        start_time = time.time()

        for stage, (agents, parallel) in stages.items():
            success = self.add_stage(stage, agents, parallel)
            if not success:
                self.logger.warning(f"Pipeline halted at stage {stage.value}")
                break

        self.state.total_execution_time_ms = (time.time() - start_time) * 1000
        return self.state

    def get_stage_result(self, stage: PipelineStage) -> Any:
        """Get result from a completed stage.

        Args:
            stage: Pipeline stage

        Returns:
            Stage result or None if not completed
        """
        return self.state.stage_results.get(stage)

    def get_all_results(self) -> dict[PipelineStage, Any]:
        """Get all stage results.

        Returns:
            Dictionary of all stage results
        """
        return self.state.stage_results

    def get_state_summary(self) -> str:
        """Get summary of pipeline state.

        Returns:
            State summary string
        """
        lines = ["Pipeline State Summary", "=" * 40]
        lines.append(f"Trace ID: {self.state.trace_id}")
        lines.append(f"Current Stage: {self.state.current_stage.value}")
        lines.append(f"Completed Stages: {len(self.state.completed_stages)}")
        lines.append(f"Total Execution Time: {self.state.total_execution_time_ms:.2f}ms")

        if self.state.errors:
            lines.append("Errors:")
            for error in self.state.errors:
                lines.append(f"  - {error}")

        return "\n".join(lines)

    def _execute_sequential(self, agents: list[AgentBase]) -> list[AgentResult]:
        """Execute agents sequentially.

        Args:
            agents: List of agents to execute

        Returns:
            List of results
        """
        results: list[AgentResult] = []

        for i, agent in enumerate(agents):
            self.logger.debug(
                f"Executing agent {i + 1}/{len(agents)}: {agent.__class__.__name__}"
            )

            result = agent.execute(self.context)
            results.append(result)

            if not result.success:
                self.logger.warning(f"Agent {agent.__class__.__name__} failed")

        return results

    def _execute_parallel(self, agents: list[AgentBase]) -> list[AgentResult]:
        """Execute agents in parallel (simulated).

        Args:
            agents: List of agents to execute

        Returns:
            List of results
        """
        self.logger.debug(f"Executing {len(agents)} agents in parallel")
        results: list[AgentResult] = []

        for agent in agents:
            result = agent.execute(self.context)
            results.append(result)

        return results
