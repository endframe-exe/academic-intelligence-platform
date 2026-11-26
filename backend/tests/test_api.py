import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app.core.config import Settings  # noqa: E402
from app.core.database import Base, get_db  # noqa: E402
from app.core.rate_limit import reset_rate_limits  # noqa: E402
from app.main import app  # noqa: E402
from seed_classroom_questions import seed_classroom_questions  # noqa: E402


@pytest.fixture()
def client():
    reset_rate_limits()
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as db:
        seed_classroom_questions(db)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client, engine
    app.dependency_overrides.clear()


def test_schema_has_all_11_requested_tables(client):
    _, engine = client
    tables = set(inspect(engine).get_table_names())
    expected = {
        "users",
        "student_profiles",
        "subjects",
        "units_topics",
        "assessments",
        "assessment_results",
        "attendance_records",
        "predictions",
        "syllabus_documents",
        "questions",
        "quiz_attempts",
    }
    assert expected.issubset(tables)


def test_niet_sem1_seed_totals_and_subjects(client):
    test_client, _ = client
    res = test_client.get("/api/v1/subjects")
    assert res.status_code == 200
    subjects = res.json()
    assert len(subjects) == 10

    non_audit = [s for s in subjects if not s["is_excluded_from_total"]]
    assert sum(s["credits"] for s in subjects) == 19
    assert sum(s["total_max_marks"] for s in non_audit) == 900

    by_code = {s["code"]: s for s in subjects}
    assert by_code["CAS0103"]["credits"] == 4
    assert by_code["CAS0103"]["internal_max_marks"] == 50
    assert by_code["CAS0103"]["external_max_marks"] == 100
    assert len(by_code["CAS0103"]["units_topics"]) == 5

    assert by_code["CMB0101"]["internal_max_marks"] == 100
    assert by_code["CMB0101"]["external_max_marks"] == 0
    assert by_code["CAU0101"]["credits"] == 0
    assert by_code["CAU0101"]["is_excluded_from_total"] is True


def test_register_login_records_and_prediction_sufficiency_gate(client):
    test_client, _ = client
    reg = test_client.post(
        "/api/v1/auth/register",
        json={
            "name": "Test Student",
            "email": "student@niet.edu.in",
            "password": "Password123",
        },
    )
    assert reg.status_code == 201
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Less than 3 records -> prediction must be withheld responsibly
    pred_low = test_client.post("/api/v1/predictions", json={}, headers=headers)
    assert pred_low.status_code == 201
    assert pred_low.json()["is_available"] is False
    assert pred_low.json()["risk_signal"] == "insufficient_data"

    subjects = test_client.get("/api/v1/subjects", headers=headers).json()
    cas_id = next(s["id"] for s in subjects if s["code"] == "CAS0103")

    # Reject obtained > max_marks
    bad_rec = test_client.post(
        "/api/v1/records",
        json={
            "subject_id": cas_id,
            "title": "Invalid Test",
            "assessment_type": "CIE",
            "max_marks": 50,
            "marks_obtained": 55,
        },
        headers=headers,
    )
    assert bad_rec.status_code == 422

    # Add 2 valid records -> prediction becomes available with MAE range, risk label & contributions
    for idx, score in enumerate((38, 42), start=1):
        ok_rec = test_client.post(
            "/api/v1/records",
            json={
                "subject_id": cas_id,
                "title": f"CIE Test {idx}",
                "assessment_type": "CIE",
                "max_marks": 50,
                "marks_obtained": score,
            },
            headers=headers,
        )
        assert ok_rec.status_code == 201

    pred_ok = test_client.post("/api/v1/predictions", json={"subject_id": cas_id}, headers=headers)
    assert pred_ok.status_code == 201
    data = pred_ok.json()
    assert data["is_available"] is True
    assert data["model_version"] == "model_v1"
    assert data["risk_signal"] in {"On Track", "Needs Revision", "High Support Priority"}
    assert data["lower_bound"] <= data["predicted_value"] <= data["upper_bound"]
    assert "feature_contributions" in data["metrics_json"]
    assert len(data["metrics_json"]["feature_contributions"]) == 4

    hist = test_client.get("/api/v1/predictions/history", headers=headers)
    assert hist.status_code == 200
    assert len(hist.json()) == 2

    card = test_client.get("/api/v1/predictions/model-card")
    assert card.status_code == 200
    card_json = card.json()
    assert "mae" in card_json["held_out_regression"]
    assert "rmse" in card_json["held_out_regression"]
    assert "r2" in card_json["held_out_regression"]
    assert "f1_weighted" in card_json["held_out_classification"]


