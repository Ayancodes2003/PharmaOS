"""File IO utilities for pipeline ingestion and stage output generation."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from pharma_os.pipelines.common.contracts import FileFormat


def ensure_directory(path: Path) -> Path:
    """Create directory recursively if it does not exist."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def infer_file_format(file_path: Path) -> FileFormat:
    """Infer file format from extension."""
    extension = file_path.suffix.lower().replace(".", "")
    try:
        return FileFormat(extension)
    except ValueError as exc:
        raise ValueError(f"Unsupported file format for path: {file_path}") from exc


def read_dataset(file_path: Path, file_format: FileFormat | None = None) -> pd.DataFrame:
    """Read dataset from CSV/JSON/Parquet with deterministic options."""
    if not file_path.exists():
        raise FileNotFoundError(f"Input file does not exist: {file_path}")

    fmt = file_format or infer_file_format(file_path)

    if fmt == FileFormat.CSV:
        return pd.read_csv(file_path)
    if fmt == FileFormat.JSON:
        return pd.read_json(file_path)
    if fmt == FileFormat.PARQUET:
        return pd.read_parquet(file_path)
    raise ValueError(f"Unsupported format: {fmt}")


def write_stage_dataset(df: pd.DataFrame, output_path: Path) -> Path:
    """Persist DataFrame as CSV stage artifact with stable ordering."""
    ensure_directory(output_path.parent)
    stable_df = df.sort_index(axis=1)
    stable_df.to_csv(output_path, index=False)
    return output_path


def write_json(payload: dict[str, object], output_path: Path) -> Path:
    """Persist JSON payload with deterministic pretty formatting."""
    ensure_directory(output_path.parent)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return output_path
