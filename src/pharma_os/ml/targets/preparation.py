"""Explicit and conservative target preparation utilities."""

from __future__ import annotations

from typing import Any

import pandas as pd

from pharma_os.ml.contracts import TargetPreparationResult


def prepare_eligibility_target(df: pd.DataFrame) -> TargetPreparationResult:
    """Prepare eligibility target, preferring explicit labels over conservative derivation."""
    explicit = _explicit_binary_target(df, "target_eligibility_label")
    if explicit is not None:
        return TargetPreparationResult(
            target_name="observed_eligibility_label",
            target_mode="observed_supervised",
            label_source_type="observed_ground_truth",
            weak_supervision=False,
            y=explicit.tolist(),
            dropped_feature_columns=[],
            derivation_columns=[],
            positive_ratio=float(explicit.mean()),
            details={"source": "target_eligibility_label"},
        )

    dropped = [
        "condition_match",
        "trial_is_recruiting",
        "serious_event_count",
        "comorbidity_count",
        "trial_remaining_slots",
    ]
    _require_columns(df, dropped, target_name="eligibility proxy")

    derived = (
        (df["condition_match"].fillna(0).astype(int) == 1)
        & (df["trial_is_recruiting"].fillna(0).astype(int) == 1)
        & (df["serious_event_count"].fillna(0).astype(int) == 0)
        & (df["comorbidity_count"].fillna(0).astype(int) <= 2)
        & (df["trial_remaining_slots"].fillna(0).astype(float) > 0)
    ).astype("int64")

    return TargetPreparationResult(
        target_name="proxy_eligibility_label",
        target_mode="weakly_supervised_proxy",
        label_source_type="derived_proxy",
        weak_supervision=True,
        y=derived.tolist(),
        dropped_feature_columns=dropped,
        derivation_columns=dropped,
        positive_ratio=float(derived.mean()),
        warnings=[
            "Weak supervision in use: eligibility target is a derived proxy, not an observed enrollment outcome.",
            "Proxy derivation columns are excluded from model features to mitigate direct target leakage.",
        ],
        details={
            "rule": "condition_match=1 AND trial_is_recruiting=1 AND serious_event_count=0 AND comorbidity_count<=2 AND trial_remaining_slots>0",
            "note": "Proxy target is conservative and used only when explicit historical outcomes are unavailable.",
        },
    )


def prepare_safety_target(df: pd.DataFrame) -> TargetPreparationResult:
    """Prepare safety target, preferring explicit labels over conservative derivation."""
    explicit = _explicit_binary_target(df, "target_safety_label")
    if explicit is not None:
        return TargetPreparationResult(
            target_name="observed_safety_label",
            target_mode="observed_supervised",
            label_source_type="observed_ground_truth",
            weak_supervision=False,
            y=explicit.tolist(),
            dropped_feature_columns=[],
            derivation_columns=[],
            positive_ratio=float(explicit.mean()),
            details={"source": "target_safety_label"},
        )

    dropped = [
        "serious_event_count",
        "severe_event_count",
        "events_last_30d",
        "safety_risk_component",
    ]
    _require_columns(df, dropped, target_name="safety proxy")

    high_risk_cutoff = float(df["safety_risk_component"].quantile(0.75)) if not df.empty else 0.0
    derived = (
        (df["serious_event_count"].fillna(0).astype(int) > 0)
        | (df["severe_event_count"].fillna(0).astype(int) > 0)
        | (df["events_last_30d"].fillna(0).astype(int) >= 2)
        | (df["safety_risk_component"].fillna(0).astype(float) >= high_risk_cutoff)
    ).astype("int64")

    return TargetPreparationResult(
        target_name="proxy_safety_label",
        target_mode="weakly_supervised_proxy",
        label_source_type="derived_proxy",
        weak_supervision=True,
        y=derived.tolist(),
        dropped_feature_columns=dropped,
        derivation_columns=dropped,
        positive_ratio=float(derived.mean()),
        warnings=[
            "Weak supervision in use: safety target is a derived proxy, not a confirmed clinical outcome label.",
            "Proxy derivation columns are excluded from model features to mitigate direct target leakage.",
        ],
        details={
            "rule": "serious_event_count>0 OR severe_event_count>0 OR events_last_30d>=2 OR safety_risk_component>=q75",
            "quantile_cutoff": high_risk_cutoff,
            "note": "Proxy target is risk-triggered and used only when labeled outcomes are unavailable.",
        },
    )


def prepare_recruitment_target(df: pd.DataFrame) -> TargetPreparationResult:
    """Prepare recruitment objective strategy without fabricating weak supervised labels."""
    if "target_recruitment_label" in df.columns:
        explicit = _explicit_binary_target(df, "target_recruitment_label")
        if explicit is not None:
            return TargetPreparationResult(
                target_name="observed_recruitment_label",
                target_mode="observed_supervised",
                label_source_type="observed_ground_truth",
                weak_supervision=False,
                y=explicit.tolist(),
                dropped_feature_columns=[],
                derivation_columns=[],
                positive_ratio=float(explicit.mean()),
                details={"source": "target_recruitment_label"},
            )

    return TargetPreparationResult(
        target_name="ranking_score_component",
        target_mode="score_only",
        label_source_type="deterministic_score",
        weak_supervision=False,
        y=df["ranking_score_component"].fillna(0).astype(float).tolist(),
        dropped_feature_columns=[],
        derivation_columns=[],
        positive_ratio=0.0,
        warnings=[
            "No supervised recruitment label detected; this path produces score-based prioritization artifacts only.",
        ],
        details={
            "note": "No reliable supervised recruitment label available. Persisting deterministic score-based ranking configuration only.",
            "supervised_training_enabled": False,
            "artifact_kind": "score_based_prioritization",
        },
    )


def _explicit_binary_target(df: pd.DataFrame, column: str) -> pd.Series | None:
    if column not in df.columns:
        return None

    series = pd.to_numeric(df[column], errors="coerce")
    valid = series.dropna()
    if valid.empty:
        return None

    unique = set(valid.astype(int).unique().tolist())
    if not unique.issubset({0, 1}):
        return None

    return series.fillna(0).astype("int64")


def _require_columns(df: pd.DataFrame, required_columns: list[str], *, target_name: str) -> None:
    missing = [column for column in required_columns if column not in df.columns]
    if missing:
        raise ValueError(
            f"Cannot derive {target_name}: required columns are missing from feature artifact: {missing}"
        )
