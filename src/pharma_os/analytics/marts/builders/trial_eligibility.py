"""Trial-level eligibility mart builders."""

from __future__ import annotations

import pandas as pd


def build_trial_eligibility_mart(
    *,
    eligibility_features: pd.DataFrame,
) -> pd.DataFrame:
    """Build trial-level fit and eligibility distribution summaries."""
    if eligibility_features.empty:
        return pd.DataFrame(
            columns=[
                "trial_code",
                "phase",
                "status",
                "candidate_count",
                "eligible_candidate_count",
                "eligibility_rate",
                "avg_fit_score",
                "avg_serious_event_count",
            ]
        )

    scored = eligibility_features.copy()
    scored["eligible_flag"] = (scored["trial_fit_score_component"] >= 3).astype("int64")

    trial_summary = (
        scored.groupby(["trial_code", "phase", "status"], dropna=False)
        .agg(
            candidate_count=("external_patient_id", "count"),
            eligible_candidate_count=("eligible_flag", "sum"),
            avg_fit_score=("trial_fit_score_component", "mean"),
            avg_serious_event_count=("serious_event_count", "mean"),
        )
        .reset_index()
    )

    trial_summary["eligibility_rate"] = (
        trial_summary["eligible_candidate_count"] / trial_summary["candidate_count"].clip(lower=1)
    )

    return trial_summary.sort_values(by=["candidate_count", "eligibility_rate"], ascending=[False, False], kind="stable")
