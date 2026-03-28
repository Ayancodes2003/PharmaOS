"""Shared utilities for Phase 5 feature engineering and analytics marts."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from pharma_os.pipelines.common.io import read_dataset


def read_stage_dataset(base_path: Path, domain: str, run_id: str) -> pd.DataFrame:
    """Read a deterministic stage artifact for a domain and run."""
    path = base_path / domain / f"{run_id}.csv"
    return read_dataset(path)


def safe_to_datetime(series: pd.Series, *, utc: bool = True) -> pd.Series:
    """Convert series to datetime without raising on malformed values."""
    return pd.to_datetime(series, errors="coerce", utc=utc)


def bool_to_int(series: pd.Series) -> pd.Series:
    """Normalize bool-like values to 0/1 integer signal."""
    normalized = series.fillna(False).astype(bool)
    return normalized.astype("int64")


def ratio_or_zero(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    """Compute stable ratios and replace divide-by-zero with zero."""
    value = numerator.astype("float64") / denominator.astype("float64")
    return value.replace([pd.NA, float("inf"), float("-inf")], 0.0).fillna(0.0)


def categorize_age(age_series: pd.Series) -> pd.Series:
    """Generate analysis-friendly age bucket labels."""
    buckets = pd.cut(
        age_series,
        bins=[-1, 17, 30, 45, 60, 75, 200],
        labels=["under_18", "18_30", "31_45", "46_60", "61_75", "76_plus"],
    )
    return buckets.astype("string").fillna("unknown")


def severity_to_score(series: pd.Series) -> pd.Series:
    """Map severity values to ordinal clinical burden signals."""
    mapping = {
        "mild": 1,
        "moderate": 2,
        "severe": 3,
        "life_threatening": 4,
        "death": 5,
    }
    return series.astype("string").map(mapping).fillna(0).astype("int64")


def days_since(reference_ts: pd.Timestamp, series: pd.Series) -> pd.Series:
    """Compute non-negative days between reference timestamp and event datetime."""
    parsed = safe_to_datetime(series)
    delta = (reference_ts - parsed).dt.days
    return delta.clip(lower=0).fillna(9999).astype("int64")
