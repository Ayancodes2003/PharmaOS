"""Dataset quality profiling helpers for ingestion pipeline metadata."""

from __future__ import annotations

from typing import Any

import pandas as pd


def dataset_quality_summary(df: pd.DataFrame, *, top_columns: int = 20) -> dict[str, Any]:
    """Generate concise quality profile for pipeline run metadata."""
    row_count = len(df.index)
    column_count = len(df.columns)

    if row_count == 0:
        return {
            "row_count": 0,
            "column_count": column_count,
            "missing_ratio_by_column": {},
            "dtypes": {column: str(dtype) for column, dtype in df.dtypes.items()},
        }

    missing_ratio = {
        column: float(df[column].isna().sum() / row_count)
        for column in df.columns[:top_columns]
    }

    return {
        "row_count": row_count,
        "column_count": column_count,
        "missing_ratio_by_column": missing_ratio,
        "dtypes": {column: str(dtype) for column, dtype in df.dtypes.items()},
    }
