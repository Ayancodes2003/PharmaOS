"""Source loaders for Phase 10 BI export generation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from pharma_os.core.settings import Settings
from pharma_os.db.models import (
    AuditLog,
    EligibilityPrediction,
    RecruitmentRanking,
    SafetyPrediction,
)
from pharma_os.pipelines.common.io import read_dataset


class ExportSourceLoader:
    """Loads existing marts, model metadata, and operational traces for exports."""

    def __init__(self, settings: Settings):
        self.settings = settings

    def resolve_phase5_run_id(self, run_id: str | None = None) -> str:
        """Resolve source Phase 5 run id; latest when omitted."""
        if run_id:
            return run_id

        reports_dir = Path(self.settings.phase5_reports_path)
        candidates = sorted(
            [item for item in reports_dir.glob("phase5_manifest_*.json") if item.is_file()],
            key=lambda item: item.stat().st_mtime,
            reverse=True,
        )
        if not candidates:
            raise FileNotFoundError(f"No Phase 5 manifests found in {reports_dir}")

        latest_name = candidates[0].stem
        return latest_name.replace("phase5_manifest_", "")

    def load_phase5_outputs(self, run_id: str) -> tuple[dict[str, pd.DataFrame], dict[str, Any]]:
        """Load Phase 5 feature and mart outputs from manifest references."""
        manifest_path = Path(self.settings.phase5_reports_path) / f"phase5_manifest_{run_id}.json"
        if not manifest_path.exists():
            raise FileNotFoundError(f"Phase 5 manifest not found: {manifest_path}")

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        outputs: dict[str, pd.DataFrame] = {}

        for section in ("feature_outputs", "analytics_outputs"):
            for name, path_raw in manifest.get(section, {}).items():
                path = Path(path_raw)
                outputs[name] = read_dataset(path)

        return outputs, manifest

    def load_model_training_metadata(self) -> pd.DataFrame:
        """Load latest model training metadata per use case from Phase 6 reports."""
        rows: list[dict[str, Any]] = []
        root = Path(self.settings.phase6_reports_path)

        for use_case in ("eligibility", "safety", "recruitment"):
            use_case_dir = root / use_case
            if not use_case_dir.exists():
                continue

            runs = sorted([item for item in use_case_dir.iterdir() if item.is_dir()], key=lambda item: item.stat().st_mtime)
            if not runs:
                continue

            for run_dir in runs:
                metadata_path = run_dir / "training_metadata.json"
                if not metadata_path.exists():
                    continue

                payload = json.loads(metadata_path.read_text(encoding="utf-8"))
                target_summary = payload.get("target_summary", {})
                rows.append(
                    {
                        "use_case": use_case,
                        "training_run_id": run_dir.name,
                        "model_name": payload.get("model_name", "unknown"),
                        "model_artifact_path": payload.get("model_artifact_path")
                        or payload.get("ranking_config_path"),
                        "feature_manifest_path": payload.get("feature_manifest_path"),
                        "label_source_type": target_summary.get("label_source_type", "unknown"),
                        "target_mode": target_summary.get("target_mode", "unknown"),
                        "weak_supervision": bool(target_summary.get("weak_supervision", False)),
                        "created_at": payload.get("training_finished_at") or payload.get("training_started_at"),
                    }
                )

        return pd.DataFrame(rows)

    def load_inference_activity(self, session: Session) -> pd.DataFrame:
        """Load persisted inference activity from SQL prediction/ranking tables."""
        rows: list[dict[str, Any]] = []

        eligibility_stmt: Select[tuple[EligibilityPrediction]] = select(EligibilityPrediction)
        for item in session.scalars(eligibility_stmt).all():
            rows.append(
                {
                    "use_case": "eligibility",
                    "inference_timestamp": item.inference_timestamp,
                    "model_name": item.model_name,
                    "model_version": item.model_version,
                    "score": float(item.eligibility_probability),
                    "confidence": float(item.confidence),
                }
            )

        safety_stmt: Select[tuple[SafetyPrediction]] = select(SafetyPrediction)
        for item in session.scalars(safety_stmt).all():
            rows.append(
                {
                    "use_case": "safety",
                    "inference_timestamp": item.inference_timestamp,
                    "model_name": item.model_name,
                    "model_version": item.model_version,
                    "score": float(item.risk_score),
                    "confidence": float(item.confidence),
                }
            )

        recruitment_stmt: Select[tuple[RecruitmentRanking]] = select(RecruitmentRanking)
        for item in session.scalars(recruitment_stmt).all():
            rows.append(
                {
                    "use_case": "recruitment",
                    "inference_timestamp": item.generated_at,
                    "model_name": "score_based_prioritizer",
                    "model_version": item.model_version,
                    "score": float(item.ranking_score),
                    "confidence": None,
                }
            )

        return pd.DataFrame(rows)

    def load_workflow_usage(self, session: Session) -> pd.DataFrame:
        """Load workflow/service usage events from audit logs."""
        stmt: Select[tuple[AuditLog]] = select(AuditLog)
        rows: list[dict[str, Any]] = []

        for item in session.scalars(stmt).all():
            rows.append(
                {
                    "actor_type": item.actor_type.value,
                    "actor_id": item.actor_id,
                    "action_type": item.action_type,
                    "entity_type": item.entity_type,
                    "entity_id": item.entity_id,
                    "trace_id": item.trace_id,
                    "occurred_at": item.occurred_at,
                }
            )

        return pd.DataFrame(rows)

    async def load_agent_trace_activity(self, mongo_db: Any | None) -> pd.DataFrame:
        """Load agent trace activity rows from MongoDB trace collection."""
        if mongo_db is None:
            return pd.DataFrame()

        collection = mongo_db.get_collection("agent_traces")
        docs = await collection.find({}).sort("timestamp", -1).to_list(length=10000)

        rows: list[dict[str, Any]] = []
        for doc in docs:
            metadata = doc.get("metadata", {}) or {}
            rows.append(
                {
                    "trace_id": doc.get("trace_id"),
                    "timestamp": doc.get("timestamp"),
                    "agent_type": metadata.get("agent_type"),
                    "agent_name": metadata.get("agent_name"),
                    "success": metadata.get("success"),
                    "execution_time_ms": metadata.get("execution_time_ms"),
                    "tool_calls_count": metadata.get("tool_calls_count", 0),
                    "provider": metadata.get("provider"),
                    "model_name": metadata.get("model_name"),
                    "stub_mode": metadata.get("stub_mode"),
                    "request_type": doc.get("request_type"),
                }
            )

        return pd.DataFrame(rows)
