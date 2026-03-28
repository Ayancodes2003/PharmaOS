"""Patient screening funnel mart builders."""

from __future__ import annotations

import pandas as pd


def build_patient_screening_funnel_mart(
    *,
    eligibility_features: pd.DataFrame,
) -> pd.DataFrame:
    """Build operational screening funnel counts grounded in eligibility signals."""
    if eligibility_features.empty:
        return pd.DataFrame(
            [
                {
                    "total_screened": 0,
                    "eligible_candidates": 0,
                    "not_eligible_candidates": 0,
                    "likely_exclusion_candidates": 0,
                    "active_candidate_count": 0,
                }
            ]
        )

    scored = eligibility_features.copy()
    eligible_mask = scored["trial_fit_score_component"] >= 3
    exclusion_mask = (scored["serious_event_count"] > 0) | (scored["comorbidity_count"] >= 3)

    return pd.DataFrame(
        [
            {
                "total_screened": int(len(scored.index)),
                "eligible_candidates": int(eligible_mask.sum()),
                "not_eligible_candidates": int((~eligible_mask).sum()),
                "likely_exclusion_candidates": int(exclusion_mask.sum()),
                "active_candidate_count": int(scored["is_active_patient"].fillna(0).astype(int).sum()),
            }
        ]
    )
