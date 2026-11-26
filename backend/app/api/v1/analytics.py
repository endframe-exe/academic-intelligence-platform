from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.rate_limit import rate_limit
from app.models.academic import (
    Assessment,
    AssessmentResult,
    AttendanceRecord,
    Subject,
    User,
)
from app.schemas.academic import (
    DashboardOut,
    RecommendationItem,
    StudyPlanOut,
    StudyPlanRequest,
    SubjectSummaryOut,
)
from app.services.recommendations import build_recommendations, build_study_plan

router = APIRouter(tags=["Analytics & Study Planner"])


def compute_dashboard_state(db: Session, user: User) -> tuple[DashboardOut, dict[str, list[str]]]:
    subjects = db.scalars(
        select(Subject)
        .options(selectinload(Subject.units_topics))
        .where(or_(Subject.user_id.is_(None), Subject.user_id == user.id))
        .order_by(Subject.is_excluded_from_total, Subject.code)
    ).all()

    results = db.execute(
        select(AssessmentResult, Assessment)
        .join(Assessment, AssessmentResult.assessment_id == Assessment.id)
        .where(AssessmentResult.student_id == user.id)
        .order_by(Assessment.assessment_date, AssessmentResult.recorded_at)
    ).all()

    attendance_rows = db.scalars(
        select(AttendanceRecord).where(AttendanceRecord.student_id == user.id)
    ).all()

    marks_by_subj: dict[str, list[tuple[float, float]]] = defaultdict(list)
    trend: list[dict] = []
    subj_lookup = {s.id: s for s in subjects}

    for res, ass in results:
        marks_by_subj[ass.subject_id].append((res.marks_obtained, ass.max_marks))
        subj = subj_lookup.get(ass.subject_id)
        pct = round((res.marks_obtained / ass.max_marks) * 100.0, 2) if ass.max_marks > 0 else 0.0
        trend.append(
            {
                "label": ass.title,
                "subject_code": subj.code if subj else "SUBJ",
                "date": str(ass.assessment_date or res.recorded_at.date()),
                "percentage": pct,
                "marks_obtained": res.marks_obtained,
                "max_marks": ass.max_marks,
            }
        )

    att_by_subj: dict[str, tuple[int, int]] = {}
    for row in attendance_rows:
        prev_att, prev_tot = att_by_subj.get(row.subject_id, (0, 0))
        att_by_subj[row.subject_id] = (prev_att + row.classes_attended, prev_tot + row.total_classes)

    subject_summaries: list[SubjectSummaryOut] = []
    subject_units: dict[str, list[str]] = {}
    total_credits = 0
    total_credit_marks_scale = 0
    recorded_marks_total = 0.0
    recorded_max_total = 0.0
    tot_att_attended = 0
    tot_att_classes = 0

    for subj in subjects:
        subj.units_topics.sort(key=lambda u: u.order_index)
        subject_units[subj.id] = [u.title for u in subj.units_topics]

        pairs = marks_by_subj.get(subj.id, [])
        obt = round(sum(p[0] for p in pairs), 2)
        mx = round(sum(p[1] for p in pairs), 2)
        pct = round((obt / mx) * 100.0, 2) if mx > 0 else None

        att_pair = att_by_subj.get(subj.id)
        att_pct = (
            round((att_pair[0] / att_pair[1]) * 100.0, 2)
            if att_pair and att_pair[1] > 0
            else None
        )

        if not subj.is_excluded_from_total:
            total_credits += subj.credits
            total_credit_marks_scale += subj.total_max_marks
            recorded_marks_total += obt
            recorded_max_total += mx
            if att_pair:
                tot_att_attended += att_pair[0]
                tot_att_classes += att_pair[1]

        subject_summaries.append(
            SubjectSummaryOut(
                subject_id=subj.id,
                code=subj.code,
                name=subj.name,
                credits=subj.credits,
                category=subj.category,
                is_excluded_from_total=subj.is_excluded_from_total,
                total_max_marks=subj.total_max_marks,
                obtained_marks=obt,
                recorded_max_marks=mx,
                percentage=pct,
                attendance_percentage=att_pct,
                assessments_count=len(pairs),
            )
        )

    overall_pct = (
        round((recorded_marks_total / recorded_max_total) * 100.0, 2)
        if recorded_max_total > 0
        else None
    )
    att_overall_pct = (
        round((tot_att_attended / tot_att_classes) * 100.0, 2) if tot_att_classes > 0 else None
    )

    scored_with_pct = [
        s for s in subject_summaries if not s.is_excluded_from_total and s.percentage is not None
    ]
    strengths = [
        f"{s.code} ({s.name}): {s.percentage:.1f}%"
        for s in sorted(scored_with_pct, key=lambda x: x.percentage or 0, reverse=True)[:3]
        if (s.percentage or 0) >= 70.0
    ]
    improvement_areas = [
        f"{s.code} ({s.name}): {s.percentage:.1f}%"
        for s in sorted(scored_with_pct, key=lambda x: x.percentage or 0)[:3]
        if (s.percentage or 0) < 75.0
    ]

    non_audit_with_data = sum(
        1 for s in subject_summaries if not s.is_excluded_from_total and s.assessments_count > 0
    )
    non_audit_total = sum(1 for s in subject_summaries if not s.is_excluded_from_total)
    coverage_note = (
        f"Covering {non_audit_with_data} of {non_audit_total} credit-bearing subjects "
        f"({round(recorded_marks_total, 1)} / {round(recorded_max_total, 1)} recorded marks; "
        f"Compulsory Audit excluded from 900-mark total)."
    )

    dashboard = DashboardOut(
        overall_percentage=overall_pct,
        total_credits=total_credits,
        total_credit_marks_scale=total_credit_marks_scale,
        recorded_marks_total=round(recorded_marks_total, 2),
        recorded_max_total=round(recorded_max_total, 2),
        attendance_overall_percentage=att_overall_pct,
        assessments_count=len(results),
        subjects=subject_summaries,
        trend=trend,
        strengths=strengths,
        improvement_areas=improvement_areas,
        data_coverage_note=coverage_note,
    )
    return dashboard, subject_units


@router.get("/analytics/dashboard", response_model=DashboardOut)
def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    dashboard, _ = compute_dashboard_state(db, current_user)
    return dashboard


@router.get("/recommendations", response_model=list[RecommendationItem])
def get_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    dashboard, _ = compute_dashboard_state(db, current_user)
    raw = build_recommendations([s.model_dump() for s in dashboard.subjects])
    return [RecommendationItem(**item) for item in raw]


@router.post(
    "/study-plans",
    response_model=StudyPlanOut,
    dependencies=[Depends(rate_limit("gemini_study_plan", max_requests=15, window_seconds=60))],
)
def create_study_plan(
    payload: StudyPlanRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    dashboard, subject_units = compute_dashboard_state(db, current_user)
    plan = build_study_plan(
        subject_summaries=[s.model_dump() for s in dashboard.subjects],
        subject_units=subject_units,
        weekly_hours_available=payload.weekly_hours_available,
        exam_days_remaining=payload.exam_days_remaining,
    )
    return StudyPlanOut(**plan)
