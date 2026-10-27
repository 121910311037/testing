"""Voice profile setup, sample upload, and test endpoints."""

from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from ..schemas import VoiceProfileResponse, VoiceTestResponse
from ..services.storage import (
    add_voice_profile,
    get_voice_profile,
    list_voice_profiles,
    new_id,
    safe_profile_file,
    update_voice_profile,
    utc_now,
)
from ..services.voice_service import ALLOWED_EXTENSIONS, sample_url, save_sample, try_xtts

router = APIRouter(prefix="/api/voice-profiles", tags=["voice profiles"])


def _notice(profile: dict) -> str:
    if profile.get("provider") == "coqui-xtts":
        return "XTTS is enabled. This profile can generate a cloned-voice preview."
    return "Profile saved. This demo can replay your reference sample; enable Coqui XTTS for a true cloned reading."


def _view(profile: dict) -> dict:
    filenames = profile.get("sample_files", [])
    first_sample = sample_url(profile["id"], filenames[0]) if filenames else None
    return {
        "id": profile["id"],
        "patient_id": profile["patient_id"],
        "profile_name": profile["profile_name"],
        "speaker_name": profile["speaker_name"],
        "language": profile["language"],
        "consent_status": profile["consent_status"],
        "sample_count": len(filenames),
        "is_ready": bool(filenames) and profile.get("consent_status") == "granted",
        "provider": profile.get("provider", "sample-playback-demo"),
        "test_notice": _notice(profile),
        "created_at": profile["created_at"],
        "sample_url": first_sample,
    }


@router.get("/", response_model=list[VoiceProfileResponse])
def get_profiles(patient_id: str | None = None) -> list[dict]:
    return [_view(profile) for profile in list_voice_profiles(patient_id)]


@router.post("/", response_model=VoiceProfileResponse)
def create_profile(
    patient_id: str = Form(...),
    profile_name: str = Form(...),
    speaker_name: str = Form(...),
    language: str = Form("en"),
    consent_confirmed: bool = Form(...),
) -> dict:
    if not consent_confirmed:
        raise HTTPException(status_code=400, detail="Permission is required before creating a voice profile.")
    if not patient_id.strip() or not profile_name.strip():
        raise HTTPException(status_code=400, detail="patient_id and profile_name are required.")
    profile = {
        "id": new_id("voice"),
        "patient_id": patient_id.strip(),
        "profile_name": profile_name.strip()[:80],
        "speaker_name": speaker_name.strip()[:80] or "My voice",
        "language": language.strip()[:12] or "en",
        "consent_status": "granted",
        "sample_files": [],
        "provider": "sample-playback-demo",
        "created_at": utc_now(),
    }
    return _view(add_voice_profile(profile))


@router.post("/{profile_id}/samples", response_model=VoiceProfileResponse)
async def upload_sample(profile_id: str, file: UploadFile = File(...)) -> dict:
    profile = get_voice_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Voice profile not found")
    if profile.get("consent_status") != "granted":
        raise HTTPException(status_code=400, detail="Permission must be granted before uploading a sample.")
    try:
        content = await file.read()
        saved = save_sample(profile_id, file.filename or "voice-sample.webm", content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    filename = saved["path"].name
    sample_files = [*profile.get("sample_files", []), filename]
    updated = update_voice_profile(profile_id, {"sample_files": sample_files})
    return _view(updated or profile)


@router.get("/{profile_id}/samples/{filename}")
def get_sample(profile_id: str, filename: str):
    profile = get_voice_profile(profile_id)
    if not profile or filename not in profile.get("sample_files", []):
        raise HTTPException(status_code=404, detail="Voice sample not found")
    path = safe_profile_file(profile_id, filename)
    if not path or not path.exists() or path.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=404, detail="Voice sample not found")
    return FileResponse(path)


@router.post("/{profile_id}/test", response_model=VoiceTestResponse)
def test_profile(
    profile_id: str,
    text: str = Form(...),
    tone: str = Form("supportive"),
) -> dict:
    profile = get_voice_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Voice profile not found")
    if profile.get("consent_status") != "granted":
        raise HTTPException(status_code=400, detail="Permission for this voice profile is not active.")
    if not text.strip():
        raise HTTPException(status_code=400, detail="Please provide text for the voice test.")
    filenames = profile.get("sample_files", [])
    if not filenames:
        raise HTTPException(status_code=400, detail="Upload or record a voice sample before testing the profile.")
    generated = try_xtts(profile, text.strip()[:2000], tone)
    if generated:
        # The provider is recorded in the response rather than mutating the profile,
        # so the user can see what happened for each individual test.
        return {
            "profile_id": profile_id,
            "provider": "coqui-xtts",
            "cloned": True,
            "tone": tone,
            "audio_url": f"/api/audio/{generated.name}",
            "notice": "This is a generated preview using the authorized voice sample.",
        }
    playback_url = sample_url(profile_id, filenames[0])
    return {
        "profile_id": profile_id,
        "provider": "sample-playback-demo",
        "cloned": False,
        "tone": tone,
        "audio_url": playback_url,
        "notice": "This demo is replaying the saved reference sample. The browser button below can read the text, but it is not a cloned voice. Enable JOG_ENABLE_XTTS=true with Coqui TTS for true cloned speech.",
    }
