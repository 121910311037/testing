"""Pydantic request/response contracts for the public API."""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class AssessmentRequest(BaseModel):
    patient_id: str = Field(default="demo-user", min_length=1, max_length=100)
    responses: dict[str, Any] = Field(default_factory=dict)
    text: str = Field(default="", max_length=2000)


class Recommendation(BaseModel):
    recommended_action: str
    recommendation: str
    voice_tone: str
    voice_script: str
    safety_note: str | None = None


class AssessmentResponse(BaseModel):
    status: str = "success"
    assessment_id: str
    patient_id: str
    dominant_mood: str
    risk_level: str
    primary_emotion: str
    emotion_confidence: float
    emotion_scores: dict[str, float]
    recommendation: Recommendation
    detection_source: str
    recorded_at: str


class VoiceProfileResponse(BaseModel):
    id: str
    patient_id: str
    profile_name: str
    speaker_name: str
    language: str
    consent_status: str
    sample_count: int
    is_ready: bool
    provider: str
    test_notice: str
    created_at: str
    sample_url: str | None = None


class VoiceTestResponse(BaseModel):
    profile_id: str
    provider: str
    cloned: bool
    tone: str
    audio_url: str | None = None
    notice: str
