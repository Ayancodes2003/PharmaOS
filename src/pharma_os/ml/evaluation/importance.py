"""Feature importance extraction helpers for trained pipelines."""

from __future__ import annotations

import pandas as pd
from sklearn.pipeline import Pipeline


def extract_feature_importance(model: Pipeline) -> pd.DataFrame:
    """Extract normalized feature importance from supported estimators."""
    preprocessor = model.named_steps.get("preprocessor")
    estimator = model.named_steps.get("model")

    if preprocessor is None or estimator is None:
        return pd.DataFrame(columns=["feature", "importance"])

    feature_names = preprocessor.get_feature_names_out()

    if hasattr(estimator, "feature_importances_"):
        values = estimator.feature_importances_
    elif hasattr(estimator, "coef_"):
        coef = estimator.coef_
        values = coef[0] if getattr(coef, "ndim", 1) > 1 else coef
        values = abs(values)
    else:
        return pd.DataFrame(columns=["feature", "importance"])

    output = pd.DataFrame(
        {
            "feature": [str(name) for name in feature_names],
            "importance": values,
        }
    )

    return output.sort_values(by="importance", ascending=False, kind="stable").reset_index(drop=True)
