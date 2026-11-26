from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


# --- Auth & Profile ---


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    education_level: str = Field(default="undergraduate", max_length=64)
    institution: str = Field(
        default="Noida Institute of Engineering and Technology (NIET)", max_length=200
    )
    programme: str = Field(default="B.Tech CSE (Data Science)", max_length=160)
    academic_period: str = Field(default="Semester-I", max_length=64)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class DemoLoginRequest(BaseModel):
    name: str = Field(default="Classroom Demo Student", min_length=2, max_length=120)
    demo_identifier: str = Field(default="DEMO-CSDS-01", min_length=2, max_length=64)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: str
    role: str
    is_demo: bool
    created_at: datetime


class StudentProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    education_level: str
    institution: str
    programme: str
    academic_period: str
    grading_scheme: str
    demo_identifier: str | None
    weekly_study_hours: float | None
    updated_at: datetime


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
    profile: StudentProfileOut | None = None


class StudentMeOut(BaseModel):
    user: UserOut
    profile: StudentProfileOut


class StudentProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    education_level: str | None = Field(default=None, max_length=64)
    institution: str | None = Field(default=None, max_length=200)
    programme: str | None = Field(default=None, max_length=160)
    academic_period: str | None = Field(default=None, max_length=64)
    grading_scheme: str | None = Field(default=None, max_length=64)
    demo_identifier: str | None = Field(default=None, max_length=64)
    weekly_study_hours: float | None = Field(default=None, ge=0, le=120)


# --- Subjects & Units ---


class UnitTopicOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    subject_id: str
    parent_id: str | None
    order_index: int
    node_type: str
    title: str
    description: str | None


class SubjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str | None
    programme: str
    academic_period: str
    code: str
    name: str
    credits: int
    category: str
    internal_label: str
    internal_max_marks: int
    external_label: str
    external_max_marks: int
    total_max_marks: int
    is_excluded_from_total: bool
    units_topics: list[UnitTopicOut] = []


class SubjectCreate(BaseModel):
    programme: str = Field(default="B.Tech CSE (Data Science)", max_length=160)
    academic_period: str = Field(default="Semester-I", max_length=64)
    code: str = Field(min_length=2, max_length=32)
    name: str = Field(min_length=2, max_length=200)
    credits: int = Field(ge=0, le=10)
    category: Literal["theory", "practical", "audit"] = "theory"
    internal_label: Literal["CIE", "PS"] = "CIE"
    internal_max_marks: int = Field(ge=0, le=200)
    external_label: Literal["ESE", "PE", "NONE"] = "ESE"
    external_max_marks: int = Field(ge=0, le=200)
    is_excluded_from_total: bool = False
    units: list[str] = Field(default_factory=list)


# --- Academic Records & Attendance ---


class AcademicRecordCreate(BaseModel):
    subject_id: str
    unit_id: str | None = None
    title: str = Field(min_length=2, max_length=200)
    assessment_type: Literal["CIE", "ESE", "PS", "PE", "QUIZ", "ASSIGNMENT", "INTERNAL", "AUDIT"]
    max_marks: float = Field(gt=0, le=500)
    marks_obtained: float = Field(ge=0, le=500)
    assessment_date: date | None = None
    academic_period: str = Field(default="Semester-I", max_length=64)
    study_hours_logged: float | None = Field(default=None, ge=0, le=100)
    notes: str | None = None

    @model_validator(mode="after")
    def validate_marks(self) -> "AcademicRecordCreate":
        if self.marks_obtained > self.max_marks:
            raise ValueError("marks_obtained cannot exceed max_marks")
        return self


class AcademicRecordUpdate(BaseModel):
    marks_obtained: float | None = Field(default=None, ge=0, le=500)
    study_hours_logged: float | None = Field(default=None, ge=0, le=100)
    notes: str | None = None


class AcademicRecordOut(BaseModel):
    id: str
    assessment_id: str
    subject_id: str
    subject_code: str
    subject_name: str
    unit_id: str | None
    title: str
    assessment_type: str
    max_marks: float
    marks_obtained: float
    percentage: float
    assessment_date: date | None
    academic_period: str
    grading_scheme_snapshot: str
    study_hours_logged: float | None
    notes: str | None
    recorded_at: datetime


class AttendanceCreate(BaseModel):
    subject_id: str
    academic_period: str = Field(default="Semester-I", max_length=64)
    classes_attended: int = Field(ge=0, le=1000)
    total_classes: int = Field(gt=0, le=1000)
    recorded_date: date

    @model_validator(mode="after")
    def validate_attendance(self) -> "AttendanceCreate":
        if self.classes_attended > self.total_classes:
            raise ValueError("classes_attended cannot exceed total_classes")
        return self


class AttendanceUpdate(BaseModel):
    classes_attended: int | None = Field(default=None, ge=0, le=1000)
    total_classes: int | None = Field(default=None, gt=0, le=1000)
    recorded_date: date | None = None


