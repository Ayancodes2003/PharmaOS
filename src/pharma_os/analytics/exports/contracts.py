"""Contracts for Phase 10 BI export orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class ExportFormat(str, Enum):
    """Supported output formats for BI exports."""

    CSV = "csv"
    PARQUET = "parquet"


@dataclass(slots=True)
class ExportedTable:
    """Materialized export table metadata for manifest tracking."""

    group: str
    table_name: str
    format: ExportFormat
    path: Path
    row_count: int
    column_count: int
    columns: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "group": self.group,
            "table_name": self.table_name,
            "format": self.format.value,
            "path": str(self.path),
            "row_count": self.row_count,
            "column_count": self.column_count,
            "columns": self.columns,
        }


@dataclass(slots=True)
class ExportRunSummary:
    """High-level run summary for BI export manifests."""

    export_run_id: str
    source_phase5_run_id: str
    started_at: datetime
    finished_at: datetime
    output_root: Path
    table_count: int
    total_rows: int
    groups: dict[str, dict[str, int]]
    tables: list[ExportedTable]
    source_refs: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "export_run_id": self.export_run_id,
            "source_phase5_run_id": self.source_phase5_run_id,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "output_root": str(self.output_root),
            "table_count": self.table_count,
            "total_rows": self.total_rows,
            "groups": self.groups,
            "tables": [table.to_dict() for table in self.tables],
            "source_refs": self.source_refs,
        }