def test_classroom_challenge_end_to_end(client):
    test_client, _ = client
    cfg = test_client.get("/api/v1/classroom-challenge/config")
    assert cfg.status_code == 200
    subjects = cfg.json()["subjects"]
    by_code = {s["code"]: s for s in subjects}
    for core_code in ("CAS0103", "CEC0101", "CCSAI0101", "CCSE0151", "CCSE0152", "CMB0101"):
        assert by_code[core_code]["question_count"] == 10

    cas = by_code["CAS0103"]
    start = test_client.post(
        "/api/v1/classroom-challenge/attempts",
        json={
            "subject_id": cas["id"],
            "num_questions": 10,
            "mode": "classroom_challenge",
            "participant_name": "Guest Participant",
            "demo_identifier": "DEMO-A11",
        },
    )
    assert start.status_code == 201
    attempt = start.json()
    assert len(attempt["questions"]) == 10

    answers = [
        {"question_id": q["id"], "answer": q["options"][0]}
        for q in attempt["questions"]
    ]
    sub = test_client.post(
        f"/api/v1/classroom-challenge/attempts/{attempt['id']}/submit",
        json={"answers": answers},
    )
    assert sub.status_code == 200
    sub_json = sub.json()
    assert sub_json["status"] == "submitted"
    assert sub_json["score"] is not None
    assert len(sub_json["topic_breakdown"]) >= 1

    # Also test single-step POST /classroom-challenge/attempts with answers payload
    direct_sub = test_client.post(
        "/api/v1/classroom-challenge/attempts",
        json={
            "subject_id": cas["id"],
            "num_questions": 10,
            "mode": "classroom_challenge",
            "participant_name": "Secret Name",
            "demo_identifier": "ERP-99999",
            "question_ids": [q["id"] for q in attempt["questions"]],
            "answers": answers,
        },
    )
    assert direct_sub.status_code == 201
    assert direct_sub.json()["status"] == "submitted"

    stats = test_client.get("/api/v1/classroom-challenge/stats")
    assert stats.status_code == 200
    stats_json = stats.json()
    assert stats_json["total_participants"] == 2
    assert stats_json["hardest_topic"] is not None
    raw_stats = stats.text
    assert "Secret Name" not in raw_stats
    assert "ERP-99999" not in raw_stats
    assert "Guest Participant" not in raw_stats


