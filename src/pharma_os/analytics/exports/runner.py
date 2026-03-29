"""Phase 10 BI export orchestration runner."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from pharma_os.analytics.exports.builders import (
    build_agent_ops_exports,
    build_eligibility_exports,
    build_model_monitoring_exports,
    build_recruitment_exports,
    build_safety_exports,
)
from pharma_os.analytics.exports.contracts import ExportFormat, ExportRunSummary, ExportedTable
from pharma_os.analytics.exports.sources import ExportSourceLoader
from pharma_os.analytics.exports.writers import write_export_table
from pharma_os.pipelines.common.io import ensure_directory, write_json


class BIExportRunner:
    """Generates Power BI-ready export groups from existing platform outputs."""

    def __init__(self, *, settings) -> None:
        self.settings = settings
        self.source_loader = ExportSourceLoader(settings)

    async def run(
        self,
        *,
        session: Session,
        mongo_db: Any | None,
        phase5_run_id: str | None = None,
        export_run_id: str | None = None,
        formats: tuple[ExportFormat, ...] = (ExportFormat.CSV,),
    ) -> dict[str, Any]:
        """Generate all BI export groups and write manifest."""
        started_at = datetime.now(UTC)
        source_run_id = self.source_loader.resolve_phase5_run_id(phase5_run_id)
        effective_export_run_id = export_run_id or datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")

        phase5_outputs, phase5_manifest = self.source_loader.load_phase5_outputs(source_run_id)
        model_training_metadata = self.source_loader.load_model_training_metadata()
        inference_activity = self.source_loader.load_inference_activity(session)
        workflow_usage = self.source_loader.load_workflow_usage(session)
        agent_trace_activity = await self.source_loader.load_agent_trace_activity(mongo_db)

        grouped_tables: dict[str, dict[str, pd.DataFrame]] = {
            "recruitment": build_recruitment_exports(phase5_outputs),
            "eligibility": build_eligibility_exports(phase5_outputs),
            "safety": build_safety_exports(phase5_outputs),
            "model_monitoring": build_model_monitoring_exports(
                phase5_outputs,
                model_training_metadata=model_training_metadata,
                inference_activity=inference_activity,
            ),
            "agent_ops": build_agent_ops_exports(
                agent_trace_activity=agent_trace_activity,
                workflow_usage=workflow_usage,
            ),
        }

        output_root = Path(self.settings.artifact_root) / "exports" / "power_bi" / effective_export_run_id
        ensure_directory(output_root)

        exported_tables: list[ExportedTable] = []

        for group, tables in grouped_tables.items():
            group_dir = ensure_directory(output_root / group)
            for table_name, table in tables.items():
                for format in formats:
                    path = write_export_table(
                        output_dir=group_dir,
                        table_name=table_name,
                        export_run_id=effective_export_run_id,
                        df=table,
                        format=format,
                    )
                    exported_tables.append(
                        ExportedTable(
                            group=group,
                            table_name=table_name,
                            format=format,
                            path=path,
                            row_count=int(len(table.index)),
                            column_count=int(len(table.columns)),
                            columns=[str(column) for column in table.columns],
                        )
                    )

        finished_at = datetime.now(UTC)
        groups_summary: dict[str, dict[str, int]] = {}
        for item in exported_tables:
            if item.group not in groups_summary:
                groups_summary[item.group] = {"table_count": 0, "total_rows": 0}
            groups_summary[item.group]["table_count"] += 1
            groups_summary[item.group]["total_rows"] += item.row_count

        training_run_ids: dict[str, str] = {}
        if not model_training_metadata.empty and "use_case" in model_training_metadata.columns and "training_run_id" in model_training_metadata.columns:
            for _, row in model_training_metadata.dropna(subset=["use_case", "training_run_id"]).iterrows():
                training_run_ids[str(row["use_case"])] = str(row["training_run_id"])

        summary = ExportRunSummary(
            export_run_id=effective_export_run_id,
            source_phase5_run_id=source_run_id,
            started_at=started_at,
            finished_at=finished_at,
            output_root=output_root,
            table_count=len(exported_tables),
            total_rows=int(sum(item.row_count for item in exported_tables)),
            groups=groups_summary,
            tables=exported_tables,
            source_refs={
                "phase5_manifest": str(Path(self.settings.phase5_reports_path) / f"phase5_manifest_{source_run_id}.json"),
                "source_run_ids": {
                    "phase5": source_run_id,
                    "phase6_training": training_run_ids,
                },
                "phase5_feature_outputs": phase5_manifest.get("feature_outputs", {}),
                "phase5_analytics_outputs": phase5_manifest.get("analytics_outputs", {}),
                "phase6_reports_root": str(self.settings.phase6_reports_path),
                "phase7_reports_root": str(self.settings.phase7_reports_path),
            },
        )

        manifest_dir = ensure_directory(Path(self.settings.artifact_root) / "reports" / "phase10")
        manifest_path = write_json(summary.to_dict(), manifest_dir / f"phase10_export_manifest_{effective_export_run_id}.json")

        return {
            "export_run_id": effective_export_run_id,
            "source_phase5_run_id": source_run_id,
            "manifest_path": str(manifest_path),
            "output_root": str(output_root),
            "table_count": summary.table_count,
            "total_rows": summary.total_rows,
            "groups": summary.groups,
        }
