"""Initial 11-table MySQL schema for AI Academic Intelligence Platform.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-11-26
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.CHAR(length=36), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("is_demo", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "student_profiles",
        sa.Column("id", sa.CHAR(length=36), nullable=False),
        sa.Column("user_id", sa.CHAR(length=36), nullable=False),
        sa.Column("education_level", sa.String(length=64), nullable=False),
        sa.Column("institution", sa.String(length=200), nullable=False),
        sa.Column("programme", sa.String(length=160), nullable=False),
        sa.Column("academic_period", sa.String(length=64), nullable=False),
        sa.Column("grading_scheme", sa.String(length=64), nullable=False),
        sa.Column("demo_identifier", sa.String(length=64), nullable=True),
        sa.Column("weekly_study_hours", sa.Float(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    op.create_table(
        "subjects",
        sa.Column("id", sa.CHAR(length=36), nullable=False),
        sa.Column("user_id", sa.CHAR(length=36), nullable=True),
        sa.Column("programme", sa.String(length=160), nullable=False),
        sa.Column("academic_period", sa.String(length=64), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("credits", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("internal_label", sa.String(length=16), nullable=False),
        sa.Column("internal_max_marks", sa.Integer(), nullable=False),
        sa.Column("external_label", sa.String(length=16), nullable=False),
        sa.Column("external_max_marks", sa.Integer(), nullable=False),
        sa.Column("total_max_marks", sa.Integer(), nullable=False),
        sa.Column("is_excluded_from_total", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_subjects_user_id", "subjects", ["user_id"])
    op.create_index("ix_subjects_programme", "subjects", ["programme"])
    op.create_index("ix_subjects_academic_period", "subjects", ["academic_period"])
    op.create_index("ix_subjects_code", "subjects", ["code"])

    op.create_table(
        "units_topics",
        sa.Column("id", sa.CHAR(length=36), nullable=False),
        sa.Column("subject_id", sa.CHAR(length=36), nullable=False),
        sa.Column("parent_id", sa.CHAR(length=36), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("node_type", sa.String(length=24), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["parent_id"], ["units_topics.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_units_topics_subject_id", "units_topics", ["subject_id"])

    op.create_table(
        "assessments",
        sa.Column("id", sa.CHAR(length=36), nullable=False),
        sa.Column("subject_id", sa.CHAR(length=36), nullable=False),
        sa.Column("unit_id", sa.CHAR(length=36), nullable=True),
        sa.Column("user_id", sa.CHAR(length=36), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("assessment_type", sa.String(length=32), nullable=False),
        sa.Column("max_marks", sa.Float(), nullable=False),
        sa.Column("assessment_date", sa.Date(), nullable=True),
        sa.Column("academic_period", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["unit_id"], ["units_topics.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_assessments_subject_id", "assessments", ["subject_id"])
    op.create_index("ix_assessments_user_id", "assessments", ["user_id"])

    op.create_table(
        "assessment_results",
        sa.Column("id", sa.CHAR(length=36), nullable=False),
        sa.Column("student_id", sa.CHAR(length=36), nullable=False),
        sa.Column("assessment_id", sa.CHAR(length=36), nullable=False),
        sa.Column("marks_obtained", sa.Float(), nullable=False),
        sa.Column("grading_scheme_snapshot", sa.String(length=64), nullable=False),
        sa.Column("study_hours_logged", sa.Float(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["assessment_id"], ["assessments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_id", "assessment_id", name="uq_student_assessment_result"),
    )
    op.create_index("ix_assessment_results_student_id", "assessment_results", ["student_id"])
    op.create_index("ix_assessment_results_assessment_id", "assessment_results", ["assessment_id"])

    op.create_table(
        "attendance_records",
        sa.Column("id", sa.CHAR(length=36), nullable=False),
        sa.Column("student_id", sa.CHAR(length=36), nullable=False),
        sa.Column("subject_id", sa.CHAR(length=36), nullable=False),
        sa.Column("academic_period", sa.String(length=64), nullable=False),
        sa.Column("classes_attended", sa.Integer(), nullable=False),
        sa.Column("total_classes", sa.Integer(), nullable=False),
        sa.Column("recorded_date", sa.Date(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_attendance_records_student_id", "attendance_records", ["student_id"])
    op.create_index("ix_attendance_records_subject_id", "attendance_records", ["subject_id"])

    op.create_table(
        "predictions",
        sa.Column("id", sa.CHAR(length=36), nullable=False),
        sa.Column("student_id", sa.CHAR(length=36), nullable=False),
        sa.Column("subject_id", sa.CHAR(length=36), nullable=True),
        sa.Column("target_type", sa.String(length=64), nullable=False),
        sa.Column("predicted_value", sa.Float(), nullable=True),
        sa.Column("lower_bound", sa.Float(), nullable=True),
        sa.Column("upper_bound", sa.Float(), nullable=True),
        sa.Column("risk_signal", sa.String(length=32), nullable=True),
        sa.Column("model_name", sa.String(length=64), nullable=False),
        sa.Column("model_version", sa.String(length=32), nullable=False),
        sa.Column("metrics_json", sa.JSON(), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("is_available", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_predictions_student_id", "predictions", ["student_id"])
    op.create_index("ix_predictions_subject_id", "predictions", ["subject_id"])

    op.create_table(
        "syllabus_documents",
        sa.Column("id", sa.CHAR(length=36), nullable=False),
        sa.Column("owner_id", sa.CHAR(length=36), nullable=False),
        sa.Column("subject_id", sa.CHAR(length=36), nullable=True),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("file_type", sa.String(length=32), nullable=False),
        sa.Column("storage_path", sa.String(length=500), nullable=False),
        sa.Column("processing_status", sa.String(length=32), nullable=False),
        sa.Column(
            "extracted_text",
            sa.Text().with_variant(mysql.LONGTEXT(), "mysql"),
            nullable=True,
        ),
        sa.Column("extracted_structure_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_syllabus_documents_owner_id", "syllabus_documents", ["owner_id"])

    op.create_table(
        "questions",
        sa.Column("id", sa.CHAR(length=36), nullable=False),
        sa.Column("subject_id", sa.CHAR(length=36), nullable=False),
        sa.Column("unit_id", sa.CHAR(length=36), nullable=True),
        sa.Column("syllabus_document_id", sa.CHAR(length=36), nullable=True),
        sa.Column("question_type", sa.String(length=24), nullable=False),
        sa.Column("difficulty", sa.String(length=16), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("options_json", sa.JSON(), nullable=True),
        sa.Column("answer_key", sa.String(length=255), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("is_reviewed", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["syllabus_document_id"], ["syllabus_documents.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["unit_id"], ["units_topics.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_questions_subject_id", "questions", ["subject_id"])
    op.create_index("ix_questions_unit_id", "questions", ["unit_id"])

    op.create_table(
        "quiz_attempts",
        sa.Column("id", sa.CHAR(length=36), nullable=False),
        sa.Column("user_id", sa.CHAR(length=36), nullable=True),
        sa.Column("subject_id", sa.CHAR(length=36), nullable=False),
        sa.Column("unit_id", sa.CHAR(length=36), nullable=True),
        sa.Column("mode", sa.String(length=32), nullable=False),
        sa.Column("participant_name", sa.String(length=120), nullable=True),
        sa.Column("demo_identifier", sa.String(length=64), nullable=True),
        sa.Column("question_ids_json", sa.JSON(), nullable=False),
        sa.Column("responses_json", sa.JSON(), nullable=True),
        sa.Column("total_questions", sa.Integer(), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("max_score", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["unit_id"], ["units_topics.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_quiz_attempts_user_id", "quiz_attempts", ["user_id"])
    op.create_index("ix_quiz_attempts_subject_id", "quiz_attempts", ["subject_id"])


def downgrade() -> None:
    op.drop_table("quiz_attempts")
    op.drop_table("questions")
    op.drop_table("syllabus_documents")
    op.drop_table("predictions")
    op.drop_table("attendance_records")
    op.drop_table("assessment_results")
    op.drop_table("assessments")
    op.drop_table("units_topics")
    op.drop_table("subjects")
    op.drop_table("student_profiles")
    op.drop_table("users")