def test_demo_login_crud_csv_import_and_recommendations(client):
    test_client, _ = client
    demo_res = test_client.post("/api/v1/auth/demo-login")
    assert demo_res.status_code == 200
    token = demo_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    dash = test_client.get("/api/v1/analytics/dashboard", headers=headers)
    assert dash.status_code == 200
    assert dash.json()["assessments_count"] >= 9
    assert dash.json()["overall_percentage"] is not None

    recs = test_client.get("/api/v1/recommendations", headers=headers)
    assert recs.status_code == 200
    assert len(recs.json()) >= 1

    # Full CRUD on attendance
    subjects = test_client.get("/api/v1/subjects", headers=headers).json()
    cas_id = next(s["id"] for s in subjects if s["code"] == "CAS0103")
    att_create = test_client.post(
        "/api/v1/attendance",
        json={
            "subject_id": cas_id,
            "classes_attended": 18,
            "total_classes": 25,
            "recorded_date": "2026-11-22",
        },
        headers=headers,
    )
    assert att_create.status_code == 201
    att_id = att_create.json()["id"]

    att_patch = test_client.patch(
        f"/api/v1/attendance/{att_id}",
        json={"classes_attended": 20, "total_classes": 25},
        headers=headers,
    )
    assert att_patch.status_code == 200
    assert att_patch.json()["percentage"] == 80.0

    att_del = test_client.delete(f"/api/v1/attendance/{att_id}", headers=headers)
    assert att_del.status_code == 204

    # CSV preview + confirm
    csv_bytes = (
        b"subject_code,title,assessment_type,marks_obtained,max_marks,assessment_date\n"
        b"CAS0103,CT-2 Valid,CIE,45,50,2026-11-21\n"
        b"CAS0103,CT-2 Invalid,CIE,60,50,2026-11-21\n"
    )
    prev = test_client.post(
        "/api/v1/imports/preview",
        files={"file": ("marks.csv", csv_bytes, "text/csv")},
        headers=headers,
    )
    assert prev.status_code == 200
    assert prev.json()["valid_rows"] == 1
    assert prev.json()["invalid_rows"] == 1

    conf = test_client.post(
        "/api/v1/imports/confirm",
        json={"rows": prev.json()["rows"]},
        headers=headers,
    )
    assert conf.status_code == 200
    assert conf.json()["imported_count"] == 1


