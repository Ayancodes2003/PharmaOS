"""Operational CLI for agent execution."""

import asyncio
import json
import logging
import sys
from argparse import ArgumentParser
from pathlib import Path
from uuid import uuid4

from pharma_os.agents import (
    AgentDispatcher,
    AgentExecutor,
    AgentType,
    EligibilityAnalystRequest,
    ResearchSummarizerRequest,
    SafetyInvestigatorRequest,
)
from pharma_os.agents.persistence import TraceStore
from pharma_os.core.settings import Settings
from pharma_os.db.postgres import get_session

logger = logging.getLogger(__name__)


async def run_eligibility_analysis(
    args: dict,
    dispatcher: AgentDispatcher,
    session,
) -> None:
    """Run eligibility analyst agent.

    Args:
        args: Command arguments
        dispatcher: Agent dispatcher
        session: Database session
    """
    request = EligibilityAnalystRequest(
        patient_id=args["patient_id"],
        trial_id=args["trial_id"],
        trace_id=args.get("trace_id") or str(uuid4()),
        include_prediction=args.get("include_prediction", True),
    )

    executor = AgentExecutor(dispatcher, trace_store=TraceStore())
    result, metadata = await executor.execute(request, session)

    # Output result
    print("=" * 80)
    print("ELIGIBILITY ANALYSIS RESULT")
    print("=" * 80)

    if result.success:
        print(f"\nPatient: {result.patient_summary}")
        print(f"Trial: {result.trial_summary}")
        print(f"\n{result.eligibility_assessment}")
        print(f"\nRecommendation: {result.recommendation}")
        if result.risk_factors:
            print(f"Risk Factors: {', '.join(result.risk_factors)}")
    else:
        print(f"ERROR: {result.error}")

    print(f"\n[Execution: {result.execution_time_ms:.1f}ms | Trace: {result.trace_id}]")

    if args.get("output_json"):
        with open(args["output_json"], "w") as f:
            json.dump(result.dict(), f, indent=2, default=str)
        print(f"Result saved to: {args['output_json']}")


async def run_safety_investigation(
    args: dict,
    dispatcher: AgentDispatcher,
    session,
) -> None:
    """Run safety investigator agent.

    Args:
        args: Command arguments
        dispatcher: Agent dispatcher
        session: Database session
    """
    request = SafetyInvestigatorRequest(
        patient_id=args["patient_id"],
        drug_name=args.get("drug_name"),
        trace_id=args.get("trace_id") or str(uuid4()),
        include_prediction=args.get("include_prediction", True),
    )

    executor = AgentExecutor(dispatcher, trace_store=TraceStore())
    result, metadata = await executor.execute(request, session)

    # Output result
    print("=" * 80)
    print("SAFETY INVESTIGATION RESULT")
    print("=" * 80)

    if result.success:
        print(f"\nPatient: {result.patient_summary}")
        print(f"\n{result.risk_assessment}")
        if result.suspicious_patterns:
            print(f"\nSuspicious Patterns:")
            for pattern in result.suspicious_patterns:
                print(f"  - {pattern}")
        print(f"\nRecommendation: {result.recommendation}")
    else:
        print(f"ERROR: {result.error}")

    print(f"\n[Execution: {result.execution_time_ms:.1f}ms | Trace: {result.trace_id}]")

    if args.get("output_json"):
        with open(args["output_json"], "w") as f:
            json.dump(result.dict(), f, indent=2, default=str)
        print(f"Result saved to: {args['output_json']}")


async def run_research_summarization(
    args: dict,
    dispatcher: AgentDispatcher,
    session,
) -> None:
    """Run research summarizer agent.

    Args:
        args: Command arguments
        dispatcher: Agent dispatcher
        session: Database session
    """
    request = ResearchSummarizerRequest(
        trial_id=args.get("trial_id"),
        query=args.get("query"),
        context_type=args.get("context_type", "trial"),
        trace_id=args.get("trace_id") or str(uuid4()),
    )

    executor = AgentExecutor(dispatcher, trace_store=TraceStore())
    result, metadata = await executor.execute(request, session)

    # Output result
    print("=" * 80)
    print("RESEARCH SUMMARY RESULT")
    print("=" * 80)

    if result.success:
        print(f"\n{result.context_summary}")
        if result.key_points:
            print("\nKey Points:")
            for point in result.key_points:
                print(f"  - {point}")
        if result.answer:
            print(f"\nAnswer: {result.answer}")
    else:
        print(f"ERROR: {result.error}")

    print(f"\n[Execution: {result.execution_time_ms:.1f}ms | Trace: {result.trace_id}]")

    if args.get("output_json"):
        with open(args["output_json"], "w") as f:
            json.dump(result.dict(), f, indent=2, default=str)
        print(f"Result saved to: {args['output_json']}")


