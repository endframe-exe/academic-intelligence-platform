from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rate_limit import rate_limit
from app.core.security import create_access_token, hash_password, verify_password
from app.models.academic import StudentProfile, User
from app.schemas.academic import (
    AuthResponse,
    DemoLoginRequest,
    LoginRequest,
    RegisterRequest,
    StudentProfileOut,
    UserOut,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit("auth_register", max_requests=20, window_seconds=60))],
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = User(
        name=payload.name.strip(),
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        role="student",
        is_demo=False,
    )
    db.add(user)
    db.flush()

    profile = StudentProfile(
        user_id=user.id,
        education_level=payload.education_level,
        institution=payload.institution,
        programme=payload.programme,
        academic_period=payload.academic_period,
        grading_scheme="NIET 900-Mark Credit System",
    )
    db.add(profile)
    db.commit()
    db.refresh(user)
    db.refresh(profile)

    token = create_access_token(subject=user.id, role=user.role)
    return AuthResponse(
        access_token=token,
        user=UserOut.model_validate(user),
        profile=StudentProfileOut.model_validate(profile),
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    dependencies=[Depends(rate_limit("auth_login", max_requests=20, window_seconds=60))],
)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    profile = db.scalar(select(StudentProfile).where(StudentProfile.user_id == user.id))
    token = create_access_token(subject=user.id, role=user.role)
    return AuthResponse(
        access_token=token,
        user=UserOut.model_validate(user),
        profile=StudentProfileOut.model_validate(profile) if profile else None,
    )


@router.post(
    "/demo-login",
    response_model=AuthResponse,
    dependencies=[Depends(rate_limit("auth_demo", max_requests=20, window_seconds=60))],
)
@router.post(
    "/demo",
    response_model=AuthResponse,
    include_in_schema=False,
    dependencies=[Depends(rate_limit("auth_demo", max_requests=20, window_seconds=60))],
)
def demo_login(payload: DemoLoginRequest | None = None, db: Session = Depends(get_db)):
    """Sign into the preloaded NIET B.Tech CSE (DS) Semester-I demo student."""
    demo_user = db.scalar(select(User).where(User.email == "demo@niet.edu.in"))
    if not demo_user:
        try:
            from seed_niet_sem1 import seed_database

            seed_database(db)
            demo_user = db.scalar(select(User).where(User.email == "demo@niet.edu.in"))
        except Exception:
            demo_user = None

    if not demo_user:
        demo_user = User(
            name=payload.name if payload else "NIET Demo Student",
            email="demo@niet.edu.in",
            password_hash=hash_password("NietDemo@2026"),
            role="student",
            is_demo=True,
        )
        db.add(demo_user)
        db.flush()
        profile = StudentProfile(
            user_id=demo_user.id,
            demo_identifier=payload.demo_identifier if payload else "DEMO-CSDS-01",
            weekly_study_hours=14.0,
        )
        db.add(profile)
        db.commit()
        db.refresh(demo_user)
    else:
        profile = db.scalar(select(StudentProfile).where(StudentProfile.user_id == demo_user.id))

    token = create_access_token(subject=demo_user.id, role=demo_user.role)
    return AuthResponse(
        access_token=token,
        user=UserOut.model_validate(demo_user),
        profile=StudentProfileOut.model_validate(profile) if profile else None,
    )


@router.post("/logout")
def logout():
    return {"status": "ok", "message": "Client token cleared."}
