from datetime import datetime, timezone
from pathlib import Path
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.database import get_db
from app.core.rate_limit import rate_limit
from app.models.academic import (
    Question,
    QuizAttempt,
    Subject,
    SyllabusDocument,
    UnitTopic,
    User,
)
from app.schemas.academic import (
    QuestionGenerateRequest,
    QuestionPublicOut,
    QuizAttemptCreate,
    QuizAttemptOut,
    QuizQuestionFeedback,
    QuizSubmitRequest,
    SyllabusDocumentOut,
    SyllabusStructureReview,
    TopicBreakdownItem,
)
from app.services.ai_gemini import (
    extract_syllabus_structure_with_gemini,
    generate_questions_with_gemini,
)
from app.services.document_parser import (
    chunk_syllabus_text,
    extract_text_from_file,
    retrieve_relevant_chunks,
    validate_uploaded_file,
)

router = APIRouter(tags=["Syllabus Lab & Assessments"])

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "md"}


def _to_public_question(q: Question) -> QuestionPublicOut:
    return QuestionPublicOut(
        id=q.id,
        subject_id=q.subject_id,
        unit_id=q.unit_id,
        question_type=q.question_type,
        difficulty=q.difficulty,
        question_text=q.question_text,
        options=q.options_json,
        source=q.source,
    )


