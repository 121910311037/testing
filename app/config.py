"""Small, environment-driven configuration for the JOG demo."""

from pathlib import Path
import os


ROOT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = ROOT_DIR / "frontend"
DATA_DIR = Path(os.getenv("JOG_DATA_DIR", str(ROOT_DIR / "data"))).resolve()
ASSESSMENTS_FILE = DATA_DIR / "assessments.json"
VOICE_PROFILES_FILE = DATA_DIR / "voice_profiles.json"
VOICE_DIR = DATA_DIR / "voice_profiles"
AUDIO_DIR = DATA_DIR / "audio"

for directory in (DATA_DIR, VOICE_DIR, AUDIO_DIR):
    directory.mkdir(parents=True, exist_ok=True)

APP_NAME = os.getenv("JOG_APP_NAME", "JOG Care Check-in")
ENABLE_TRANSFORMER = os.getenv("JOG_ENABLE_TRANSFORMER", "false").lower() in {"1", "true", "yes"}
EMOTION_MODEL = os.getenv("JOG_EMOTION_MODEL", "michellejieli/emotion_text_classifier")
ENABLE_XTTS = os.getenv("JOG_ENABLE_XTTS", "false").lower() in {"1", "true", "yes"}
XTTS_MODEL = os.getenv("JOG_XTTS_MODEL", "tts_models/multilingual/multi-dataset/xtts_v2")
MAX_SAMPLE_BYTES = int(os.getenv("JOG_MAX_SAMPLE_BYTES", str(25 * 1024 * 1024)))
