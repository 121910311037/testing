"""Emotion check-in endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..schemas import AssessmentRequest, AssessmentResponse
from ..services.emotion_service import analyze
from ..services.recommendation_service import make_recommendation
from ..services.storage import add_assessment, list_assessments, new_id, utc_now

router = APIRouter(prefix="/api/assessments", tags=["emotion check-in"])


@router.post("/", response_model=AssessmentResponse)
def create_assessment(payload: AssessmentRequest) -> dict:
    result = analyze(payload.responses, payload.text)
    recommendation = make_recommendation(result["primary_emotion"], result["risk_level"])
    record = {
        "assessment_id": new_id("assessment"),
        "patient_id": payload.patient_id.strip(),
        **result,
        "recommendation": recommendation,
        "recorded_at": utc_now(),
    }
    add_assessment(record)
    return {"status": "success", **record}


@router.get("/{patient_id}")
def patient_assessments(patient_id: str) -> list[dict]:
    if not patient_id.strip():
        raise HTTPException(status_code=400, detail="patient_id is required")
    return list_assessments(patient_id.strip())
