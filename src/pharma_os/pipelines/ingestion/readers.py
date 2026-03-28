"""Schema-aware domain ingestion readers for structured datasets."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from pharma_os.pipelines.common.contracts import FileFormat, PipelineDomain
from pharma_os.pipelines.common.io import read_dataset
from pharma_os.pipelines.common.normalization import normalize_column_names


def ingest_domain_dataset(
    domain: PipelineDomain,
    source_path: Path,
    *,
    file_format: FileFormat | None = None,
) -> pd.DataFrame:
    """Ingest a structured domain dataset from source file."""
    df = read_dataset(source_path, file_format)
    df = normalize_column_names(df)
    if df.empty:
        raise ValueError(f"Ingestion produced empty dataset for domain '{domain.value}'")
    return df
