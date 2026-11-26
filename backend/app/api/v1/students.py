from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.academic import StudentProfile, User
from app.schemas.academic import StudentMeOut, StudentProfileOut, StudentProfileUpdate, UserOut

router = APIRouter(prefix="/students", tags=["Students"])


def _ensure_profile(db: Session, user: User) -> StudentProfile:
    profile = db.scalar(select(StudentProfile).where(StudentProfile.user_id == user.id))
    if not profile:
        profile = StudentProfile(user_id=user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.get("/me", response_model=StudentMeOut)
def get_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = _ensure_profile(db, current_user)
    return StudentMeOut(
        user=UserOut.model_validate(current_user),
        profile=StudentProfileOut.model_validate(profile),
    )


@router.patch("/me", response_model=StudentMeOut)
def update_me(
    payload: StudentProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = _ensure_profile(db, current_user)
    if payload.name is not None:
        current_user.name = payload.name.strip()

    for field in (
        "education_level",
        "institution",
        "programme",
        "academic_period",
        "grading_scheme",
        "demo_identifier",
        "weekly_study_hours",
    ):
        val = getattr(payload, field)
        if val is not None:
            setattr(profile, field, val)

    db.commit()
    db.refresh(current_user)
    db.refresh(profile)
    return StudentMeOut(
        user=UserOut.model_validate(current_user),
        profile=StudentProfileOut.model_validate(profile),
    )
