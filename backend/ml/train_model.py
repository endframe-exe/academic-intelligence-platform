"""Train and evaluate regression and risk-classification models with zero student leakage.

Outputs in `/backend/ml/`:
- `model_v1.joblib`: winning regressor, LogisticRegression risk classifier, scaler, and feature metadata.
- `model_metrics.json`: held-out MAE, RMSE, R^2, baseline MAE, and classification F1 / precision / recall.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    precision_score,
    r2_score,
    recall_score,
    root_mean_squared_error,
)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ML_DIR = Path(__file__).resolve().parent
ARTIFACT_PATH = ML_DIR / "model_v1.joblib"
METRICS_PATH = ML_DIR / "model_metrics.json"
MODEL_VERSION = "model_v1"

FEATURE_COLUMNS = [
    "internal_assessment_pct",
    "attendance_pct",
    "weekly_study_hours",
    "subject_credits",
]


def _assign_risk_label(score_pct: float, attendance_pct: float) -> str:
    """Derive 3-class support signal label for training benchmark records."""
    if score_pct < 52.0 or attendance_pct < 68.0:
        return "High Support Priority"
    if score_pct < 70.0 or attendance_pct < 75.0:
        return "Needs Revision"
    return "On Track"


def build_benchmark_dataframe(seed: int = 42, num_students: int = 120) -> pd.DataFrame:
    """Build a lawful synthetic-calibrated student benchmark dataset with student_id groups.

    Multiple subject records belong to each `student_id`. Splitting via GroupShuffleSplit
    prevents the same student's records from appearing in both train and validation/test sets.
    """
    rng = np.random.default_rng(seed)
    rows: list[dict[str, Any]] = []

    for s_idx in range(num_students):
        student_id = f"BENCH-{s_idx:04d}"
        # Student-level latent study consistency so records within a student correlate
        student_aptitude = rng.uniform(42.0, 92.0)
        student_study_base = rng.uniform(4.0, 26.0)
        student_att_base = rng.uniform(58.0, 98.0)

        for subj_slot in range(5):
            internal_pct = float(np.clip(student_aptitude + rng.normal(0, 8.5), 25.0, 99.0))
            attendance_pct = float(np.clip(student_att_base + rng.normal(0, 6.0), 40.0, 100.0))
            study_hours = float(np.clip(student_study_base + rng.normal(0, 2.5), 1.0, 35.0))
            credits = int(rng.choice([1, 2, 3, 4]))

            noise = float(rng.normal(0, 3.8))
            target_score = float(
                np.clip(
                    0.65 * internal_pct
                    + 0.18 * attendance_pct
                    + 0.45 * study_hours
                    + 0.4 * credits
                    + noise
                    - 5.0,
                    18.0,
                    99.0,
                )
            )
            risk_label = _assign_risk_label(target_score, attendance_pct)
            rows.append(
                {
                    "student_id": student_id,
                    "subject_slot": subj_slot,
                    "internal_assessment_pct": round(internal_pct, 2),
                    "attendance_pct": round(attendance_pct, 2),
                    "weekly_study_hours": round(study_hours, 2),
                    "subject_credits": credits,
                    "target_next_exam_pct": round(target_score, 2),
                    "risk_label": risk_label,
                }
            )

    return pd.DataFrame(rows)


def train_and_save() -> dict[str, Any]:
    """Run zero-leakage train/val/test split, compare candidates, and save joblib + metrics JSON."""
    df = build_benchmark_dataframe()
    X = df[FEATURE_COLUMNS].to_numpy(dtype=float)
    y_reg = df["target_next_exam_pct"].to_numpy(dtype=float)
    y_cls = df["risk_label"].to_numpy()
    groups = df["student_id"].to_numpy()

    # 1) Hold out 20% of students for untouched final test evaluation
    gss_test = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=42)
    train_val_idx, test_idx = next(gss_test.split(X, y_reg, groups))

    X_train_val, X_test = X[train_val_idx], X[test_idx]
    y_reg_tv, y_reg_test = y_reg[train_val_idx], y_reg[test_idx]
    y_cls_tv, y_cls_test = y_cls[train_val_idx], y_cls[test_idx]
    groups_tv = groups[train_val_idx]

    # 2) Split remaining 80% into 60% train / 20% validation (0.25 of 80% = 20%)
    gss_val = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=42)
    train_idx, val_idx = next(gss_val.split(X_train_val, y_reg_tv, groups_tv))

    X_train, X_val = X_train_val[train_idx], X_train_val[val_idx]
    y_reg_train, y_reg_val = y_reg_tv[train_idx], y_reg_tv[val_idx]

    # Leakage verification assertions
    assert set(groups_tv[train_idx]).isdisjoint(set(groups_tv[val_idx]))
    assert set(groups[train_val_idx]).isdisjoint(set(groups[test_idx]))

    # Regression candidates evaluated on validation split for model selection
    candidates: dict[str, Pipeline] = {
        "RidgeRegression": Pipeline(
            [("scaler", StandardScaler()), ("model", Ridge(alpha=1.0, random_state=42))]
        ),
        "RandomForestRegressor": Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "model",
                    RandomForestRegressor(
                        n_estimators=120, max_depth=7, min_samples_leaf=3, random_state=42
                    ),
                ),
            ]
        ),
    }

    val_results: dict[str, dict[str, float]] = {}
    winner_name = "RidgeRegression"
    winner_val_rmse = float("inf")

    for name, pipe in candidates.items():
        pipe.fit(X_train, y_reg_train)
        val_preds = pipe.predict(X_val)
        val_rmse = float(root_mean_squared_error(y_reg_val, val_preds))
        val_results[name] = {
            "val_mae": round(float(mean_absolute_error(y_reg_val, val_preds)), 3),
            "val_rmse": round(val_rmse, 3),
            "val_r2": round(float(r2_score(y_reg_val, val_preds)), 3),
        }
        if val_rmse < winner_val_rmse:
            winner_val_rmse = val_rmse
            winner_name = name

    # Refit all candidates on full train+val and evaluate on untouched held-out test set
    dummy = DummyRegressor(strategy="mean").fit(X_train_val, y_reg_tv)
    dummy_test_preds = dummy.predict(X_test)
    baseline_mae = float(mean_absolute_error(y_reg_test, dummy_test_preds))

    test_comparison: dict[str, dict[str, float]] = {}
    fitted_regressors: dict[str, Pipeline] = {}
    for name, pipe in candidates.items():
        pipe.fit(X_train_val, y_reg_tv)
        fitted_regressors[name] = pipe
        t_preds = pipe.predict(X_test)
        test_comparison[name] = {
            "mae": round(float(mean_absolute_error(y_reg_test, t_preds)), 3),
            "rmse": round(float(root_mean_squared_error(y_reg_test, t_preds)), 3),
            "r2": round(float(r2_score(y_reg_test, t_preds)), 3),
        }

    winning_regressor = fitted_regressors[winner_name]
    ridge_explainer = fitted_regressors["RidgeRegression"]
    winner_test_metrics = test_comparison[winner_name]

    # Logistic Regression risk classifier
    risk_classifier = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("model", LogisticRegression(max_iter=1000, random_state=42)),
        ]
    )
    risk_classifier.fit(X_train_val, y_cls_tv)
    cls_preds = risk_classifier.predict(X_test)
    cls_labels = ["On Track", "Needs Revision", "High Support Priority"]
    cls_f1_weighted = float(f1_score(y_cls_test, cls_preds, average="weighted", zero_division=0))
    cls_f1_macro = float(f1_score(y_cls_test, cls_preds, average="macro", zero_division=0))
    cls_precision = float(precision_score(y_cls_test, cls_preds, average="weighted", zero_division=0))
    cls_recall = float(recall_score(y_cls_test, cls_preds, average="weighted", zero_division=0))
    cm = confusion_matrix(y_cls_test, cls_preds, labels=cls_labels).tolist()
    report = classification_report(y_cls_test, cls_preds, labels=cls_labels, output_dict=True, zero_division=0)

    feature_means = X_train_val.mean(axis=0).tolist()
    feature_stds = np.where(X_train_val.std(axis=0) == 0, 1.0, X_train_val.std(axis=0)).tolist()

    metrics_payload: dict[str, Any] = {
        "model_version": MODEL_VERSION,
        "trained_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_summary": {
            "source": "Calibrated synthetic-benchmark student performance records (grouped by student_id)",
            "total_records": int(len(df)),
            "unique_students": int(df["student_id"].nunique()),
            "split_protocol": "GroupShuffleSplit 60% train / 20% validation / 20% held-out test (zero student leakage)",
            "train_records": int(len(X_train)),
            "validation_records": int(len(X_val)),
            "test_records": int(len(X_test)),
        },
        "features": FEATURE_COLUMNS,
        "selected_regressor": winner_name,
        "baseline_mean_mae": round(baseline_mae, 3),
        "held_out_regression": winner_test_metrics,
        "validation_selection": val_results,
        "candidate_test_comparison": test_comparison,
        "held_out_classification": {
            "classifier_name": "LogisticRegression",
            "labels": cls_labels,
            "f1_weighted": round(cls_f1_weighted, 3),
            "f1_macro": round(cls_f1_macro, 3),
            "precision_weighted": round(cls_precision, 3),
            "recall_weighted": round(cls_recall, 3),
            "confusion_matrix": cm,
            "per_class": {
                lbl: {
                    "precision": round(float(report[lbl]["precision"]), 3),
                    "recall": round(float(report[lbl]["recall"]), 3),
                    "f1": round(float(report[lbl]["f1-score"]), 3),
                    "support": int(report[lbl]["support"]),
                }
                for lbl in cls_labels
            },
        },
        "disclaimer": (
            "Benchmarked on public/synthetic-calibrated data; estimates are guidance, "
            "not official NIET grades."
        ),
    }

    artifact_bundle = {
        "model_version": MODEL_VERSION,
        "selected_regressor_name": winner_name,
        "regressor": winning_regressor,
        "ridge_explainer": ridge_explainer,
        "risk_classifier": risk_classifier,
        "feature_columns": FEATURE_COLUMNS,
        "feature_means": feature_means,
        "feature_stds": feature_stds,
        "held_out_mae": winner_test_metrics["mae"],
        "metrics": metrics_payload,
    }

    ML_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact_bundle, ARTIFACT_PATH)
    METRICS_PATH.write_text(json.dumps(metrics_payload, indent=2), encoding="utf-8")
    return metrics_payload


if __name__ == "__main__":
    summary = train_and_save()
    print(
        f"Saved {ARTIFACT_PATH.name} & {METRICS_PATH.name} | "
        f"Winner: {summary['selected_regressor']} | "
        f"Test MAE={summary['held_out_regression']['mae']}, "
        f"RMSE={summary['held_out_regression']['rmse']}, "
        f"R2={summary['held_out_regression']['r2']}, "
        f"Risk F1={summary['held_out_classification']['f1_weighted']}"
    )
