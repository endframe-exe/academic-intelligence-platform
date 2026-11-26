from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user, get_optional_user
from app.core.database import get_db
from app.models.academic import Subject, UnitTopic, User
from app.schemas.academic import SubjectCreate, SubjectOut, UnitTopicOut

router = APIRouter(prefix="/subjects", tags=["Subjects"])


@router.get("", response_model=list[SubjectOut])
def list_subjects(
    programme: str | None = None,
    academic_period: str | None = None,
    current_user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """Return global catalogue subjects plus any user-owned custom subjects."""
    stmt = select(Subject).options(selectinload(Subject.units_topics))
    if current_user:
        stmt = stmt.where(or_(Subject.user_id.is_(None), Subject.user_id == current_user.id))
    else:
        stmt = stmt.where(Subject.user_id.is_(None))
    if programme:
        stmt = stmt.where(Subject.programme == programme)
    if academic_period:
        stmt = stmt.where(Subject.academic_period == academic_period)

    subjects = db.scalars(stmt.order_by(Subject.is_excluded_from_total, Subject.code)).all()
    for s in subjects:
        s.units_topics.sort(key=lambda u: u.order_index)
    return subjects


@router.post("", response_model=SubjectOut, status_code=status.HTTP_201_CREATED)
def create_subject(
    payload: SubjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    total = (
        0
        if payload.is_excluded_from_total
        else payload.internal_max_marks + payload.external_max_marks
    )
    subject = Subject(
        user_id=current_user.id,
        programme=payload.programme,
        academic_period=payload.academic_period,
        code=payload.code.strip().upper(),
        name=payload.name.strip(),
        credits=payload.credits,
        category=payload.category,
        internal_label=payload.internal_label,
        internal_max_marks=payload.internal_max_marks,
        external_label=payload.external_label,
        external_max_marks=payload.external_max_marks,
        total_max_marks=total,
        is_excluded_from_total=payload.is_excluded_from_total,
    )
    db.add(subject)
    db.flush()

    for idx, title in enumerate(payload.units, start=1):
        clean = title.strip()
        if clean:
            db.add(
                UnitTopic(
                    subject_id=subject.id,
                    order_index=idx,
                    node_type="unit",
                    title=clean,
                )
            )

    db.commit()
    db.refresh(subject)
    subject = db.scalar(
        select(Subject)
        .options(selectinload(Subject.units_topics))
        .where(Subject.id == subject.id)
    )
    return subject


@router.get("/{subject_id}/topics", response_model=list[UnitTopicOut])
def get_subject_topics(
    subject_id: str,
    current_user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    subject = db.get(Subject, subject_id)
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found.")
    if subject.user_id is not None and (current_user is None or subject.user_id != current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    units = db.scalars(
        select(UnitTopic)
        .where(UnitTopic.subject_id == subject_id)
        .order_by(UnitTopic.order_index)
    ).all()
    return units