@router.post(
    "/documents",
    response_model=SyllabusDocumentOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit("gemini_upload", max_requests=15, window_seconds=60))],
)
async def upload_syllabus_document(
    file: UploadFile = File(...),
    subject_id: str | None = Form(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    settings = get_settings()
    filename = file.filename or "syllabus.pdf"
    ext = Path(filename).suffix.lower().lstrip(".")
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '.{ext}'. Allowed: PDF, DOCX, TXT, MD.",
        )

    raw = await file.read()
    try:
        validate_uploaded_file(raw, ext, max_mb=settings.MAX_UPLOAD_MB)
    except ValueError as exc:
        msg = str(exc)
        code = (
            413
            if "limit" in msg.lower()
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=code, detail=msg)

    subject_name = "Uploaded Academic Syllabus"
    if subject_id:
        subj = db.get(Subject, subject_id)
        if not subj or (subj.user_id is not None and subj.user_id != current_user.id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found.")
        subject_name = f"{subj.code} {subj.name}"

    upload_root = Path(settings.UPLOAD_DIR) / current_user.id
    upload_root.mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid.uuid4()}.{ext}"
    dest = upload_root / safe_name
    dest.write_bytes(raw)

    try:
        extracted_text = extract_text_from_file(dest, ext)
        structure, _ = extract_syllabus_structure_with_gemini(extracted_text, subject_name)
        chunks = chunk_syllabus_text(extracted_text)
        structure["chunks"] = chunks
        structure.setdefault("subject_name", subject_name)
        proc_status = "extracted"
    except Exception:
        extracted_text = ""
        structure = {"subject_name": subject_name, "units": [], "chunks": []}
        proc_status = "failed"

    doc = SyllabusDocument(
        owner_id=current_user.id,
        subject_id=subject_id,
        filename=filename,
        file_type=ext,
        storage_path=str(dest),
        processing_status=proc_status,
        extracted_text=extracted_text,
        extracted_structure_json=structure,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@router.get("/documents", response_model=list[SyllabusDocumentOut])
def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    docs = db.scalars(
        select(SyllabusDocument)
        .where(SyllabusDocument.owner_id == current_user.id)
        .order_by(SyllabusDocument.created_at.desc())
    ).all()
    return docs


@router.get("/documents/{doc_id}", response_model=SyllabusDocumentOut)
def get_document(
    doc_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = db.get(SyllabusDocument, doc_id)
    if not doc or doc.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    return doc


@router.patch("/documents/{doc_id}/review", response_model=SyllabusDocumentOut)
def review_document_structure(
    doc_id: str,
    payload: SyllabusStructureReview,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = db.get(SyllabusDocument, doc_id)
    if not doc or doc.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    existing_struct = doc.extracted_structure_json or {}
    chunks = payload.chunks
    if chunks is None:
        # Rebuild chunks incorporating any user edits to units/topics alongside extracted text
        unit_summary_text = "\n".join(
            f"Unit: {u.get('title', '')}. Topics: {', '.join(u.get('topics', []))}"
            for u in payload.units
        )
        combined = f"{unit_summary_text}\n{doc.extracted_text or ''}".strip()
        chunks = chunk_syllabus_text(combined) or existing_struct.get("chunks", [])

    doc.extracted_structure_json = {
        "subject_name": payload.subject_name or existing_struct.get("subject_name", doc.filename),
        "units": payload.units,
        "chunks": chunks,
    }
    doc.processing_status = "reviewed"
    db.commit()
    db.refresh(doc)
    return doc


@router.post(
    "/question-sets/generate",
    dependencies=[Depends(rate_limit("gemini_generate", max_requests=15, window_seconds=60))],
)
def generate_question_set(
    payload: QuestionGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    subj = db.get(Subject, payload.subject_id)
    if not subj or (subj.user_id is not None and subj.user_id != current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found.")

    unit = db.get(UnitTopic, payload.unit_id) if payload.unit_id else None
    doc = (
        db.get(SyllabusDocument, payload.syllabus_document_id)
        if payload.syllabus_document_id
        else None
    )
    if doc and doc.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to document.")

    # Build candidate chunks and rank via scikit-learn TfidfVectorizer
    if doc:
        saved_chunks = (doc.extracted_structure_json or {}).get("chunks") or []
        chunks = saved_chunks or chunk_syllabus_text(doc.extracted_text or "")
        if not chunks:
            units_json = (doc.extracted_structure_json or {}).get("units") or []
            chunks = [
                f"{u.get('title', '')}: {', '.join(u.get('topics', []))}" for u in units_json
            ]
    else:
        units = db.scalars(
            select(UnitTopic).where(UnitTopic.subject_id == subj.id).order_by(UnitTopic.order_index)
        ).all()
        chunks = [f"{subj.code} {subj.name} — {u.title}: {u.description or ''}" for u in units]

    query = f"{subj.code} {subj.name} {unit.title if unit else ''} {unit.description if unit else ''}"
    retrieved_chunks = retrieve_relevant_chunks(chunks, query, top_k=5)
    context_text = "\n---\n".join(retrieved_chunks) if retrieved_chunks else f"{subj.code} {subj.name}"

    # Never pass user PII (name, email, owner_id) to Gemini
    generated, ai_used, notice = generate_questions_with_gemini(
        subject_code=subj.code,
        subject_name=subj.name,
        unit_title=unit.title if unit else None,
        context_text=context_text,
        num_questions=payload.num_questions,
        difficulty=payload.difficulty,
    )

    saved: list[QuestionPublicOut] = []
    if generated:
        for item in generated:
            q = Question(
                subject_id=subj.id,
                unit_id=unit.id if unit else None,
                syllabus_document_id=doc.id if doc else None,
                question_type="mcq",
                difficulty=item["difficulty"],
                question_text=item["question_text"],
                options_json=item["options"],
                answer_key=item["answer_key"],
                explanation=item["explanation"],
                source="gemini_rag",
                is_reviewed=False,
            )
            db.add(q)
            db.flush()
            saved.append(_to_public_question(q))
        db.commit()
    else:
        stmt = select(Question).where(
            Question.subject_id == subj.id,
            Question.source == "reviewed_bank",
        )
        if unit:
            unit_qs = db.scalars(stmt.where(Question.unit_id == unit.id).limit(payload.num_questions)).all()
            if len(unit_qs) < payload.num_questions:
                extra = db.scalars(
                    select(Question)
                    .where(Question.subject_id == subj.id, Question.source == "reviewed_bank")
                    .limit(payload.num_questions)
                ).all()
                seen = {q.id for q in unit_qs}
                fallback_qs = unit_qs + [q for q in extra if q.id not in seen]
                fallback_qs = fallback_qs[: payload.num_questions]
            else:
                fallback_qs = unit_qs
        else:
            fallback_qs = db.scalars(stmt.limit(payload.num_questions)).all()
        saved = [_to_public_question(q) for q in fallback_qs]

    return {
        "subject_code": subj.code,
        "subject_name": subj.name,
        "retrieved_chunks_count": len(retrieved_chunks),
        "ai_used": ai_used,
        "source": "gemini_rag" if ai_used else "reviewed_bank",
        "notice": notice,
        "questions": saved,
    }


def build_topic_breakdown(topic_counts: dict[str, dict[str, int]]) -> list[TopicBreakdownItem]:
    items: list[TopicBreakdownItem] = []
    for topic, counts in topic_counts.items():
        tot = counts["total"]
        cor = counts["correct"]
        pct = round((cor / tot) * 100.0, 1) if tot > 0 else 0.0
        items.append(
            TopicBreakdownItem(
                topic=topic,
                correct=cor,
                total=tot,
                percentage=pct,
                status="Strength" if pct >= 70.0 else "Needs Review",
            )
        )
    items.sort(key=lambda t: t.percentage)
    return items


def score_quiz_attempt(db: Session, attempt: QuizAttempt, payload: QuizSubmitRequest) -> QuizAttemptOut:
    q_map = {
        q.id: q
        for q in db.scalars(
            select(Question).where(Question.id.in_(attempt.question_ids_json))
        ).all()
    }
    unit_ids = {q.unit_id for q in q_map.values() if q.unit_id}
    unit_map = (
        {
            u.id: u.title
            for u in db.scalars(select(UnitTopic).where(UnitTopic.id.in_(unit_ids))).all()
        }
        if unit_ids
        else {}
    )
    answer_lookup = {a.question_id: a.answer for a in payload.answers}

    total_score = 0.0
    feedback: list[QuizQuestionFeedback] = []
    responses_to_store: list[dict] = []
    breakdown: dict[str, dict[str, int]] = {}
    topic_counts: dict[str, dict[str, int]] = {}

    for qid in attempt.question_ids_json:
        q = q_map.get(qid)
        if not q:
            continue
        topic_title = unit_map.get(q.unit_id, "Core Concepts") if q.unit_id else "Core Concepts"
        user_ans = answer_lookup.get(qid, "")
        is_correct = user_ans.strip() == q.answer_key.strip()
        awarded = 1.0 if is_correct else 0.0
        total_score += awarded

        diff_bucket = breakdown.setdefault(q.difficulty, {"correct": 0, "total": 0})
        diff_bucket["total"] += 1
        if is_correct:
            diff_bucket["correct"] += 1

        topic_bucket = topic_counts.setdefault(topic_title, {"correct": 0, "total": 0})
        topic_bucket["total"] += 1
        if is_correct:
            topic_bucket["correct"] += 1

        feedback.append(
            QuizQuestionFeedback(
                question_id=q.id,
                question_text=q.question_text,
                difficulty=q.difficulty,
                topic_title=topic_title,
                user_answer=user_ans,
                correct_answer=q.answer_key,
                is_correct=is_correct,
                explanation=q.explanation,
            )
        )
        responses_to_store.append(
            {
                "question_id": q.id,
                "user_answer": user_ans,
                "is_correct": is_correct,
                "awarded_score": awarded,
                "difficulty": q.difficulty,
                "topic_title": topic_title,
            }
        )

    attempt.responses_json = responses_to_store
    attempt.score = total_score
    attempt.status = "submitted"
    attempt.submitted_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()
    db.refresh(attempt)

    subj = db.get(Subject, attempt.subject_id)
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
        questions=[],
        feedback=feedback,
        difficulty_breakdown=breakdown,
        topic_breakdown=build_topic_breakdown(topic_counts),
        started_at=attempt.started_at,
        submitted_at=attempt.submitted_at,
    )


@router.post("/quiz-attempts", response_model=QuizAttemptOut, status_code=status.HTTP_201_CREATED)
def create_quiz_attempt(
    payload: QuizAttemptCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    subj = db.get(Subject, payload.subject_id)
    if not subj or (subj.user_id is not None and subj.user_id != current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found.")

    if payload.question_ids:
        qs = db.scalars(
            select(Question).where(
                Question.subject_id == subj.id,
                Question.id.in_(payload.question_ids),
            )
        ).all()
    else:
        stmt = select(Question).where(Question.subject_id == subj.id)
        if payload.unit_id:
            unit_qs = db.scalars(
                stmt.where(Question.unit_id == payload.unit_id).limit(payload.num_questions)
            ).all()
            qs = unit_qs if unit_qs else db.scalars(stmt.limit(payload.num_questions)).all()
        else:
            qs = db.scalars(stmt.limit(payload.num_questions)).all()

    if not qs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No questions available for this subject yet. Generate questions first.",
        )

    attempt = QuizAttempt(
        user_id=current_user.id,
        subject_id=subj.id,
        unit_id=payload.unit_id,
        mode=payload.mode,
        participant_name=current_user.name,
        question_ids_json=[q.id for q in qs],
        total_questions=len(qs),
        max_score=float(len(qs)),
        status="in_progress",
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

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


@router.get("/quiz-attempts/{attempt_id}", response_model=QuizAttemptOut)
def get_quiz_attempt(
    attempt_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    attempt = db.get(QuizAttempt, attempt_id)
    if not attempt or attempt.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz attempt not found.")
    subj = db.get(Subject, attempt.subject_id)
    qs = db.scalars(select(Question).where(Question.id.in_(attempt.question_ids_json))).all()
    q_map = {q.id: q for q in qs}
    ordered_qs = [_to_public_question(q_map[qid]) for qid in attempt.question_ids_json if qid in q_map]
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
        questions=ordered_qs,
        started_at=attempt.started_at,
        submitted_at=attempt.submitted_at,
    )


@router.post("/quiz-attempts/{attempt_id}/submit", response_model=QuizAttemptOut)
def submit_quiz_attempt(
    attempt_id: str,
    payload: QuizSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    attempt = db.get(QuizAttempt, attempt_id)
    if not attempt or attempt.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz attempt not found.")
    return score_quiz_attempt(db, attempt, payload)