async def main():
    """Main CLI entry point."""
    parser = ArgumentParser(description="PHARMA-OS Agent CLI")

    subparsers = parser.add_subparsers(dest="command", help="Agent type")

    # Eligibility analyst
    eligibility_parser = subparsers.add_parser(
        "eligibility",
        help="Run eligibility analyst agent",
    )
    eligibility_parser.add_argument("patient_id", help="Patient ID or external patient ID")
    eligibility_parser.add_argument("trial_id", help="Trial ID or trial code")
    eligibility_parser.add_argument(
        "--trace-id",
        help="Optional trace ID for correlation",
    )
    eligibility_parser.add_argument(
        "--no-prediction",
        action="store_true",
        help="Skip eligibility prediction lookup",
    )
    eligibility_parser.add_argument(
        "--output-json",
        help="Output result to JSON file",
    )

    # Safety investigator
    safety_parser = subparsers.add_parser(
        "safety",
        help="Run safety investigator agent",
    )
    safety_parser.add_argument("patient_id", help="Patient ID or external patient ID")
    safety_parser.add_argument(
        "--drug",
        dest="drug_name",
        help="Optional specific drug to investigate",
    )
    safety_parser.add_argument(
        "--trace-id",
        help="Optional trace ID for correlation",
    )
    safety_parser.add_argument(
        "--no-prediction",
        action="store_true",
        help="Skip safety prediction lookup",
    )
    safety_parser.add_argument(
        "--output-json",
        help="Output result to JSON file",
    )

    # Research summarizer
    research_parser = subparsers.add_parser(
        "research",
        help="Run research summarizer agent",
    )
    research_parser.add_argument(
        "--trial",
        dest="trial_id",
        help="Trial ID or trial code",
    )
    research_parser.add_argument(
        "--query",
        help="Research query",
    )
    research_parser.add_argument(
        "--context",
        dest="context_type",
        default="trial",
        help="Context type: trial, literature, disease, drug",
    )
    research_parser.add_argument(
        "--trace-id",
        help="Optional trace ID for correlation",
    )
    research_parser.add_argument(
        "--output-json",
        help="Output result to JSON file",
    )

    # Info command
    info_parser = subparsers.add_parser(
        "info",
        help="Show available agents and tools",
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Load settings
    settings = Settings()

    # Create dispatcher
    dispatcher = AgentDispatcher(settings)

    # Handle info command
    if args.command == "info":
        print("PHARMA-OS Agent Framework Information")
        print("=" * 80)
        print("\nAvailable Agents:")
        for agent_info in dispatcher.list_available_agents():
            print(f"\n  {agent_info['agent_name']}")
            print(f"    Type: {agent_info['agent_type']}")
            print(f"    Description: {agent_info['agent_description']}")
            print(f"    LLM: {agent_info['llm_provider']}/{agent_info['llm_model']}")
        print(f"\n  LLM Provider: {dispatcher.llm_provider.get_provider_name()}")
        print(f"  LLM Available: {dispatcher.llm_provider.is_available()}")
        print("\nAvailable Tools:")
        for tool_info in dispatcher.get_tools_info():
            print(f"\n  {tool_info['name']}")
            print(f"    {tool_info['description']}")
        return

    # Get session
    session = get_session(settings)

    try:
        # Route to appropriate command
        if args.command == "eligibility":
            await run_eligibility_analysis(
                vars(args),
                dispatcher,
                session,
            )
        elif args.command == "safety":
            await run_safety_investigation(
                vars(args),
                dispatcher,
                session,
            )
        elif args.command == "research":
            await run_research_summarization(
                vars(args),
                dispatcher,
                session,
            )
        else:
            parser.print_help()

    except Exception as e:
        logger.error(f"Error executing agent: {e}", exc_info=True)
        sys.exit(1)

    finally:
        session.close()


if __name__ == "__main__":
    asyncio.run(main())
