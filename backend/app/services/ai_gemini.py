import json
import logging
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.services.document_parser import fallback_extract_structure

logger = logging.getLogger(__name__)


class GeneratedMCQ(BaseModel):
    question_text: str
    options: list[str] = Field(min_length=4, max_length=4)
    answer_key: str
    difficulty: Literal["easy", "medium", "hard"]
    explanation: str


class ExtractedUnit(BaseModel):
    title: str
    topics: list[str]


class ExtractedSyllabusSchema(BaseModel):
    subject_name: str
    units: list[ExtractedUnit]


def _get_gemini_client():
    settings = get_settings()
    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY.startswith("your-"):
        return None, settings, "GEMINI_API_KEY is not configured"
    try:
        from google import genai

        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        return client, settings, None
    except Exception as exc:  # pragma: no cover - defensive runtime fallback
        logger.warning("Gemini client unavailable: %s", exc)
        return None, settings, f"Gemini SDK unavailable: {exc}"


def extract_syllabus_structure_with_gemini(
    raw_text: str, subject_name: str
) -> tuple[dict[str, Any], bool]:
    """Extract subject name, units, and topics from syllabus text only (zero PII)."""
    client, settings, _ = _get_gemini_client()
    if client is None:
        return fallback_extract_structure(raw_text, subject_name), False

    excerpt = raw_text[:12000]
    prompt = (
        "You are an academic curriculum parser. Extract ONLY from the syllabus text below.\n"
        f"Reference Subject: {subject_name}\n"
        "Return the subject name, units/modules, and their subtopics.\n\n"
        f"SYLLABUS TEXT:\n{excerpt}"
    )
    try:
        from google.genai import types

        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ExtractedSyllabusSchema,
                temperature=0.2,
            ),
        )
        parsed = json.loads(response.text or "{}")
        if isinstance(parsed, dict) and isinstance(parsed.get("units"), list) and parsed["units"]:
            return parsed, True
    except Exception as exc:  # pragma: no cover
        logger.warning("Gemini syllabus extraction failed, falling back: %s", exc)

    return fallback_extract_structure(raw_text, subject_name), False


def generate_questions_with_gemini(
    *,
    subject_code: str,
    subject_name: str,
    unit_title: str | None,
    context_text: str,
    num_questions: int,
    difficulty: str,
) -> tuple[list[dict[str, Any]], bool, str]:
    """Generate syllabus-grounded MCQs using google-genai (gemini-2.5-flash) with zero PII."""
    client, settings, reason = _get_gemini_client()
    if client is None:
        return (
            [],
            False,
            f"{reason}. Serving reviewed questions from the preloaded NIET bank.",
        )

    diff_instruction = (
        "a balanced mix of easy, medium, and hard"
        if difficulty == "mixed"
        else f"difficulty '{difficulty}'"
    )
    prompt = (
        "Generate syllabus-grounded multiple-choice questions for undergraduate students.\n"
        "Base every question strictly on the retrieved syllabus chunks below. "
        "Each question must have 4 distinct options, an answer_key matching one option verbatim, "
        "and a concise explanation.\n"
        f"Course: {subject_code} - {subject_name}\n"
        f"Unit/Module Focus: {unit_title or 'All Units'}\n"
        f"Count: {num_questions}\n"
        f"Difficulty: {diff_instruction}\n\n"
        f"RETRIEVED SYLLABUS CHUNKS:\n{context_text[:9000]}"
    )

    try:
        from google.genai import types

        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=list[GeneratedMCQ],
                temperature=0.3,
            ),
        )
        data = json.loads(response.text or "[]")
        validated: list[dict[str, Any]] = []
        if isinstance(data, list):
            for item in data[:num_questions]:
                q_text = str(item.get("question_text", "")).strip()
                options = item.get("options") or []
                answer_key = str(item.get("answer_key", "")).strip()
                explanation = str(item.get("explanation", "")).strip()
                diff = str(item.get("difficulty", "medium")).lower()
                if diff not in {"easy", "medium", "hard"}:
                    diff = "medium"
                if (
                    q_text
                    and isinstance(options, list)
                    and len(options) == 4
                    and answer_key in options
                    and explanation
                ):
                    validated.append(
                        {
                            "question_text": q_text,
                            "options": [str(o) for o in options],
                            "answer_key": answer_key,
                            "difficulty": diff,
                            "explanation": explanation,
                        }
                    )
        if validated:
            return (
                validated,
                True,
                f"Generated {len(validated)} syllabus-grounded MCQs via Gemini 2.5 Flash.",
            )
        return (
            [],
            False,
            "Gemini returned no valid MCQs. Serving reviewed questions from the preloaded NIET bank.",
        )
    except Exception as exc:  # pragma: no cover
        logger.warning("Gemini question generation failed: %s", exc)
        return (
            [],
            False,
            f"Gemini API unavailable or rate-limited ({type(exc).__name__}). Serving reviewed questions from the preloaded NIET bank.",
        )


def generate_study_advice_with_gemini(
    *,
    anonymized_summary: dict[str, Any],
    sessions: list[dict[str, Any]],
) -> tuple[str, bool]:
    """Turn structured rule/ML findings into clear study guidance without PII."""
    client, settings, _ = _get_gemini_client()
    fallback_text = (
        "Prioritized study plan derived from recorded assessment percentages, "
        "credit weights, attendance levels, and available weekly hours. "
        "Allocate extra revision blocks to lower-scoring, higher-credit courses first."
    )
    if client is None:
        return fallback_text, False

    prompt = (
        "You are an academic study advisor. Provide a concise, encouraging, evidence-based "
        "2-to-3 sentence study summary using ONLY the anonymized metrics below. "
        "Never claim guaranteed exam scores.\n"
        f"METRICS: {json.dumps(anonymized_summary)}\n"
        f"PLANNED SESSIONS: {json.dumps(sessions[:7])}"
    )
    try:
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
        )
        text = (response.text or "").strip()
        if text:
            return text, True
    except Exception as exc:  # pragma: no cover
        logger.warning("Gemini study summary failed: %s", exc)

    return fallback_text, False
