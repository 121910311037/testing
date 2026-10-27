from __future__ import annotations

from app.services.emotion_service import analyze
from app.services.recommendation_service import make_recommendation
from app.services.voice_service import save_sample


def test_emotion_check_in_detects_anxiety_and_medium_or_high_support_need():
    result = analyze(
        {"sleep_pattern": 2, "energy_level": 2, "stress_level": 4, "self_reported_feeling": "fear"},
        "I feel worried and overwhelmed today.",
    )
    assert result["primary_emotion"] == "fear"
    assert result["risk_level"] in {"Medium", "High"}
    assert result["emotion_scores"]["fear"] > 0


def test_high_risk_recommendation_is_supportive_and_non_diagnostic():
    result = make_recommendation("fear", "High")
    assert result["recommended_action"] == "Connect with your care team"
    assert result["safety_note"]
    assert "diagnos" not in result["recommendation"].lower()


def test_voice_sample_is_safely_named_and_saved(tmp_path, monkeypatch):
    import app.services.voice_service as voice_service

    monkeypatch.setattr(voice_service, "profile_dir", lambda profile_id: tmp_path / profile_id)
    saved = save_sample("voice_test", "../../my voice.webm", b"audio-bytes")
    assert saved["path"].parent == tmp_path / "voice_test"
    assert saved["path"].suffix == ".webm"
    assert ".." not in saved["path"].name
