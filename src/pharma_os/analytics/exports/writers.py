"""Writers for Phase 5 feature and analytics artifacts."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from pharma_os.pipelines.common.io import ensure_directory, write_json


def write_named_dataset(*, output_dir: Path, name: str, run_id: str, df: pd.DataFrame) -> Path:
    """Write dataset artifact with deterministic naming under an output group directory."""
    ensure_directory(output_dir)
    path = output_dir / f"{name}_{run_id}.csv"
    stable_df = df.sort_index(axis=1)
    stable_df.to_csv(path, index=False)
    return path


def write_run_manifest(*, output_dir: Path, run_id: str, payload: dict[str, object]) -> Path:
    """Write run manifest for downstream orchestration and reproducibility."""
    ensure_directory(output_dir)
    return write_json(payload, output_dir / f"phase5_manifest_{run_id}.json")
