"""Domain-specific ingestion entrypoints."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from pharma_os.pipelines.common.contracts import FileFormat, PipelineDomain
from pharma_os.pipelines.ingestion.readers import ingest_domain_dataset


def ingest_patients(source_path: Path, *, file_format: FileFormat | None = None) -> pd.DataFrame:
    return ingest_domain_dataset(PipelineDomain.PATIENTS, source_path, file_format=file_format)


def ingest_trials(source_path: Path, *, file_format: FileFormat | None = None) -> pd.DataFrame:
    return ingest_domain_dataset(PipelineDomain.TRIALS, source_path, file_format=file_format)


def ingest_adverse_events(source_path: Path, *, file_format: FileFormat | None = None) -> pd.DataFrame:
    return ingest_domain_dataset(PipelineDomain.ADVERSE_EVENTS, source_path, file_format=file_format)


def ingest_drug_exposures(source_path: Path, *, file_format: FileFormat | None = None) -> pd.DataFrame:
    return ingest_domain_dataset(PipelineDomain.DRUG_EXPOSURES, source_path, file_format=file_format)
