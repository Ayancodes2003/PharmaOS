"""CLI entrypoint for PHARMA-OS Phase 7 model loading and inference workflows."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from sqlalchemy.orm import Session

from pharma_os.core.settings import get_settings
from pharma_os.db.postgres import get_session_factory, initialize_postgres
from pharma_os.ml.inference.contracts import (
    EligibilityInferenceRequest,
    RecruitmentInferenceRequest,
    SafetyInferenceRequest,
)
from pharma_os.ml.inference.orchestration import (
    run_all_inference_use_cases,
    run_eligibility_inference,
    run_recruitment_inference,
    run_safety_inference,
)
from pharma_os.ml.inference.reporting import persist_inference_summary
from pharma_os.observability.logging import configure_logging, get_logger

logger = get_logger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run PHARMA-OS Phase 7 inference workflows")
    parser.add_argument("--use-case", choices=["eligibility", "safety", "recruitment", "all"], required=True)
    parser.add_argument("--training-run-id", help="Optional specific training run id for model loading")
    parser.add_argument("--persist", action="store_true", help="Persist predictions to PostgreSQL")
    parser.add_argument("--trace-id", help="Optional trace id for audit correlation")

    parser.add_argument("--input", help="Input JSON for single use-case execution")
    parser.add_argument("--eligibility-input", help="Eligibility request JSON path (for --use-case all)")
    parser.add_argument("--safety-input", help="Safety request JSON path (for --use-case all)")
    parser.add_argument("--recruitment-input", help="Recruitment request JSON path (for --use-case all)")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    settings = get_settings()
    configure_logging(settings)

    initialize_postgres(settings)
    session_factory = get_session_factory()

    with session_factory() as session:
        if args.use_case == "eligibility":
            _require_arg(parser, args.input, "--input is required for eligibility inference")
            request = _load_request(EligibilityInferenceRequest, args.input, persist=args.persist, trace_id=args.trace_id)
            result = run_eligibility_inference(
                session=session,
                settings=settings,
                request=request,
                training_run_id=args.training_run_id,
            )
            persist_inference_summary(
                settings=settings,
                use_case="eligibility",
                payload=result,
                trace_id=args.trace_id,
            )
            print(result.model_dump_json(indent=2))
            return 0

        if args.use_case == "safety":
            _require_arg(parser, args.input, "--input is required for safety inference")
            request = _load_request(SafetyInferenceRequest, args.input, persist=args.persist, trace_id=args.trace_id)
            result = run_safety_inference(
                session=session,
                settings=settings,
                request=request,
                training_run_id=args.training_run_id,
            )
            persist_inference_summary(
                settings=settings,
                use_case="safety",
                payload=result,
                trace_id=args.trace_id,
            )
            print(result.model_dump_json(indent=2))
            return 0

        if args.use_case == "recruitment":
            _require_arg(parser, args.input, "--input is required for recruitment inference")
            request = _load_request(RecruitmentInferenceRequest, args.input, persist=args.persist, trace_id=args.trace_id)
            result = run_recruitment_inference(
                session=session,
                settings=settings,
                request=request,
                training_run_id=args.training_run_id,
            )
            persist_inference_summary(
                settings=settings,
                use_case="recruitment",
                payload=result,
                trace_id=args.trace_id,
            )
            print(result.model_dump_json(indent=2))
            return 0

        eligibility_request = (
            _load_request(EligibilityInferenceRequest, args.eligibility_input, persist=args.persist, trace_id=args.trace_id)
            if args.eligibility_input
            else None
        )
        safety_request = (
            _load_request(SafetyInferenceRequest, args.safety_input, persist=args.persist, trace_id=args.trace_id)
            if args.safety_input
            else None
        )
        recruitment_request = (
            _load_request(RecruitmentInferenceRequest, args.recruitment_input, persist=args.persist, trace_id=args.trace_id)
            if args.recruitment_input
            else None
        )

        if eligibility_request is None and safety_request is None and recruitment_request is None:
            parser.error("At least one of --eligibility-input, --safety-input, --recruitment-input must be provided")

        summary = run_all_inference_use_cases(
            session=session,
            settings=settings,
            eligibility_request=eligibility_request,
            safety_request=safety_request,
            recruitment_request=recruitment_request,
            training_run_id=args.training_run_id,
            trace_id=args.trace_id,
        )
        persist_inference_summary(
            settings=settings,
            use_case="all",
            payload=summary,
            trace_id=args.trace_id,
        )
        print(summary.model_dump_json(indent=2))
        return 0


def _load_request(model_cls, file_path: str, *, persist: bool, trace_id: str | None):
    path = Path(file_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["persist_prediction"] = persist
    if trace_id:
        payload["trace_id"] = trace_id
    return model_cls.model_validate(payload)


def _require_arg(parser: argparse.ArgumentParser, value: str | None, message: str) -> None:
    if value is None:
        parser.error(message)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        logger.exception("phase 7 inference execution failed", extra={"error": str(exc)})
        sys.exit(1)
