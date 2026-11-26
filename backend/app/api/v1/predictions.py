from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.v1.analytics import compute_dashboard_state
from app.core.database import get_db
from app.models.academic import Prediction, StudentProfile, Subject, User
from app.schemas.academic import PredictionOut, PredictionRunRequest
from app.services.ml_predictor import get_model_metrics, predict_academic_outcome

router = APIRouter(prefix="/predictions", tags=["Predictions"])


@router.get("/model-card")
def get_model_card():
    """Return live held-out evaluation metrics from `/backend/ml/model_metrics.json`."""
    return get_model_metrics()


@router.get("/history", response_model=list[PredictionOut])
def get_prediction_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.scalars(
        select(Prediction)
        .where(Prediction.student_id == current_user.id)
        .order_by(Prediction.created_at.desc())
        .limit(30)
    ).all()
    return rows


@router.post("", response_model=PredictionOut, status_code=status.HTTP_201_CREATED)
def run_prediction(
    payload: PredictionRunRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    dashboard, _ = compute_dashboard_state(db, current_user)
    profile = db.scalar(select(StudentProfile).where(StudentProfile.user_id == current_user.id))
    weekly_hours = profile.weekly_study_hours if profile else None

    if payload.subject_id:
        subj = db.get(Subject, payload.subject_id)
        if not subj or (subj.user_id is not None and subj.user_id != current_user.id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found.")
        match = next((s for s in dashboard.subjects if s.subject_id == subj.id), None)
        num_ass = match.assessments_count if match else 0
        internal_pct = match.percentage if (match and match.percentage is not None) else 0.0
        att_pct = match.attendance_percentage if match else None
        target_type = "subject_ese"
        target_label = f"{subj.code} ({subj.name})"
        credits = subj.credits
    else:
        num_ass = dashboard.assessments_count
        internal_pct = dashboard.overall_percentage or 0.0
        att_pct = dashboard.attendance_overall_percentage
        target_type = "overall_percentage"
        target_label = "Semester-I Overall"
        credits = 4

    result = predict_academic_outcome(
        num_assessments=num_ass,
        internal_pct=internal_pct,
        attendance_pct=att_pct,
        weekly_study_hours=weekly_hours,
        credits=credits,
        target_label=target_label,
    )

    pred = Prediction(
        student_id=current_user.id,
        subject_id=payload.subject_id,
        target_type=target_type,
        predicted_value=result["predicted_value"],
        lower_bound=result["lower_bound"],
        upper_bound=result["upper_bound"],
        risk_signal=result["risk_signal"],
        model_name=result["model_name"],
        model_version=result["model_version"],
        metrics_json=result["metrics_json"],
        explanation=result["explanation"],
        is_available=result["is_available"],
    )
    db.add(pred)
    db.commit()
    db.refresh(pred)
    return pred
