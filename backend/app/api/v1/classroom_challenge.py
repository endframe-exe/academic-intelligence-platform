from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.v1.syllabus import _to_public_question, build_topic_breakdown, score_quiz_attempt
from app.core.database import get_db
from app.models.academic import Question, QuizAttempt, Subject, UnitTopic
from app.schemas.academic import (
    QuizAttemptCreate,
    QuizAttemptOut,
    QuizQuestionFeedback,
    QuizSubmitRequest,
)

router = APIRouter(prefix="/classroom-challenge", tags=["Classroom Challenge"])


@router.get("/config")
def get_classroom_challenge_config(db: Session = Depends(get_db)):
    """Return preloaded NIET B.Tech CSE (DS) Semester-I configuration for QR demo."""
    subjects = db.scalars(
        select(Subject)
        .options(selectinload(Subject.units_topics))
        .where(
            Subject.user_id.is_(None),
            Subject.programme == "B.Tech CSE (Data Science)",
            Subject.academic_period == "Semester-I",
        )
        .order_by(Subject.is_excluded_from_total, Subject.code)
    ).all()

    q_counts = dict(
        db.execute(
            select(Question.subject_id, func.count(Question.id)).group_by(Question.subject_id)
        ).all()
    )

    configured_subjects = []
    for s in subjects:
        s.units_topics.sort(key=lambda u: u.order_index)
        count = q_counts.get(s.id, 0)
        if count > 0:
            configured_subjects.append(
                {
                    "id": s.id,
                    "code": s.code,
                    "name": s.name,
                    "credits": s.credits,
                    "total_max_marks": s.total_max_marks,
                    "question_count": count,
                    "units": [
                        {"id": u.id, "title": u.title, "order_index": u.order_index}
                        for u in s.units_topics
                    ],
                }
            )

    return {
        "institution": "Noida Institute of Engineering and Technology (NIET)",
        "programme": "B.Tech CSE (Data Science)",
        "academic_period": "Semester-I",
        "recommended_length": 10,
        "privacy_notice": (
            "Enter a display name and optional classroom demo code. Real ERP IDs are never "
            "required and individual identities never appear in projector analytics."
        ),
        "subjects": configured_subjects,
    }


@router.post("/attempts", response_model=QuizAttemptOut, status_code=status.HTTP_201_CREATED)
def create_or_submit_classroom_attempt(payload: QuizAttemptCreate, db: Session = Depends(get_db)):
    subj = db.get(Subject, payload.subject_id)
    if not subj or subj.user_id is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preconfigured classroom subject not found.",
        )

    all_subject_qs = db.scalars(select(Question).where(Question.subject_id == subj.id)).all()
    q_lookup = {q.id: q for q in all_subject_qs}

    if payload.question_ids:
        qs = [q_lookup[qid] for qid in payload.question_ids if qid in q_lookup]
    elif payload.unit_id:
        unit_qs = [q for q in all_subject_qs if q.unit_id == payload.unit_id]
        other_qs = [q for q in all_subject_qs if q.unit_id != payload.unit_id]
        qs = (unit_qs + other_qs)[: payload.num_questions]
    else:
        qs = all_subject_qs[: payload.num_questions]

    if not qs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No reviewed questions available for this subject.",
        )

    attempt = QuizAttempt(
        user_id=None,
        subject_id=subj.id,
        unit_id=payload.unit_id,
        mode="classroom_challenge",
        participant_name=payload.participant_name or "Classroom Participant",
        demo_identifier=payload.demo_identifier or "DEMO-GUEST",
        question_ids_json=[q.id for q in qs],
        total_questions=len(qs),
        max_score=float(len(qs)),
        status="in_progress",
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    if payload.answers is not None:
        return score_quiz_attempt(db, attempt, QuizSubmitRequest(answers=payload.answers))

    return QuizAttemptOut(
        id=attempt.id,
        subject_id=subj.id,
        subject_code=subj.code,
        subject_name=subj.name,
        unit_id=attempt.unit_id,
        mode=attempt.mode,
        status=attempt.status,
        total_questions=attempt.total_questions,
        score=attempt.score,
        max_score=attempt.max_score,
        questions=[_to_public_question(q) for q in qs],
        started_at=attempt.started_at,
        submitted_at=attempt.submitted_at,
    )


@router.get("/attempts/{attempt_id}", response_model=QuizAttemptOut)
def get_classroom_attempt(attempt_id: str, db: Session = Depends(get_db)):
    attempt = db.get(QuizAttempt, attempt_id)
    if not attempt or attempt.mode != "classroom_challenge":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classroom Challenge attempt not found.",
        )
    subj = db.get(Subject, attempt.subject_id)
    qs = db.scalars(select(Question).where(Question.id.in_(attempt.question_ids_json))).all()
    q_map = {q.id: q for q in qs}
    unit_ids = {q.unit_id for q in qs if q.unit_id}
    unit_map = (
        {
            u.id: u.title
            for u in db.scalars(select(UnitTopic).where(UnitTopic.id.in_(unit_ids))).all()
        }
        if unit_ids
        else {}
    )
    ordered_qs = [_to_public_question(q_map[qid]) for qid in attempt.question_ids_json if qid in q_map]

    feedback: list[QuizQuestionFeedback] = []
    breakdown: dict[str, dict[str, int]] = {}
    topic_counts: dict[str, dict[str, int]] = {}
    if attempt.status == "submitted" and attempt.responses_json:
        resp_map = {r["question_id"]: r for r in attempt.responses_json}
        for qid in attempt.question_ids_json:
            q = q_map.get(qid)
            r = resp_map.get(qid)
            if not q or not r:
                continue
            topic_title = r.get("topic_title") or (
                unit_map.get(q.unit_id, "Core Concepts") if q.unit_id else "Core Concepts"
            )
            diff_bucket = breakdown.setdefault(q.difficulty, {"correct": 0, "total": 0})
            diff_bucket["total"] += 1
            if r["is_correct"]:
                diff_bucket["correct"] += 1

            t_bucket = topic_counts.setdefault(topic_title, {"correct": 0, "total": 0})
            t_bucket["total"] += 1
            if r["is_correct"]:
                t_bucket["correct"] += 1

            feedback.append(
                QuizQuestionFeedback(
                    question_id=q.id,
                    question_text=q.question_text,
                    difficulty=q.difficulty,
                    topic_title=topic_title,
                    user_answer=r["user_answer"],
                    correct_answer=q.answer_key,
                    is_correct=r["is_correct"],
                    explanation=q.explanation,
                )
            )

    return QuizAttemptOut(
        id=attempt.id,
        subject_id=attempt.subject_id,
        subject_code=subj.code if subj else None,
        subject_name=subj.name if subj else None,
        unit_id=attempt.unit_id,
        mode=attempt.mode,
        status=attempt.status,
        total_questions=attempt.total_questions,
        score=attempt.score,
        max_score=attempt.max_score,
        questions=ordered_qs if attempt.status == "in_progress" else [],
        feedback=feedback,
        difficulty_breakdown=breakdown,
        topic_breakdown=build_topic_breakdown(topic_counts) if topic_counts else [],
        started_at=attempt.started_at,
        submitted_at=attempt.submitted_at,
    )


