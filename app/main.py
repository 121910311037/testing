"""FastAPI entry point for the JOG guided check-in demo."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .api.assessments import router as assessments_router
from .api.voice_profiles import router as voice_profiles_router
from .config import APP_NAME, AUDIO_DIR, FRONTEND_DIR

app = FastAPI(
    title=APP_NAME,
    description="Emotion check-in → recommendation → consent-aware voice profile test",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(assessments_router)
app.include_router(voice_profiles_router)
# Serve the CSS and JavaScript folders beneath one same-origin static path.
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "app": APP_NAME}


@app.get("/api/audio/{filename}")
def generated_audio(filename: str):
    # Only files directly inside the generated-audio directory are public.
    base = AUDIO_DIR.resolve()
    candidate = (base / filename).resolve()
    try:
        candidate.relative_to(base)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Audio not found") from exc
    if not candidate.exists() or not candidate.is_file():
        raise HTTPException(status_code=404, detail="Audio not found")
    return FileResponse(candidate)
