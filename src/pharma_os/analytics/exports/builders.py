"""BI dataset builders grouped by dashboard/reporting domain."""

from __future__ import annotations

from typing import Any

import pandas as pd


def build_recruitment_exports(outputs: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Build recruitment funnel and trial ops export tables."""
    recruitment_features = outputs.get("recruitment_features", pd.DataFrame())
    screening_funnel = outputs.get("patient_screening_funnel", pd.DataFrame())
    recruitment_kpis = outputs.get("recruitment_kpis", pd.DataFrame())

    trial_recruitment_funnel = screening_funnel.copy()

    trial_candidate_summary = recruitment_kpis.copy()

    if recruitment_features.empty:
        recruitment_priority_distribution = pd.DataFrame(
            columns=["trial_code", "priority_bucket", "candidate_count"]
        )
        top_candidate_rollups = pd.DataFrame(
            columns=[
                "trial_code",
                "external_patient_id",
                "ranking_score_component",
                "urgency_proxy",
                "trial_readiness_indicator",
                "exclusion_risk_signal",
            ]
        )
    else:
        scored = recruitment_features.copy()
        scored["priority_bucket"] = pd.cut(
            scored["ranking_score_component"],
            bins=[-999, 0, 2, 4, 999],
            labels=["low", "moderate", "high", "critical"],
        ).astype("string")

        recruitment_priority_distribution = (
            scored.groupby(["trial_code", "priority_bucket"], dropna=False)
            .agg(candidate_count=("external_patient_id", "count"))
            .reset_index()
            .sort_values(["trial_code", "priority_bucket"], kind="stable")
        )

        top_candidate_rollups = (
            scored.sort_values(["trial_code", "ranking_score_component"], ascending=[True, False], kind="stable")
            .groupby("trial_code", dropna=False)
            .head(25)
            .reindex(
                columns=[
                    "trial_code",
                    "external_patient_id",
                    "ranking_score_component",
                    "urgency_proxy",
                    "trial_readiness_indicator",
                    "exclusion_risk_signal",
                ]
            )
            .reset_index(drop=True)
        )

    return {
        "trial_recruitment_funnel": trial_recruitment_funnel,
        "trial_candidate_summary": trial_candidate_summary,
        "recruitment_priority_distribution": recruitment_priority_distribution,
        "top_candidate_rollups": top_candidate_rollups,
    }


def build_eligibility_exports(outputs: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Build eligibility analytics export tables."""
    eligibility_features = outputs.get("eligibility_features", pd.DataFrame())
    trial_eligibility = outputs.get("trial_eligibility", pd.DataFrame())

    if eligibility_features.empty:
        patient_eligibility_summary = pd.DataFrame(
            columns=[
                "external_patient_id",
                "trial_code",
                "trial_fit_score_component",
                "condition_match",
                "diagnosis_indication_match",
                "serious_event_count",
                "comorbidity_count",
                "eligibility_bucket",
            ]
        )
        eligibility_fit_breakdowns = pd.DataFrame(columns=["trial_code", "fit_bucket", "candidate_count"])
        exclusion_indicator_summary = pd.DataFrame(
            columns=[
                "trial_code",
                "serious_event_exclusions",
                "high_comorbidity_exclusions",
                "inactive_patient_exclusions",
            ]
        )
    else:
        scored = eligibility_features.copy()
        scored["eligibility_bucket"] = pd.cut(
            scored["trial_fit_score_component"],
            bins=[-999, 1, 3, 5, 999],
            labels=["low_fit", "borderline_fit", "good_fit", "high_fit"],
        ).astype("string")

        patient_eligibility_summary = scored.reindex(
            columns=[
                "external_patient_id",
                "trial_code",
                "trial_fit_score_component",
                "condition_match",
                "diagnosis_indication_match",
                "serious_event_count",
                "comorbidity_count",
                "eligibility_bucket",
            ]
        )

        eligibility_fit_breakdowns = (
            scored.groupby(["trial_code", "eligibility_bucket"], dropna=False)
            .agg(candidate_count=("external_patient_id", "count"))
            .reset_index()
            .rename(columns={"eligibility_bucket": "fit_bucket"})
        )

        exclusion_indicator_summary = (
            scored.groupby("trial_code", dropna=False)
            .agg(
                serious_event_exclusions=("serious_event_count", lambda s: int((s > 0).sum())),
                high_comorbidity_exclusions=("comorbidity_count", lambda s: int((s >= 3).sum())),
                inactive_patient_exclusions=("is_active_patient", lambda s: int((s.fillna(0) == 0).sum())),
            )
            .reset_index()
        )

    return {
        "patient_eligibility_summary": patient_eligibility_summary,
        "trial_eligibility_distribution": trial_eligibility.copy(),
        "eligibility_fit_breakdowns": eligibility_fit_breakdowns,
        "exclusion_indicator_summary": exclusion_indicator_summary,
    }


def build_safety_exports(outputs: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Build adverse event and safety monitoring export tables."""
    adverse_monitoring = outputs.get("adverse_event_monitoring", pd.DataFrame())
    safety_features = outputs.get("safety_features", pd.DataFrame())

    adverse_event_summary = adverse_monitoring.copy()

    if adverse_monitoring.empty:
        severity_distribution = pd.DataFrame(columns=["severity", "is_serious", "event_count"])
    else:
        severity_distribution = (
            adverse_monitoring.groupby(["severity", "is_serious"], dropna=False)
            .agg(event_count=("event_count", "sum"))
            .reset_index()
            .sort_values(["event_count", "severity"], ascending=[False, True], kind="stable")
        )

    if safety_features.empty:
        safety_signal_summary = pd.DataFrame(
            columns=["drug_name", "patient_count", "avg_safety_risk_component", "high_risk_patient_count"]
        )
        exposure_risk_rollups = pd.DataFrame(
            columns=[
                "patient_external_id",
                "drug_name",
                "active_exposure_count",
                "prior_event_count",
                "serious_event_count",
                "safety_risk_component",
            ]
        )
    else:
        safety_signal_summary = (
            safety_features.groupby("drug_name", dropna=False)
            .agg(
                patient_count=("patient_external_id", "nunique"),
                avg_safety_risk_component=("safety_risk_component", "mean"),
                high_risk_patient_count=("safety_risk_component", lambda s: int((s >= 5).sum())),
            )
            .reset_index()
            .sort_values(["high_risk_patient_count", "avg_safety_risk_component"], ascending=[False, False])
        )

        exposure_risk_rollups = safety_features.reindex(
            columns=[
                "patient_external_id",
                "drug_name",
                "active_exposure_count",
                "prior_event_count",
                "serious_event_count",
                "safety_risk_component",
            ]
        )

    return {
        "adverse_event_summary": adverse_event_summary,
        "severity_distribution": severity_distribution,
        "safety_signal_summary": safety_signal_summary,
        "exposure_risk_rollups": exposure_risk_rollups,
    }


def build_model_monitoring_exports(
    outputs: dict[str, pd.DataFrame],
    *,
    model_training_metadata: pd.DataFrame,
    inference_activity: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """Build model monitoring and provenance export tables."""
    feature_readiness_summary = outputs.get("model_monitoring_support", pd.DataFrame()).copy()

    model_training_summary = model_training_metadata.copy()

    if model_training_metadata.empty:
        model_artifact_registry_export = pd.DataFrame(
            columns=["use_case", "training_run_id", "model_name", "model_artifact_path", "created_at"]
        )
        label_source_summary = pd.DataFrame(columns=["use_case", "label_source_type", "target_mode", "run_count"])
    else:
        model_artifact_registry_export = model_training_metadata.reindex(
            columns=["use_case", "training_run_id", "model_name", "model_artifact_path", "created_at"]
        )
        label_source_summary = (
            model_training_metadata.groupby(["use_case", "label_source_type", "target_mode"], dropna=False)
            .agg(run_count=("training_run_id", "count"))
            .reset_index()
        )

    if inference_activity.empty:
        inference_activity_summary = pd.DataFrame(
            columns=["use_case", "event_date", "prediction_count", "avg_score", "avg_confidence"]
        )
    else:
        scored = inference_activity.copy()
        scored["event_date"] = pd.to_datetime(scored["inference_timestamp"], errors="coerce").dt.date
        inference_activity_summary = (
            scored.groupby(["use_case", "event_date"], dropna=False)
            .agg(
                prediction_count=("model_name", "count"),
                avg_score=("score", "mean"),
                avg_confidence=("confidence", "mean"),
            )
            .reset_index()
            .sort_values(["event_date", "use_case"], ascending=[False, True], kind="stable")
        )

    return {
        "model_training_summary": model_training_summary,
        "model_artifact_registry_export": model_artifact_registry_export,
        "feature_readiness_summary": feature_readiness_summary,
        "label_source_summary": label_source_summary,
        "inference_activity_summary": inference_activity_summary,
    }


def build_agent_ops_exports(
    *,
    agent_trace_activity: pd.DataFrame,
    workflow_usage: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """Build agent and operational intelligence export tables."""
    if agent_trace_activity.empty:
        agent_execution_summary = pd.DataFrame(
            columns=["agent_type", "event_date", "execution_count", "success_count", "avg_execution_time_ms"]
        )
        agent_provider_mode_summary = pd.DataFrame(
            columns=["provider", "model_name", "stub_mode", "execution_count"]
        )
    else:
        traces = agent_trace_activity.copy()
        traces["event_date"] = pd.to_datetime(traces["timestamp"], errors="coerce").dt.date
        traces["success_int"] = traces["success"].fillna(False).astype(int)

        agent_execution_summary = (
            traces.groupby(["agent_type", "event_date"], dropna=False)
            .agg(
                execution_count=("trace_id", "count"),
                success_count=("success_int", "sum"),
                avg_execution_time_ms=("execution_time_ms", "mean"),
            )
            .reset_index()
            .sort_values(["event_date", "agent_type"], ascending=[False, True], kind="stable")
        )

        agent_provider_mode_summary = (
            traces.groupby(["provider", "model_name", "stub_mode"], dropna=False)
            .agg(execution_count=("trace_id", "count"))
            .reset_index()
            .sort_values("execution_count", ascending=False, kind="stable")
        )

    if workflow_usage.empty:
        workflow_usage_summary = pd.DataFrame(
            columns=["event_date", "actor_type", "actor_id", "action_type", "event_count"]
        )
    else:
        usage = workflow_usage.copy()
        usage["event_date"] = pd.to_datetime(usage["occurred_at"], errors="coerce").dt.date
        workflow_usage_summary = (
            usage.groupby(["event_date", "actor_type", "actor_id", "action_type"], dropna=False)
            .agg(event_count=("action_type", "count"))
            .reset_index()
            .sort_values(["event_date", "event_count"], ascending=[False, False], kind="stable")
        )

    return {
        "agent_execution_summary": agent_execution_summary,
        "agent_trace_activity": agent_trace_activity.copy(),
        "agent_provider_mode_summary": agent_provider_mode_summary,
        "workflow_usage_summary": workflow_usage_summary,
    }