@router.post("/attempts/{attempt_id}/submit", response_model=QuizAttemptOut)
def submit_classroom_attempt(
    attempt_id: str,
    payload: QuizSubmitRequest,
    db: Session = Depends(get_db),
):
    attempt = db.get(QuizAttempt, attempt_id)
    if not attempt or attempt.mode != "classroom_challenge":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classroom Challenge attempt not found.",
        )
    return score_quiz_attempt(db, attempt, payload)


@router.get("/stats")
def get_anonymized_classroom_stats(db: Session = Depends(get_db)):
    """Anonymized aggregate classroom metrics only (no names or ERP/demo identifiers)."""
    attempts = db.scalars(
        select(QuizAttempt).where(
            QuizAttempt.mode == "classroom_challenge",
            QuizAttempt.status == "submitted",
        )
    ).all()
    if not attempts:
        return {
            "total_participants": 0,
            "total_submitted_attempts": 0,
            "average_percentage": None,
            "hardest_topic": None,
            "subject_participation": [],
        }

    pcts = [
        (a.score / a.max_score) * 100.0
        for a in attempts
        if a.score is not None and a.max_score > 0
    ]
    avg = round(sum(pcts) / len(pcts), 2) if pcts else None

    topic_stats: dict[str, dict[str, int]] = {}
    subj_stats: dict[str, list[float]] = {}
    for a in attempts:
        if a.score is not None and a.max_score > 0:
            subj_stats.setdefault(a.subject_id, []).append((a.score / a.max_score) * 100.0)
        for resp in a.responses_json or []:
            topic = resp.get("topic_title") or "Core Concepts"
            bucket = topic_stats.setdefault(topic, {"correct": 0, "total": 0})
            bucket["total"] += 1
            if resp.get("is_correct"):
                bucket["correct"] += 1

    hardest_topic = None
    if topic_stats:
        ranked_topics = sorted(
            topic_stats.items(),
            key=lambda kv: (kv[1]["correct"] / kv[1]["total"]) if kv[1]["total"] > 0 else 1.0,
        )
        t_name, t_counts = ranked_topics[0]
        hardest_topic = {
            "topic": t_name,
            "accuracy_percentage": round((t_counts["correct"] / t_counts["total"]) * 100.0, 1),
            "responses": t_counts["total"],
        }

    subj_map = {
        s.id: s
        for s in db.scalars(select(Subject).where(Subject.id.in_(subj_stats.keys()))).all()
    }
    subject_participation = [
        {
            "code": subj_map[sid].code if sid in subj_map else "SUBJ",
            "name": subj_map[sid].name if sid in subj_map else "Subject",
            "attempts": len(scores),
            "average_percentage": round(sum(scores) / len(scores), 1),
        }
        for sid, scores in subj_stats.items()
    ]
    subject_participation.sort(key=lambda x: x["attempts"], reverse=True)

    return {
        "total_participants": len(attempts),
        "total_submitted_attempts": len(attempts),
        "average_percentage": avg,
        "hardest_topic": hardest_topic,
        "subject_participation": subject_participation,
    }
