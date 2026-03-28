"""Reusable normalization and coercion helpers for domain preprocessors."""

from __future__ import annotations

import re
from collections.abc import Iterable

import pandas as pd


def normalize_column_name(name: str) -> str:
    """Normalize arbitrary column name into snake_case."""
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", name.strip().lower())
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Return DataFrame with normalized snake_case columns."""
    df = df.copy()
    df.columns = [normalize_column_name(col) for col in df.columns]
    return df


def strip_text_columns(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    """Trim and normalize whitespace in text columns."""
    df = df.copy()
    for column in columns:
        if column in df.columns:
            df[column] = (
                df[column]
                .astype("string")
                .str.strip()
                .str.replace(r"\s+", " ", regex=True)
                .replace({"": pd.NA})
            )
    return df


def normalize_boolean_series(series: pd.Series) -> pd.Series:
    """Normalize mixed boolean-like values into pandas nullable boolean."""
    true_values = {"true", "1", "yes", "y", "active", "t"}
    false_values = {"false", "0", "no", "n", "inactive", "f"}

    normalized = series.astype("string").str.strip().str.lower()
    mapped = normalized.map(
        lambda value: True
        if value in true_values
        else False
        if value in false_values
        else pd.NA
    )
    return pd.Series(mapped, index=series.index, dtype="boolean")


def normalize_enum_values(series: pd.Series, mapping: dict[str, str], default: str | None = None) -> pd.Series:
    """Normalize categorical labels using case-insensitive mapping."""
    normalized = series.astype("string").str.strip().str.lower()
    mapped = normalized.map(mapping)
    if default is not None:
        mapped = mapped.fillna(default)
    return mapped.astype("string")


def coerce_datetime(series: pd.Series, *, utc: bool = True) -> pd.Series:
    """Coerce date/datetime strings into datetime64."""
    return pd.to_datetime(series, errors="coerce", utc=utc)


def coerce_date_string(series: pd.Series) -> pd.Series:
    """Coerce values to ISO date strings (YYYY-MM-DD) with null safety."""
    date_series = pd.to_datetime(series, errors="coerce").dt.date
    return pd.Series(date_series, index=series.index, dtype="string")
