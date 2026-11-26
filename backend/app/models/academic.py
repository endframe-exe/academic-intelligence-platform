import uuid
from datetime import date, datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    CHAR,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    """Account identity for students, classroom demo participants, and admins."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), default="student", nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)

    profile: Mapped["StudentProfile | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    assessment_results: Mapped[list["AssessmentResult"]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )
    attendance_records: Mapped[list["AttendanceRecord"]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )
    predictions: Mapped[list["Prediction"]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )
    syllabus_documents: Mapped[list["SyllabusDocument"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )


class StudentProfile(Base):
    """Academic configuration and onboarding preferences for a student."""

    __tablename__ = "student_profiles"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    education_level: Mapped[str] = mapped_column(String(64), default="undergraduate", nullable=False)
    institution: Mapped[str] = mapped_column(
        String(200), default="Noida Institute of Engineering and Technology (NIET)", nullable=False
    )
    programme: Mapped[str] = mapped_column(
        String(160), default="B.Tech CSE (Data Science)", nullable=False
    )
    academic_period: Mapped[str] = mapped_column(String(64), default="Semester-I", nullable=False)
    grading_scheme: Mapped[str] = mapped_column(
        String(64), default="NIET 900-Mark Credit System", nullable=False
    )
    demo_identifier: Mapped[str | None] = mapped_column(String(64), nullable=True)
    weekly_study_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow, nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="profile")


class Subject(Base):
    """Configurable subject catalogue entry with CIE/ESE or PS/PE max marks."""

    __tablename__ = "subjects"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=_uuid)
    user_id: Mapped[str | None] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    programme: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    academic_period: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    credits: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    category: Mapped[str] = mapped_column(String(32), default="theory", nullable=False)
    internal_label: Mapped[str] = mapped_column(String(16), default="CIE", nullable=False)
    internal_max_marks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    external_label: Mapped[str] = mapped_column(String(16), default="ESE", nullable=False)
    external_max_marks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_max_marks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_excluded_from_total: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)

    units_topics: Mapped[list["UnitTopic"]] = relationship(
        back_populates="subject", cascade="all, delete-orphan"
    )
    assessments: Mapped[list["Assessment"]] = relationship(
        back_populates="subject", cascade="all, delete-orphan"
    )


class UnitTopic(Base):
    """Syllabus unit/module and nested topic hierarchy per subject."""

    __tablename__ = "units_topics"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=_uuid)
    subject_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    parent_id: Mapped[str | None] = mapped_column(
        CHAR(36), ForeignKey("units_topics.id", ondelete="CASCADE"), nullable=True
    )
    order_index: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    node_type: Mapped[str] = mapped_column(String(24), default="unit", nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    subject: Mapped["Subject"] = relationship(back_populates="units_topics")


class Assessment(Base):
    """Tests, CIE/ESE/PS/PE exams, assignments, and unit evaluations."""

    __tablename__ = "assessments"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=_uuid)
    subject_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    unit_id: Mapped[str | None] = mapped_column(
        CHAR(36), ForeignKey("units_topics.id", ondelete="SET NULL"), nullable=True
    )
    user_id: Mapped[str | None] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    assessment_type: Mapped[str] = mapped_column(String(32), default="CIE", nullable=False)
    max_marks: Mapped[float] = mapped_column(Float, nullable=False)
    assessment_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    academic_period: Mapped[str] = mapped_column(String(64), default="Semester-I", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)

    subject: Mapped["Subject"] = relationship(back_populates="assessments")
    results: Mapped[list["AssessmentResult"]] = relationship(
        back_populates="assessment", cascade="all, delete-orphan"
    )


class AssessmentResult(Base):
    """Recorded marks obtained by a student on an assessment."""

    __tablename__ = "assessment_results"
    __table_args__ = (
        UniqueConstraint("student_id", "assessment_id", name="uq_student_assessment_result"),
    )

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=_uuid)
    student_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assessment_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    marks_obtained: Mapped[float] = mapped_column(Float, nullable=False)
    grading_scheme_snapshot: Mapped[str] = mapped_column(
        String(64), default="NIET 900-Mark Credit System", nullable=False
    )
    study_hours_logged: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)

    student: Mapped["User"] = relationship(back_populates="assessment_results")
    assessment: Mapped["Assessment"] = relationship(back_populates="results")


class AttendanceRecord(Base):
    """Subject-wise attendance tracking for a student."""

    __tablename__ = "attendance_records"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=_uuid)
    student_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subject_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    academic_period: Mapped[str] = mapped_column(String(64), default="Semester-I", nullable=False)
    classes_attended: Mapped[int] = mapped_column(Integer, nullable=False)
    total_classes: Mapped[int] = mapped_column(Integer, nullable=False)
    recorded_date: Mapped[date] = mapped_column(Date, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow, nullable=False
    )

    student: Mapped["User"] = relationship(back_populates="attendance_records")


class Prediction(Base):
    """Versioned ML prediction outputs with uncertainty interval and metrics."""

    __tablename__ = "predictions"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=_uuid)
    student_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subject_id: Mapped[str | None] = mapped_column(
        CHAR(36), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=True, index=True
    )
    target_type: Mapped[str] = mapped_column(String(64), nullable=False)
    predicted_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    lower_bound: Mapped[float | None] = mapped_column(Float, nullable=True)
    upper_bound: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_signal: Mapped[str | None] = mapped_column(String(32), nullable=True)
    model_name: Mapped[str] = mapped_column(String(64), nullable=False)
    model_version: Mapped[str] = mapped_column(String(32), nullable=False)
    metrics_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)

    student: Mapped["User"] = relationship(back_populates="predictions")


class SyllabusDocument(Base):
    """Uploaded syllabus/study documents and extracted topic structure."""

    __tablename__ = "syllabus_documents"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=_uuid)
    owner_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subject_id: Mapped[str | None] = mapped_column(
        CHAR(36), ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(32), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    processing_status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    extracted_text: Mapped[str | None] = mapped_column(
        Text().with_variant(LONGTEXT, "mysql"), nullable=True
    )
    extracted_structure_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)

    owner: Mapped["User"] = relationship(back_populates="syllabus_documents")


class Question(Base):
    """Syllabus-grounded practice and Classroom Challenge assessment questions."""

    __tablename__ = "questions"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=_uuid)
    subject_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    unit_id: Mapped[str | None] = mapped_column(
        CHAR(36), ForeignKey("units_topics.id", ondelete="SET NULL"), nullable=True, index=True
    )
    syllabus_document_id: Mapped[str | None] = mapped_column(
        CHAR(36), ForeignKey("syllabus_documents.id", ondelete="SET NULL"), nullable=True
    )
    question_type: Mapped[str] = mapped_column(String(24), default="mcq", nullable=False)
    difficulty: Mapped[str] = mapped_column(String(16), default="medium", nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    options_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    answer_key: Mapped[str] = mapped_column(String(255), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(32), default="reviewed_bank", nullable=False)
    is_reviewed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)


class QuizAttempt(Base):
    """Student practice and Classroom Challenge quiz attempts with responses."""

    __tablename__ = "quiz_attempts"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=_uuid)
    user_id: Mapped[str | None] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    subject_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    unit_id: Mapped[str | None] = mapped_column(
        CHAR(36), ForeignKey("units_topics.id", ondelete="SET NULL"), nullable=True
    )
    mode: Mapped[str] = mapped_column(String(32), default="practice", nullable=False)
    participant_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    demo_identifier: Mapped[str | None] = mapped_column(String(64), nullable=True)
    question_ids_json: Mapped[list] = mapped_column(JSON, nullable=False)
    responses_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_score: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="in_progress", nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
