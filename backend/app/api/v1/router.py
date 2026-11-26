from fastapi import APIRouter

from app.api.v1 import (
    analytics,
    auth,
    classroom_challenge,
    predictions,
    records,
    students,
    subjects,
    syllabus,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(students.router)
api_router.include_router(subjects.router)
api_router.include_router(records.router)
api_router.include_router(analytics.router)
api_router.include_router(predictions.router)
api_router.include_router(syllabus.router)
api_router.include_router(classroom_challenge.router)
