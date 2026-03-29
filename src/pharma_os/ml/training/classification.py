"""Reusable binary classification training pipeline for Phase 6 use cases."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from pharma_os.ml.evaluation.classification import evaluate_binary_classifier


@dataclass(slots=True)
class ClassificationTrainingOutput:
    """In-memory output of classification candidate training and selection."""

    selected_model_name: str
    selected_model: Pipeline
    evaluations: dict[str, dict[str, dict[str, float] | dict[str, int]]]
    class_balance: dict[str, float]
    feature_columns: list[str]
    split_sizes: dict[str, int]
    model_selection_summary: dict[str, object]


def train_binary_classification_models(
    *,
    X: pd.DataFrame,
    y: pd.Series,
    random_state: int = 42,
) -> ClassificationTrainingOutput:
    """Train baseline and stronger classifiers with reproducible data splits."""
    X_train_val, X_test, y_train_val, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=random_state,
        stratify=y,
    )

    X_train, X_val, y_train, y_val = train_test_split(
        X_train_val,
        y_train_val,
        test_size=0.25,
        random_state=random_state,
        stratify=y_train_val,
    )

    preprocessor = _build_preprocessor(X)
    class_weight = _class_weight_strategy(y_train)

    candidates: dict[str, Pipeline] = {
        "logistic_regression": Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                (
                    "model",
                    LogisticRegression(
                        max_iter=1000,
                        class_weight=class_weight,
                        random_state=random_state,
                    ),
                ),
            ]
        ),
        "random_forest": Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                (
                    "model",
                    RandomForestClassifier(
                        n_estimators=300,
                        min_samples_leaf=2,
                        class_weight=class_weight,
                        random_state=random_state,
                        n_jobs=-1,
                    ),
                ),
            ]
        ),
    }

    evaluations: dict[str, dict[str, dict[str, float] | dict[str, int]]] = {}
    best_name = ""
    best_score = -1.0

    for name, pipeline in candidates.items():
        pipeline.fit(X_train, y_train)

        val_eval = _evaluate_split(pipeline, X_val, y_val)
        test_eval = _evaluate_split(pipeline, X_test, y_test)
        evaluations[name] = {
            "validation": val_eval,
            "test": test_eval,
        }

        current_score = float(val_eval["metrics"].get("roc_auc", val_eval["metrics"]["f1"]))
        if current_score > best_score:
            best_score = current_score
            best_name = name

    selected = candidates[best_name]
    selected.fit(X_train_val, y_train_val)

    final_test_eval = _evaluate_split(selected, X_test, y_test)
    evaluations[best_name]["test_retrained"] = final_test_eval

    candidate_validation_scores = {
        name: float(payload["validation"]["metrics"].get("roc_auc", payload["validation"]["metrics"]["f1"]))
        for name, payload in evaluations.items()
    }

    return ClassificationTrainingOutput(
        selected_model_name=best_name,
        selected_model=selected,
        evaluations=evaluations,
        class_balance={
            "positive_ratio": float(y.mean()),
            "negative_ratio": float(1.0 - y.mean()),
        },
        feature_columns=list(X.columns),
        split_sizes={
            "train_rows": int(len(X_train.index)),
            "validation_rows": int(len(X_val.index)),
            "test_rows": int(len(X_test.index)),
            "train_validation_rows": int(len(X_train_val.index)),
            "full_rows": int(len(X.index)),
        },
        model_selection_summary={
            "selection_metric": "validation_roc_auc_with_f1_fallback",
            "candidate_validation_scores": candidate_validation_scores,
            "selected_model": best_name,
            "selected_score": float(best_score),
            "selection_rule": "Choose candidate with best validation ROC-AUC; if unavailable, fallback to validation F1.",
        },
    )


def _build_preprocessor(X: pd.DataFrame) -> ColumnTransformer:
    categorical_columns = [
        column
        for column in X.columns
        if str(X[column].dtype) in {"object", "string", "category", "bool"}
    ]
    numeric_columns = [column for column in X.columns if column not in categorical_columns]

    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, numeric_columns),
            ("categorical", categorical_pipeline, categorical_columns),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )


def _evaluate_split(model: Pipeline, X: pd.DataFrame, y: pd.Series) -> dict[str, dict[str, float] | dict[str, int]]:
    y_pred = model.predict(X)
    y_score = _extract_score(model, X)
    return evaluate_binary_classifier(
        y_true=np.asarray(y),
        y_pred=np.asarray(y_pred),
        y_score=y_score,
    )


def _extract_score(model: Pipeline, X: pd.DataFrame) -> np.ndarray | None:
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(X)
        if proba.ndim == 2 and proba.shape[1] > 1:
            return proba[:, 1]
    if hasattr(model, "decision_function"):
        scores = model.decision_function(X)
        return np.asarray(scores)
    return None


def _class_weight_strategy(y: pd.Series) -> str | None:
    ratio = float(y.mean()) if len(y.index) > 0 else 0.0
    if ratio < 0.35 or ratio > 0.65:
        return "balanced"
    return None
