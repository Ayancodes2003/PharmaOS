"""Metadata summarization for Phase 5 feature and mart outputs."""

from __future__ import annotations

from typing import Any

import pandas as pd


def summarize_dataset(df: pd.DataFrame, *, name: str) -> dict[str, Any]:
    """Build summary payload suitable for ML/BI artifact monitoring."""
    return {
        "name": name,
        "row_count": int(len(df.index)),
        "column_count": int(len(df.columns)),
        "columns": [str(column) for column in df.columns],
        "null_ratio_mean": float(df.isna().mean().mean()) if not df.empty else 0.0,
    }


def summarize_collection(named_frames: dict[str, pd.DataFrame]) -> dict[str, Any]:
    """Build collection-level summary for multiple outputs."""
    summaries = {name: summarize_dataset(df, name=name) for name, df in named_frames.items()}
    total_rows = int(sum(item["row_count"] for item in summaries.values()))
    return {
        "datasets": summaries,
        "dataset_count": len(named_frames),
        "total_rows": total_rows,
    }