def test_syllabus_lab_upload_validation_tfidf_and_gemini_fallback(client):
    import io
    import docx as python_docx

    test_client, _ = client
    demo_res = test_client.post("/api/v1/auth/demo-login")
    headers = {"Authorization": f"Bearer {demo_res.json()['access_token']}"}
    subjects = test_client.get("/api/v1/subjects", headers=headers).json()
    cas = next(s for s in subjects if s["code"] == "CAS0103")

    # 1) Reject spoofed PDF missing %PDF- header
    bad_pdf = test_client.post(
        "/api/v1/documents",
        files={"file": ("fake.pdf", b"NOT_A_REAL_PDF", "application/pdf")},
        data={"subject_id": cas["id"]},
        headers=headers,
    )
    assert bad_pdf.status_code == 400

    # 2) Reject > 5 MB upload
    oversized = b"%PDF-1.4\n" + (b"0" * (5 * 1024 * 1024 + 64))
    too_big = test_client.post(
        "/api/v1/documents",
        files={"file": ("big.pdf", oversized, "application/pdf")},
        data={"subject_id": cas["id"]},
        headers=headers,
    )
    assert too_big.status_code == 413

    # 3) Valid DOCX upload -> extract -> review/save chunks -> TF-IDF + Gemini fallback
    doc_obj = python_docx.Document()
    doc_obj.add_paragraph("Unit 1: Matrices")
    doc_obj.add_paragraph("Rank of a matrix, orthogonal matrices, Cayley-Hamilton theorem.")
    doc_obj.add_paragraph("Unit 2: Vector Calculus")
    doc_obj.add_paragraph("Gradient, divergence, curl, Stokes and Gauss theorems.")
    buf = io.BytesIO()
    doc_obj.save(buf)

    up = test_client.post(
        "/api/v1/documents",
        files={
            "file": (
                "cas0103_syllabus.docx",
                buf.getvalue(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
        data={"subject_id": cas["id"]},
        headers=headers,
    )
    assert up.status_code == 201
    doc_json = up.json()
    assert doc_json["processing_status"] == "extracted"
    assert len(doc_json["extracted_structure_json"]["chunks"]) >= 1

    rev = test_client.patch(
        f"/api/v1/documents/{doc_json['id']}/review",
        json={
            "subject_name": "Calculus and Linear Algebra",
            "units": [
                {"title": "Matrices", "topics": ["Rank", "Cayley-Hamilton"]},
                {"title": "Vector Calculus", "topics": ["Curl", "Divergence"]},
            ],
        },
        headers=headers,
    )
    assert rev.status_code == 200
    assert rev.json()["processing_status"] == "reviewed"

    gen = test_client.post(
        "/api/v1/question-sets/generate",
        json={
            "subject_id": cas["id"],
            "syllabus_document_id": doc_json["id"],
            "num_questions": 5,
            "difficulty": "mixed",
        },
        headers=headers,
    )
    assert gen.status_code == 200
    gen_json = gen.json()
    assert gen_json["retrieved_chunks_count"] >= 1
    assert gen_json["source"] == "reviewed_bank"
    assert gen_json["ai_used"] is False
    assert "preloaded NIET bank" in gen_json["notice"]
    assert len(gen_json["questions"]) == 5


def test_idor_isolation_cors_frontend_url_and_rate_limiting(client):
    test_client, _ = client

    # 1) Verify CORS origins load from FRONTEND_URL
    cfg = Settings(FRONTEND_URL="https://scholia.vercel.app, https://preview.vercel.app")
    assert cfg.cors_origin_list == [
        "https://scholia.vercel.app",
        "https://preview.vercel.app",
    ]

    # 2) Register Student A and Student B
    reg_a = test_client.post(
        "/api/v1/auth/register",
        json={"name": "Student A", "email": "a@niet.edu.in", "password": "Password123"},
    )
    reg_b = test_client.post(
        "/api/v1/auth/register",
        json={"name": "Student B", "email": "b@niet.edu.in", "password": "Password123"},
    )
    headers_a = {"Authorization": f"Bearer {reg_a.json()['access_token']}"}
    headers_b = {"Authorization": f"Bearer {reg_b.json()['access_token']}"}

    subjects = test_client.get("/api/v1/subjects", headers=headers_a).json()
    cas_id = next(s["id"] for s in subjects if s["code"] == "CAS0103")

    # Student A creates a mark, attendance, and custom subject
    rec_a = test_client.post(
        "/api/v1/records",
        json={
            "subject_id": cas_id,
            "title": "A Private CIE",
            "assessment_type": "CIE",
            "max_marks": 50,
            "marks_obtained": 42,
        },
        headers=headers_a,
    ).json()
    att_a = test_client.post(
        "/api/v1/attendance",
        json={
            "subject_id": cas_id,
            "classes_attended": 10,
            "total_classes": 12,
            "recorded_date": "2026-11-20",
        },
        headers=headers_a,
    ).json()
    subj_a = test_client.post(
        "/api/v1/subjects",
        json={
            "code": "PRIV101",
            "name": "Private Subject",
            "credits": 2,
            "internal_max_marks": 50,
            "external_max_marks": 50,
        },
        headers=headers_a,
    ).json()

    # Student B cannot read/modify/delete Student A's private resources
    assert (
        test_client.patch(
            f"/api/v1/records/{rec_a['id']}", json={"marks_obtained": 10}, headers=headers_b
        ).status_code
        == 404
    )
    assert (
        test_client.delete(f"/api/v1/records/{rec_a['id']}", headers=headers_b).status_code == 404
    )
    assert (
        test_client.patch(
            f"/api/v1/attendance/{att_a['id']}", json={"classes_attended": 1}, headers=headers_b
        ).status_code
        == 404
    )
    assert (
        test_client.delete(f"/api/v1/attendance/{att_a['id']}", headers=headers_b).status_code
        == 404
    )
    assert (
        test_client.get(f"/api/v1/subjects/{subj_a['id']}/topics", headers=headers_b).status_code
        == 403
    )

    # 3) Verify rate limiter returns 429 after 20 auth/login calls
    statuses = [
        test_client.post(
            "/api/v1/auth/login",
            json={"email": "a@niet.edu.in", "password": "wrong-password"},
        ).status_code
        for _ in range(21)
    ]
    assert statuses[-1] == 429
