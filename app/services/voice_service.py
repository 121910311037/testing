"""Consent-aware voice sample handling and optional XTTS integration."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any
from uuid import uuid4

from ..config import AUDIO_DIR, ENABLE_XTTS, MAX_SAMPLE_BYTES, XTTS_MODEL
from .storage import profile_dir, safe_profile_file

ALLOWED_EXTENSIONS = {".wav", ".mp3", ".m4a", ".mp4", ".ogg", ".webm", ".flac"}


def _safe_name(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "-", value or "sample").strip("-")
    return cleaned[:70] or "sample"


def save_sample(profile_id: str, filename: str, content: bytes) -> dict[str, Any]:
    suffix = Path(filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError("Please upload WAV, MP3, M4A, OGG, WebM, or FLAC audio.")
    if not content:
        raise ValueError("The audio sample is empty.")
    if len(content) > MAX_SAMPLE_BYTES:
        raise ValueError(f"The audio sample must be smaller than {MAX_SAMPLE_BYTES // (1024 * 1024)} MB.")
    target_dir = profile_dir(profile_id)
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{_safe_name(Path(filename).stem)}-{uuid4().hex[:8]}{suffix}"
    target.write_bytes(content)
    return {"filename": target.name, "size_bytes": len(content), "path": target}


def sample_url(profile_id: str, filename: str) -> str:
    return f"/api/voice-profiles/{profile_id}/samples/{filename}"


def _wav_reference(profile_id: str, filenames: list[str]) -> list[str]:
    """Return usable reference files, converting one sample with ffmpeg if present."""
    references: list[str] = []
    for filename in filenames:
        path = safe_profile_file(profile_id, filename)
        if not path or not path.exists():
            continue
        if path.suffix.lower() == ".wav":
            references.append(path.as_posix())
            continue
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            continue
        converted = profile_dir(profile_id) / f"reference-{_safe_name(path.stem)}.wav"
        try:
            result = subprocess.run(
                [ffmpeg, "-y", "-i", path.as_posix(), "-vn", "-ac", "1", "-ar", "16000", converted.as_posix()],
                capture_output=True,
                timeout=45,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        if result.returncode == 0 and converted.exists():
            references.append(converted.as_posix())
    return references


def try_xtts(profile: dict[str, Any], text: str, tone: str) -> Path | None:
    """Generate with Coqui XTTS only when explicitly enabled.

    The import is lazy because XTTS is large and is not required for the
    runnable demo. It is deliberately opt-in so a user is never surprised by
    a multi-gigabyte model download.
    """
    if not ENABLE_XTTS or not profile.get("sample_files"):
        return None
    references = _wav_reference(profile["id"], profile["sample_files"])
    if not references:
        return None
    try:
        from TTS.api import TTS  # type: ignore

        output = AUDIO_DIR / f"{profile['id']}-{_safe_name(tone)}-{uuid4().hex[:8]}.wav"
        tts = TTS(XTTS_MODEL, progress_bar=False)
        tts.tts_to_file(
            text=text,
            speaker_wav=references,
            language=profile.get("language", "en"),
            file_path=output.as_posix(),
        )
        return output if output.exists() else None
    except Exception:
        return None
