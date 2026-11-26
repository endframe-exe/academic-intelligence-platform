import csv
import io
from datetime import date

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.academic import (
    Assessment,
    AssessmentResult,
    AttendanceRecord,
    StudentProfile,
    Subject,
    User,
)
from app.schemas.academic import (
    AcademicRecordCreate,
    AcademicRecordOut,
    AcademicRecordUpdate,
    AttendanceCreate,
    AttendanceOut,
    AttendanceUpdate,
    CsvImportConfirmRequest,
    CsvImportPreviewOut,
    CsvImportPreviewRow,
)

router = APIRouter(tags=["Academic Records & Imports"])


def _allowed_subject(db: Session, subject_id: str, user_id: str) -> Subject:
    subject = db.get(Subject, subject_id)
    if not subject or (subject.user_id is not None and subject.user_id != user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found.")
    return subject


def _to_record_out(res: AssessmentResult, assessment: Assessment, subject: Subject) -> AcademicRecordOut:
    pct = round((res.marks_obtained / assessment.max_marks) * 100.0, 2) if assessment.max_marks > 0 else 0.0
    return AcademicRecordOut(
        id=res.id,
        assessment_id=assessment.id,
        subject_id=subject.id,
        subject_code=subject.code,
        subject_name=subject.name,
        unit_id=assessment.unit_id,
        title=assessment.title,
        assessment_type=assessment.assessment_type,
        max_marks=assessment.max_marks,
        marks_obtained=res.marks_obtained,
        percentage=pct,
        assessment_date=assessment.assessment_date,
        academic_period=assessment.academic_period,
        grading_scheme_snapshot=res.grading_scheme_snapshot,
        study_hours_logged=res.study_hours_logged,
        notes=res.notes,
        recorded_at=res.recorded_at,
    )


@router.get("/records", response_model=list[AcademicRecordOut])
def list_records(
    subject_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = (
        select(AssessmentResult, Assessment, Subject)
        .join(Assessment, AssessmentResult.assessment_id == Assessment.id)
        .join(Subject, Assessment.subject_id == Subject.id)
        .where(AssessmentResult.student_id == current_user.id)
    )
    if subject_id:
        stmt = stmt.where(Assessment.subject_id == subject_id)
    stmt = stmt.order_by(AssessmentResult.recorded_at.desc())
    rows = db.execute(stmt).all()
    return [_to_record_out(res, ass, subj) for res, ass, subj in rows]


@router.post("/records", response_model=AcademicRecordOut, status_code=status.HTTP_201_CREATED)
def create_record(
    payload: AcademicRecordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    subject = _allowed_subject(db, payload.subject_id, current_user.id)
    profile = db.scalar(select(StudentProfile).where(StudentProfile.user_id == current_user.id))
    scheme = profile.grading_scheme if profile else "NIET 900-Mark Credit System"

    assessment = Assessment(
        subject_id=subject.id,
        unit_id=payload.unit_id,
        user_id=current_user.id,
        title=payload.title.strip(),
        assessment_type=payload.assessment_type,
        max_marks=payload.max_marks,
        assessment_date=payload.assessment_date,
        academic_period=payload.academic_period,
    )
    db.add(assessment)
    db.flush()

    res = AssessmentResult(
        student_id=current_user.id,
        assessment_id=assessment.id,
        marks_obtained=payload.marks_obtained,
        grading_scheme_snapshot=scheme,
        study_hours_logged=payload.study_hours_logged,
        notes=payload.notes,
    )
    db.add(res)
    db.commit()
    db.refresh(res)
    db.refresh(assessment)
    return _to_record_out(res, assessment, subject)


@router.patch("/records/{record_id}", response_model=AcademicRecordOut)
def update_record(
    record_id: str,
    payload: AcademicRecordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    res = db.get(AssessmentResult, record_id)
    if not res or res.student_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found.")
    assessment = db.get(Assessment, res.assessment_id)
    subject = db.get(Subject, assessment.subject_id)

    if payload.marks_obtained is not None:
        if payload.marks_obtained > assessment.max_marks:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="marks_obtained cannot exceed max_marks.",
            )
        res.marks_obtained = payload.marks_obtained
    if payload.study_hours_logged is not None:
        res.study_hours_logged = payload.study_hours_logged
    if payload.notes is not None:
        res.notes = payload.notes

    db.commit()
    db.refresh(res)
    return _to_record_out(res, assessment, subject)


@router.delete("/records/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_record(
    record_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    res = db.get(AssessmentResult, record_id)
    if not res or res.student_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found.")
    assessment = db.get(Assessment, res.assessment_id)
    db.delete(res)
    if assessment and assessment.user_id == current_user.id:
        db.delete(assessment)
    db.commit()


@router.get("/attendance", response_model=list[AttendanceOut])
def list_attendance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.execute(
        select(AttendanceRecord, Subject)
        .join(Subject, AttendanceRecord.subject_id == Subject.id)
        .where(AttendanceRecord.student_id == current_user.id)
        .order_by(AttendanceRecord.recorded_date.desc())
    ).all()
    return [
        AttendanceOut(
            id=att.id,
            subject_id=subj.id,
            subject_code=subj.code,
            subject_name=subj.name,
            academic_period=att.academic_period,
            classes_attended=att.classes_attended,
            total_classes=att.total_classes,
            percentage=round((att.classes_attended / att.total_classes) * 100.0, 2),
            recorded_date=att.recorded_date,
            updated_at=att.updated_at,
        )
        for att, subj in rows
    ]


@router.post("/attendance", response_model=AttendanceOut, status_code=status.HTTP_201_CREATED)
def upsert_attendance(
    payload: AttendanceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    subject = _allowed_subject(db, payload.subject_id, current_user.id)
    att = AttendanceRecord(
        student_id=current_user.id,
        subject_id=subject.id,
        academic_period=payload.academic_period,
        classes_attended=payload.classes_attended,
        total_classes=payload.total_classes,
        recorded_date=payload.recorded_date,
    )
    db.add(att)
    db.commit()
    db.refresh(att)
    return AttendanceOut(
        id=att.id,
        subject_id=subject.id,
        subject_code=subject.code,
        subject_name=subject.name,
        academic_period=att.academic_period,
        classes_attended=att.classes_attended,
        total_classes=att.total_classes,
        percentage=round((att.classes_attended / att.total_classes) * 100.0, 2),
        recorded_date=att.recorded_date,
        updated_at=att.updated_at,
    )


@router.patch("/attendance/{attendance_id}", response_model=AttendanceOut)
def update_attendance(
    attendance_id: str,
    payload: AttendanceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    att = db.get(AttendanceRecord, attendance_id)
    if not att or att.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Attendance record not found."
        )
    new_attended = (
        payload.classes_attended if payload.classes_attended is not None else att.classes_attended
    )
    new_total = payload.total_classes if payload.total_classes is not None else att.total_classes
    if new_attended > new_total:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="classes_attended cannot exceed total_classes.",
        )
    att.classes_attended = new_attended
    att.total_classes = new_total
    if payload.recorded_date is not None:
        att.recorded_date = payload.recorded_date
    db.commit()
    db.refresh(att)
    subject = db.get(Subject, att.subject_id)
    return AttendanceOut(
        id=att.id,
        subject_id=subject.id,
        subject_code=subject.code,
        subject_name=subject.name,
        academic_period=att.academic_period,
        classes_attended=att.classes_attended,
        total_classes=att.total_classes,
        percentage=round((att.classes_attended / att.total_classes) * 100.0, 2),
        recorded_date=att.recorded_date,
        updated_at=att.updated_at,
    )


@router.delete("/attendance/{attendance_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attendance(
    attendance_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    att = db.get(AttendanceRecord, attendance_id)
    if not att or att.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Attendance record not found."
        )
    db.delete(att)
    db.commit()


@router.get("/imports/template")
def download_csv_template():
    csv_text = (
        "subject_code,title,assessment_type,marks_obtained,max_marks,assessment_date,study_hours_logged\n"
        "CAS0103,CIE-1 Calculus Test,CIE,41,50,2026-10-15,6\n"
        "CCSAI0101,CIE-1 AI Quiz,CIE,44,50,2026-10-18,4.5\n"
    )
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=academic_records_template.csv"},
    )


@router.post("/imports/preview", response_model=CsvImportPreviewOut)
async def preview_csv_import(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    raw = await file.read()
    text = raw.decode("utf-8", errors="ignore")
    reader = csv.DictReader(io.StringIO(text))

    available_subjects = db.scalars(
        select(Subject).where(
            or_(Subject.user_id.is_(None), Subject.user_id == current_user.id)
        )
    ).all()
    code_map = {s.code.upper(): s for s in available_subjects}
    allowed_types = {"CIE", "ESE", "PS", "PE", "QUIZ", "ASSIGNMENT", "INTERNAL", "AUDIT"}

    preview_rows: list[CsvImportPreviewRow] = []
    valid_count = 0
    invalid_count = 0

    for idx, row in enumerate(reader, start=1):
        code = (row.get("subject_code") or "").strip().upper()
        title = (row.get("title") or "").strip()
        a_type = (row.get("assessment_type") or "CIE").strip().upper()
        errors: list[str] = []

        if code not in code_map:
            errors.append(f"Unknown subject_code '{code}'")
        if not title:
            errors.append("Missing title")
        if a_type not in allowed_types:
            errors.append(f"Unsupported assessment_type '{a_type}'")

        try:
            obt = float(row.get("marks_obtained") or 0)
            mx = float(row.get("max_marks") or 0)
            if mx <= 0:
                errors.append("max_marks must be > 0")
            if obt < 0 or obt > mx:
                errors.append("marks_obtained must be between 0 and max_marks")
        except ValueError:
            obt, mx = 0.0, 0.0
            errors.append("Invalid numeric marks")

        parsed_date: date | None = None
        raw_date = (row.get("assessment_date") or "").strip()
        if raw_date:
            try:
                parsed_date = date.fromisoformat(raw_date)
            except ValueError:
                errors.append("assessment_date must be YYYY-MM-DD")

        hrs: float | None = None
        raw_hrs = (row.get("study_hours_logged") or "").strip()
        if raw_hrs:
            try:
                hrs = float(raw_hrs)
            except ValueError:
                errors.append("Invalid study_hours_logged")

        is_valid = len(errors) == 0
        if is_valid:
            valid_count += 1
        else:
            invalid_count += 1

        preview_rows.append(
            CsvImportPreviewRow(
                row_number=idx,
                subject_code=code,
                title=title or "Untitled",
                assessment_type=a_type,
                marks_obtained=obt,
                max_marks=mx,
                assessment_date=parsed_date,
                study_hours_logged=hrs,
                valid=is_valid,
                error="; ".join(errors) if errors else None,
            )
        )

    return CsvImportPreviewOut(
        total_rows=len(preview_rows),
        valid_rows=valid_count,
        invalid_rows=invalid_count,
        rows=preview_rows,
    )


@router.post("/imports/confirm")
def confirm_csv_import(
    payload: CsvImportConfirmRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    valid_rows = [r for r in payload.rows if r.valid]
    if not valid_rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid rows supplied for import.",
        )

    profile = db.scalar(select(StudentProfile).where(StudentProfile.user_id == current_user.id))
    scheme = profile.grading_scheme if profile else "NIET 900-Mark Credit System"
    period = profile.academic_period if profile else "Semester-I"
    available_subjects = db.scalars(
        select(Subject).where(
            or_(Subject.user_id.is_(None), Subject.user_id == current_user.id)
        )
    ).all()
    code_map = {s.code.upper(): s for s in available_subjects}

    imported = 0
    for row in valid_rows:
        subject = code_map.get(row.subject_code.upper())
        if not subject or row.marks_obtained > row.max_marks or row.max_marks <= 0:
            continue
        assessment = Assessment(
            subject_id=subject.id,
            user_id=current_user.id,
            title=row.title,
            assessment_type=row.assessment_type,
            max_marks=row.max_marks,
            assessment_date=row.assessment_date,
            academic_period=period,
        )
        db.add(assessment)
        db.flush()
        db.add(
            AssessmentResult(
                student_id=current_user.id,
                assessment_id=assessment.id,
                marks_obtained=row.marks_obtained,
                grading_scheme_snapshot=scheme,
                study_hours_logged=row.study_hours_logged,
                notes="Imported via CSV validation pipeline",
            )
        )
        imported += 1

    db.commit()
    return {"imported_count": imported}
