"""Phase 6 orchestration for use-case-specific training pipelines."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Callable

import pandas as pd

from pharma_os.core.settings import Settings
from pharma_os.ml.contracts import TrainingRunSummary, UseCaseTrainingResult
from pharma_os.ml.data import load_feature_dataset
from pharma_os.ml.evaluation import extract_feature_importance
from pharma_os.ml.persistence import (
    persist_classification_training_artifacts,
    persist_recruitment_ranking_artifacts,
)
from pharma_os.ml.targets import (
    prepare_eligibility_target,
    prepare_recruitment_target,
    prepare_safety_target,
)
from pharma_os.ml.training import build_feature_matrix, train_binary_classification_models
from pharma_os.observability.logging import get_logger
from pharma_os.pipelines.common.io import ensure_directory, write_json

logger = get_logger(__name__)

USE_CASES = ("eligibility", "safety", "recruitment")
TARGET_PREPARERS: dict[str, Callable[[pd.DataFrame], object]] = {
    "eligibility": prepare_eligibility_target,
    "safety": prepare_safety_target,
    "recruitment": prepare_recruitment_target,
}


def train_single_use_case(
    *,
    use_case: str,
    feature_run_id: str,
    training_run_id: str,
    settings: Settings,
) -> UseCaseTrainingResult:
    """Train one use case and persist model/evaluation artifacts."""
    if use_case not in USE_CASES:
        raise ValueError(f"Unsupported use case: {use_case}")

    logger.info("phase 6 training start", extra={"use_case": use_case, "training_run_id": training_run_id})
    dataset = load_feature_dataset(use_case=use_case, run_id=feature_run_id, settings=settings)

    preparer = TARGET_PREPARERS[use_case]
    target_result = preparer(dataset)

    if use_case == "recruitment" and target_result.target_mode == "score_only":
        ranking_config = {
            "ranking_mode": "deterministic_weighted_score",
            "score_formula": "4*condition_fit + 2*urgency_proxy + 2*enrollment_ready_flag - 2*exclusion_risk_signal - I(active_exposure_count>=3)",
            "source_feature_run_id": feature_run_id,
        }
        summary_payload = {
            "mode": "score_only",
            "row_count": int(len(dataset.index)),
            "avg_score": float(dataset["ranking_score_component"].mean()) if not dataset.empty else 0.0,
            "p90_score": float(dataset["ranking_score_component"].quantile(0.9)) if not dataset.empty else 0.0,
            "target_strategy": target_result.details,
        }

        artifacts = persist_recruitment_ranking_artifacts(
            training_run_id=training_run_id,
            ranking_config=ranking_config,
            summary_payload=summary_payload,
            settings=settings,
        )

        return UseCaseTrainingResult(
            use_case=use_case,
            training_run_id=training_run_id,
            feature_run_id=feature_run_id,
            trained=False,
            selected_model="score_based_ranker",
            target_mode=target_result.target_mode,
            row_count=int(len(dataset.index)),
            artifacts=artifacts,
            notes=["No reliable supervised recruitment target found; persisted deterministic ranking configuration."],
        )

    X = build_feature_matrix(df=dataset, dropped_feature_columns=target_result.dropped_feature_columns)
    y = pd.Series(target_result.y, index=dataset.index).astype("int64")

    if y.nunique(dropna=False) < 2:
        return UseCaseTrainingResult(
            use_case=use_case,
            training_run_id=training_run_id,
            feature_run_id=feature_run_id,
            trained=False,
            selected_model="none",
            target_mode=target_result.target_mode,
            row_count=int(len(dataset.index)),
            artifacts=None,
            notes=["Training skipped because target contains a single class after preparation."],
        )

    training_output = train_binary_classification_models(X=X, y=y)
    feature_importance_df = extract_feature_importance(training_output.selected_model)

    target_summary = {
        "target_name": target_result.target_name,
        "target_mode": target_result.target_mode,
        "positive_ratio": target_result.positive_ratio,
        "details": target_result.details,
        "dropped_feature_columns": target_result.dropped_feature_columns,
    }

    artifacts = persist_classification_training_artifacts(
        use_case=use_case,
        training_run_id=training_run_id,
        model_name=training_output.selected_model_name,
        model=training_output.selected_model,
        evaluations=training_output.evaluations,
        feature_columns=training_output.feature_columns,
        target_summary=target_summary,
        extra_metadata={
            "feature_run_id": feature_run_id,
            "class_balance": training_output.class_balance,
        },
        feature_importance_df=feature_importance_df,
        settings=settings,
    )

    logger.info(
        "phase 6 training complete",
        extra={
            "use_case": use_case,
            "training_run_id": training_run_id,
            "selected_model": training_output.selected_model_name,
        },
    )

    return UseCaseTrainingResult(
        use_case=use_case,
        training_run_id=training_run_id,
        feature_run_id=feature_run_id,
        trained=True,
        selected_model=training_output.selected_model_name,
        target_mode=target_result.target_mode,
        row_count=int(len(dataset.index)),
        artifacts=artifacts,
        notes=[],
    )


def train_all_use_cases(
    *,
    feature_run_id: str,
    training_run_id: str,
    settings: Settings,
) -> TrainingRunSummary:
    """Train all supported Phase 6 use cases and persist manifest summary."""
    started_at = datetime.now(UTC)
    results: list[UseCaseTrainingResult] = []

    for use_case in USE_CASES:
        try:
            result = train_single_use_case(
                use_case=use_case,
                feature_run_id=feature_run_id,
                training_run_id=training_run_id,
                settings=settings,
            )
        except Exception as exc:
            logger.exception(
                "phase 6 use case failure",
                extra={"use_case": use_case, "training_run_id": training_run_id, "error": str(exc)},
            )
            result = UseCaseTrainingResult(
                use_case=use_case,
                training_run_id=training_run_id,
                feature_run_id=feature_run_id,
                trained=False,
                selected_model="none",
                target_mode="error",
                row_count=0,
                artifacts=None,
                notes=[str(exc)],
            )
        results.append(result)

    summary = TrainingRunSummary(
        training_run_id=training_run_id,
        feature_run_id=feature_run_id,
        started_at=started_at,
        finished_at=datetime.now(UTC),
        results=results,
    )

    summary_dir = ensure_directory(settings.phase6_reports_path)
    write_json(summary.to_dict(), summary_dir / f"training_manifest_{training_run_id}.json")

    return summary