class AttendanceOut(BaseModel):
    id: str
    subject_id: str
    subject_code: str
    subject_name: str
    academic_period: str
    classes_attended: int
    total_classes: int
    percentage: float
    recorded_date: date
    updated_at: datetime


class CsvImportPreviewRow(BaseModel):
    row_number: int
    subject_code: str
    title: str
    assessment_type: str
    marks_obtained: float
    max_marks: float
    assessment_date: date | None = None
    study_hours_logged: float | None = None
    valid: bool
    error: str | None = None


class CsvImportPreviewOut(BaseModel):
    total_rows: int
    valid_rows: int
    invalid_rows: int
    rows: list[CsvImportPreviewRow]


class CsvImportConfirmRequest(BaseModel):
    rows: list[CsvImportPreviewRow]


# --- Dashboard & Recommendations ---


class SubjectSummaryOut(BaseModel):
    subject_id: str
    code: str
    name: str
    credits: int
    category: str
    is_excluded_from_total: bool
    total_max_marks: int
    obtained_marks: float
    recorded_max_marks: float
    percentage: float | None
    attendance_percentage: float | None
    assessments_count: int


class DashboardOut(BaseModel):
    overall_percentage: float | None
    total_credits: int
    total_credit_marks_scale: int
    recorded_marks_total: float
    recorded_max_total: float
    attendance_overall_percentage: float | None
    assessments_count: int
    subjects: list[SubjectSummaryOut]
    trend: list[dict]
    strengths: list[str]
    improvement_areas: list[str]
    data_coverage_note: str


class RecommendationItem(BaseModel):
    id: str
    subject_code: str | None
    subject_name: str | None
    priority: Literal["high", "medium", "low"]
    title: str
    evidence: str
    action: str
    suggested_hours_per_week: float
    source: str


class StudyPlanRequest(BaseModel):
    weekly_hours_available: float = Field(default=14.0, gt=0, le=80)
    exam_days_remaining: int = Field(default=21, ge=1, le=365)


class StudySessionOut(BaseModel):
    day: str
    subject_code: str
    subject_name: str
    focus_topic: str
    duration_hours: float
    rationale: str


class StudyPlanOut(BaseModel):
    weekly_hours_available: float
    exam_days_remaining: int
    sessions: list[StudySessionOut]
    ai_summary: str
    ai_used: bool


# --- Predictions ---


class PredictionRunRequest(BaseModel):
    subject_id: str | None = None


class PredictionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    student_id: str
    subject_id: str | None
    target_type: str
    predicted_value: float | None
    lower_bound: float | None
    upper_bound: float | None
    risk_signal: str | None
    model_name: str
    model_version: str
    metrics_json: dict | None
    explanation: str
    is_available: bool
    created_at: datetime


# --- Syllabus Lab & Questions ---


class SyllabusStructureReview(BaseModel):
    subject_name: str | None = None
    units: list[dict]
    chunks: list[str] | None = None


class SyllabusDocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    owner_id: str
    subject_id: str | None
    filename: str
    file_type: str
    processing_status: str
    extracted_structure_json: dict | None
    created_at: datetime


class QuestionGenerateRequest(BaseModel):
    subject_id: str
    unit_id: str | None = None
    syllabus_document_id: str | None = None
    num_questions: int = Field(default=5, ge=1, le=15)
    difficulty: Literal["easy", "medium", "hard", "mixed"] = "mixed"


class QuestionPublicOut(BaseModel):
    id: str
    subject_id: str
    unit_id: str | None
    question_type: str
    difficulty: str
    question_text: str
    options: list[str] | None = None
    source: str


class QuizAnswerItem(BaseModel):
    question_id: str
    answer: str


class QuizSubmitRequest(BaseModel):
    answers: list[QuizAnswerItem]


class QuizAttemptCreate(BaseModel):
    subject_id: str
    unit_id: str | None = None
    num_questions: int = Field(default=10, ge=1, le=20)
    mode: Literal["practice", "classroom_challenge"] = "practice"
    participant_name: str | None = Field(default=None, max_length=120)
    demo_identifier: str | None = Field(default=None, max_length=64)
    question_ids: list[str] | None = None
    answers: list[QuizAnswerItem] | None = None


class QuizQuestionFeedback(BaseModel):
    question_id: str
    question_text: str
    difficulty: str
    topic_title: str = "Core Concepts"
    user_answer: str
    correct_answer: str
    is_correct: bool
    explanation: str


class TopicBreakdownItem(BaseModel):
    topic: str
    correct: int
    total: int
    percentage: float
    status: Literal["Strength", "Needs Review"]


class QuizAttemptOut(BaseModel):
    id: str
    subject_id: str
    subject_code: str | None = None
    subject_name: str | None = None
    unit_id: str | None
    mode: str
    status: str
    total_questions: int
    score: float | None
    max_score: float
    questions: list[QuestionPublicOut] = []
    feedback: list[QuizQuestionFeedback] = []
    difficulty_breakdown: dict = {}
    topic_breakdown: list[TopicBreakdownItem] = []
    started_at: datetime
    submitted_at: datetime | None
