"""Tiny JSON storage used by the proof-of-concept.

The storage boundary keeps the first demo easy to run without a database. It is
intentionally replaceable before production use; do not put real patient data
or unconsented voice recordings in this demo workspace.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any
from uuid import uuid4

from ..config import ASSESSMENTS_FILE, DATA_DIR, VOICE_PROFILES_FILE, VOICE_DIR

_LOCK = Lock()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


def _read(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def _write(path: Path, records: list[dict[str, Any]]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)


def add_assessment(record: dict[str, Any]) -> dict[str, Any]:
    with _LOCK:
        records = _read(ASSESSMENTS_FILE)
        records.append(record)
        _write(ASSESSMENTS_FILE, records)
    return record


def list_assessments(patient_id: str | None = None) -> list[dict[str, Any]]:
    records = _read(ASSESSMENTS_FILE)
    if patient_id is None:
        return records
    return [record for record in records if record.get("patient_id") == patient_id]


def add_voice_profile(record: dict[str, Any]) -> dict[str, Any]:
    with _LOCK:
        records = _read(VOICE_PROFILES_FILE)
        records.append(record)
        _write(VOICE_PROFILES_FILE, records)
    return record


def get_voice_profile(profile_id: str) -> dict[str, Any] | None:
    return next((item for item in _read(VOICE_PROFILES_FILE) if item.get("id") == profile_id), None)


def update_voice_profile(profile_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    with _LOCK:
        records = _read(VOICE_PROFILES_FILE)
        for record in records:
            if record.get("id") == profile_id:
                record.update(updates)
                _write(VOICE_PROFILES_FILE, records)
                return record
    return None


def list_voice_profiles(patient_id: str | None = None) -> list[dict[str, Any]]:
    records = _read(VOICE_PROFILES_FILE)
    if patient_id is None:
        return records
    return [record for record in records if record.get("patient_id") == patient_id]


def profile_dir(profile_id: str) -> Path:
    path = VOICE_DIR / profile_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_profile_file(profile_id: str, filename: str) -> Path | None:
    """Resolve a sample only if it remains inside its profile directory."""
    base = profile_dir(profile_id).resolve()
    candidate = (base / filename).resolve()
    try:
        candidate.relative_to(base)
    except ValueError:
        return None
    return candidate
