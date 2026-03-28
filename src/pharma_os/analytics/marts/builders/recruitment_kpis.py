"""Recruitment operational KPI mart builders."""

from __future__ import annotations

import pandas as pd


def build_recruitment_kpis_mart(
    *,
    recruitment_features: pd.DataFrame,
) -> pd.DataFrame:
    """Build trial-level operational recruitment KPI summaries."""
    if recruitment_features.empty:
        return pd.DataFrame(
            columns=[
                "trial_code",
                "candidate_count",
                "top_candidate_score",
                "avg_ranking_score",
                "high_urgency_candidates",
                "avg_exclusion_risk_signal",
            ]
        )

    mart = (
        recruitment_features.groupby("trial_code", dropna=False)
        .agg(
            candidate_count=("external_patient_id", "count"),
            top_candidate_score=("ranking_score_component", "max"),
            avg_ranking_score=("ranking_score_component", "mean"),
            high_urgency_candidates=("urgency_proxy", lambda s: int((s >= 2).sum())),
            avg_exclusion_risk_signal=("exclusion_risk_signal", "mean"),
        )
        .reset_index()
    )

    return mart.sort_values(by=["avg_ranking_score", "candidate_count"], ascending=[False, False], kind="stable")
