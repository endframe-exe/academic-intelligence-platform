"""Academic prediction service backed by `/backend/ml/model_v1.joblib` and `model_metrics.json`.

Rules:
- Minimum sufficiency gate: >= 2 recorded assessments required before issuing an estimate.
- Score range: estimate +/- held-out MAE (clamped to 0..100).
- Risk classification: "On Track" | "Needs Revision" | "High Support Priority" via LogisticRegression.
- Feature contributions: transparent linear attribution relative to benchmark mean.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from ml.train_model import ARTIFACT_PATH, METRICS_PATH, train_and_save

FEATURE_LABELS = {
    "internal_assessment_pct": "Internal / CT Average (%)",
    "attendance_pct": "Attendance Rate (%)",
    "weekly_study_hours": "Weekly Study Hours",
    "subject_credits": "Subject Credits",
}

_CACHED_BUNDLE: dict[str, Any] | None = None
_CACHED_METRICS: dict[str, Any] | None = None


def _ensure_artifacts() -> tuple[dict[str, Any], dict[str, Any]]:
    global _CACHED_BUNDLE, _CACHED_METRICS
    if _CACHED_BUNDLE is None or _CACHED_METRICS is None:
        if not ARTIFACT_PATH.exists() or not METRICS_PATH.exists():
            train_and_save()
        _CACHED_BUNDLE = joblib.load(ARTIFACT_PATH)
        _CACHED_METRICS = json.loads(Path(METRICS_PATH).read_text(encoding="utf-8"))
    return _CACHED_BUNDLE, _CACHED_METRICS


def get_model_metrics() -> dict[str, Any]:
    """Return live contents of `/backend/ml/model_metrics.json`."""
    _, metrics = _ensure_artifacts()
    return metrics


def _compute_feature_contributions(
    bundle: dict[str, Any], feature_vec: np.ndarray
) -> list[dict[str, Any]]:
    """Compute per-feature point contributions relative to the benchmark training mean."""
    ridge_pipe = bundle["ridge_explainer"]
    scaler = ridge_pipe.named_steps["scaler"]
    ridge = ridge_pipe.named_steps["model"]

    scaled_x = scaler.transform(feature_vec)[0]
    coefs = ridge.coef_
    raw_vals = feature_vec[0]
    means = bundle["feature_means"]

    contributions: list[dict[str, Any]] = []
    for idx, col in enumerate(bundle["feature_columns"]):
        impact = round(float(coefs[idx] * scaled_x[idx]), 2)
        contributions.append(
            {
                "feature": col,
                "label": FEATURE_LABELS.get(col, col),
                "input_value": round(float(raw_vals[idx]), 2),
                "benchmark_mean": round(float(means[idx]), 2),
                "impact_points": impact,
                "direction": "positive" if impact >= 0 else "negative",
            }
        )
    contributions.sort(key=lambda c: abs(c["impact_points"]), reverse=True)
    return contributions


def predict_academic_outcome(
    *,
    num_assessments: int,
    internal_pct: float,
    attendance_pct: float | None,
    weekly_study_hours: float | None,
    credits: int,
    target_label: str,
) -> dict[str, Any]:
    """Return estimate +/- MAE, risk signal, and feature contributions, or descriptive fallback."""
    bundle, metrics = _ensure_artifacts()
    model_version = str(bundle["model_version"])
    model_name = str(bundle["selected_regressor_name"])
    held_out_mae = float(bundle["held_out_mae"])

    if num_assessments < 2:
        return {
            "is_available": False,
            "predicted_value": None,
            "lower_bound": None,
            "upper_bound": None,
            "risk_signal": "insufficient_data",
            "model_name": model_name,
            "model_version": model_version,
            "metrics_json": {
                "sufficiency_required": 2,
                "assessments_found": num_assessments,
                "held_out_mae": held_out_mae,
                "feature_contributions": [],
                "model_metrics": metrics,
            },
            "explanation": (
                f"Prediction withheld for {target_label}: at least 2 recorded assessments "
                f"are required before computing an estimate (currently {num_assessments} recorded). "
                "Descriptive marks and attendance analytics remain available on your dashboard."
            ),
        }

    att = float(attendance_pct) if attendance_pct is not None else 75.0
    hrs = float(weekly_study_hours) if weekly_study_hours is not None else 12.0
    cred = float(max(credits, 1))
    feature_vec = np.array([[float(internal_pct), att, hrs, cred]], dtype=float)

    regressor = bundle["regressor"]
    classifier = bundle["risk_classifier"]

    raw_est = float(regressor.predict(feature_vec)[0])
    estimate = round(float(np.clip(raw_est, 0.0, 100.0)), 2)
    lower = round(max(0.0, estimate - held_out_mae), 2)
    upper = round(min(100.0, estimate + held_out_mae), 2)

    risk_signal = str(classifier.predict(feature_vec)[0])
    contributions = _compute_feature_contributions(bundle, feature_vec)

    att_note = (
        f"{att:.1f}% recorded attendance"
        if attendance_pct is not None
        else "75.0% baseline attendance assumed (no attendance logged)"
    )
    explanation = (
        f"Estimated next-exam score for {target_label}: {estimate:.1f}% "
        f"(range {lower:.1f}% – {upper:.1f}%, ±{held_out_mae:.2f} held-out MAE). "
        f"Risk support signal: {risk_signal}. Based on {internal_pct:.1f}% recorded average "
        f"across {num_assessments} assessments, {att_note}, and {hrs:.1f} weekly study hours. "
        "Benchmarked on public/synthetic-calibrated data; estimates are guidance, not official NIET grades."
    )

    return {
        "is_available": True,
        "predicted_value": estimate,
        "lower_bound": lower,
        "upper_bound": upper,
        "risk_signal": risk_signal,
        "model_name": model_name,
        "model_version": model_version,
        "metrics_json": {
            "held_out_mae": held_out_mae,
            "assessments_used": num_assessments,
            "feature_contributions": contributions,
            "model_metrics": metrics,
        },
        "explanation": explanation,
    }
