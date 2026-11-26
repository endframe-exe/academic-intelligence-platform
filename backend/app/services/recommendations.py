"""Hybrid rule-based + ML + optional Gemini study recommendation engine."""

from typing import Any
from app.services.ai_gemini import generate_study_advice_with_gemini


def build_recommendations(subject_summaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Generate transparent, evidence-backed study recommendations."""
    recs: list[dict[str, Any]] = []
    scored = [s for s in subject_summaries if not s["is_excluded_from_total"]]

    for idx, s in enumerate(scored):
        pct = s.get("percentage")
        att = s.get("attendance_percentage")
        credits = s.get("credits", 1)

        if att is not None and att < 75.0:
            recs.append(
                {
                    "id": f"rec-att-{s['code']}-{idx}",
                    "subject_code": s["code"],
                    "subject_name": s["name"],
                    "priority": "high",
                    "title": f"Attendance attention in {s['code']}",
                    "evidence": f"Recorded attendance is {att:.1f}%, below the 75% threshold.",
                    "action": "Attend upcoming lectures/labs without absence and review missed module notes.",
                    "suggested_hours_per_week": float(max(2, credits)),
                    "source": "rule_attendance_threshold",
                }
            )

        if pct is not None and pct < 65.0:
            recs.append(
                {
                    "id": f"rec-marks-{s['code']}-{idx}",
                    "subject_code": s["code"],
                    "subject_name": s["name"],
                    "priority": "high" if credits >= 3 else "medium",
                    "title": f"Strengthen core concepts in {s['name']}",
                    "evidence": f"Current recorded marks average {pct:.1f}% across {s['assessments_count']} assessment(s) ({credits} credits).",
                    "action": "Schedule targeted practice quizzes on weak units and rework solved examples.",
                    "suggested_hours_per_week": round(float(credits) * 1.5, 1),
                    "source": "rule_performance_gap",
                }
            )
        elif pct is None:
            recs.append(
                {
                    "id": f"rec-data-{s['code']}-{idx}",
                    "subject_code": s["code"],
                    "subject_name": s["name"],
                    "priority": "medium",
                    "title": f"Log baseline assessment for {s['code']}",
                    "evidence": f"No internal/practical marks recorded yet for {s['name']} ({credits} credits).",
                    "action": "Add your latest CIE/PS score or attempt a Syllabus Lab diagnostic quiz.",
                    "suggested_hours_per_week": float(max(1.5, credits)),
                    "source": "rule_data_coverage",
                }
            )

    if not recs:
        recs.append(
            {
                "id": "rec-steady-pace",
                "subject_code": None,
                "subject_name": None,
                "priority": "low",
                "title": "Maintain steady spaced revision",
                "evidence": "All tracked subjects are currently above baseline thresholds.",
                "action": "Keep a balanced weekly rotation across high-credit theory subjects and lab practice.",
                "suggested_hours_per_week": 6.0,
                "source": "rule_maintenance",
            }
        )

    priority_order = {"high": 0, "medium": 1, "low": 2}
    recs.sort(key=lambda r: priority_order[r["priority"]])
    return recs


def build_study_plan(
    *,
    subject_summaries: list[dict[str, Any]],
    subject_units: dict[str, list[str]],
    weekly_hours_available: float,
    exam_days_remaining: int,
) -> dict[str, Any]:
    """Allocate weekly study sessions weighted by credit weight and performance gap."""
    scored = [s for s in subject_summaries if not s["is_excluded_from_total"]]
    if not scored:
        return {
            "weekly_hours_available": weekly_hours_available,
            "exam_days_remaining": exam_days_remaining,
            "sessions": [],
            "ai_summary": "Add subjects to generate a personalized study schedule.",
            "ai_used": False,
        }

    weights: list[tuple[dict[str, Any], float]] = []
    for s in scored:
        pct = s.get("percentage")
        gap = (100.0 - pct) if pct is not None else 35.0
        att_penalty = 15.0 if (s.get("attendance_percentage") or 80.0) < 75.0 else 0.0
        weight = max(1.0, float(s.get("credits", 1))) * (1.0 + (gap + att_penalty) / 50.0)
        weights.append((s, weight))

    weights.sort(key=lambda item: item[1], reverse=True)
    total_w = sum(w for _, w in weights)
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    sessions: list[dict[str, Any]] = []
    for idx, (s, w) in enumerate(weights[:7]):
        alloc = round(max(1.0, (w / total_w) * weekly_hours_available), 1)
        units = subject_units.get(s["subject_id"], [])
        focus_topic = units[idx % len(units)] if units else "Core Syllabus Review"
        pct = s.get("percentage")
        rationale = (
            f"{s['credits']} credits; current score {pct:.1f}%."
            if pct is not None
            else f"{s['credits']} credits; no recorded marks yet."
        )
        sessions.append(
            {
                "day": days[idx % len(days)],
                "subject_code": s["code"],
                "subject_name": s["name"],
                "focus_topic": focus_topic,
                "duration_hours": alloc,
                "rationale": rationale,
            }
        )

    anonymized_summary = {
        "weekly_hours_available": weekly_hours_available,
        "exam_days_remaining": exam_days_remaining,
        "subjects_tracked": len(scored),
        "lowest_scoring_code": weights[0][0]["code"],
    }
    ai_summary, ai_used = generate_study_advice_with_gemini(
        anonymized_summary=anonymized_summary, sessions=sessions
    )
    return {
        "weekly_hours_available": weekly_hours_available,
        "exam_days_remaining": exam_days_remaining,
        "sessions": sessions,
        "ai_summary": ai_summary,
        "ai_used": ai_used,
    }
