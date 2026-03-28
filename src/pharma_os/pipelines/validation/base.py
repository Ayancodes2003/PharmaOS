"""Reusable validation quality-gate utilities for ingestion datasets."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import pandas as pd

from pharma_os.pipelines.common.contracts import DataQualityIssue, PipelineDomain, ValidationReport


@dataclass(slots=True)
class ValidationSpec:
    """Validation contract for a domain dataset."""

    domain: PipelineDomain
    required_columns: list[str]
    optional_columns: list[str]
    critical_columns: list[str]
    duplicate_key_columns: list[str]
    numeric_columns: list[str]
    datetime_columns: list[str]
    categorical_columns: dict[str, set[str]]


def build_validation_report(df: pd.DataFrame, spec: ValidationSpec) -> ValidationReport:
    """Validate DataFrame against a domain validation spec."""
    issues: list[DataQualityIssue] = []

    actual_columns = list(df.columns)
    missing_columns = [col for col in spec.required_columns if col not in actual_columns]
    allowed_columns = set(spec.required_columns + spec.optional_columns)
    unexpected_columns = [col for col in actual_columns if col not in allowed_columns]

    for missing in missing_columns:
        issues.append(
            DataQualityIssue(
                code="MISSING_REQUIRED_COLUMN",
                message=f"Missing required column: {missing}",
                severity="error",
                column=missing,
            )
        )

    if unexpected_columns:
        issues.append(
            DataQualityIssue(
                code="UNEXPECTED_COLUMNS",
                message=f"Unexpected columns detected: {', '.join(sorted(unexpected_columns))}",
                severity="warning",
                metadata={"columns": sorted(unexpected_columns)},
            )
        )

    for critical in spec.critical_columns:
        if critical in df.columns:
            missing_count = int(df[critical].isna().sum())
            if missing_count > 0:
                issues.append(
                    DataQualityIssue(
                        code="MISSING_CRITICAL_VALUES",
                        message=f"Critical field contains missing values: {critical}",
                        severity="error",
                        column=critical,
                        row_count=missing_count,
                    )
                )

    duplicate_count = 0
    if all(col in df.columns for col in spec.duplicate_key_columns):
        duplicate_count = int(df.duplicated(subset=spec.duplicate_key_columns, keep=False).sum())
        if duplicate_count > 0:
            issues.append(
                DataQualityIssue(
                    code="DUPLICATE_KEYS",
                    message="Duplicate records detected on business key columns",
                    severity="warning",
                    row_count=duplicate_count,
                    metadata={"keys": spec.duplicate_key_columns},
                )
            )

    for numeric_col in spec.numeric_columns:
        if numeric_col in df.columns:
            coerced = pd.to_numeric(df[numeric_col], errors="coerce")
            invalid_numeric = int(coerced.isna().sum() - df[numeric_col].isna().sum())
            if invalid_numeric > 0:
                issues.append(
                    DataQualityIssue(
                        code="NUMERIC_TYPE_MISMATCH",
                        message=f"Non-numeric values detected in numeric column: {numeric_col}",
                        severity="error",
                        column=numeric_col,
                        row_count=invalid_numeric,
                    )
                )

    for date_col in spec.datetime_columns:
        if date_col in df.columns:
            parsed = pd.to_datetime(df[date_col], errors="coerce", utc=True)
            invalid_dates = int(parsed.isna().sum() - df[date_col].isna().sum())
            if invalid_dates > 0:
                issues.append(
                    DataQualityIssue(
                        code="DATETIME_PARSE_ERROR",
                        message=f"Unparseable datetime values detected: {date_col}",
                        severity="error",
                        column=date_col,
                        row_count=invalid_dates,
                    )
                )

    for category_col, allowed_values in spec.categorical_columns.items():
        if category_col in df.columns:
            normalized = (
                df[category_col]
                .dropna()
                .astype("string")
                .str.strip()
                .str.lower()
            )
            invalid_values = sorted(set(normalized) - set(allowed_values))
            if invalid_values:
                issues.append(
                    DataQualityIssue(
                        code="CATEGORY_OUT_OF_RANGE",
                        message=f"Values outside allowed set detected in {category_col}",
                        severity="warning",
                        column=category_col,
                        metadata={"invalid_values": invalid_values[:25]},
                    )
                )

    passed = not any(issue.severity == "error" for issue in issues)

    return ValidationReport(
        domain=spec.domain,
        passed=passed,
        row_count=len(df.index),
        required_columns=spec.required_columns,
        missing_columns=missing_columns,
        unexpected_columns=unexpected_columns,
        duplicate_count=duplicate_count,
        issues=issues,
    )


def require_validation_pass(report: ValidationReport) -> None:
    """Raise ValueError if validation report contains error-severity issues."""
    if report.passed:
        return

    error_messages = [issue.message for issue in report.issues if issue.severity == "error"]
    raise ValueError(
        f"Validation failed for {report.domain.value}: "
        + " | ".join(error_messages)
    )


def validate_and_enforce(df: pd.DataFrame, spec: ValidationSpec) -> ValidationReport:
    """Build validation report and enforce pass/fail quality gate."""
    report = build_validation_report(df, spec)
    require_validation_pass(report)
    return report


DomainCleaner = Callable[[pd.DataFrame], pd.DataFrame]
