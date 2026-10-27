"""Emotion detection with a safe, dependency-light demo fallback.

The production target named in the original README is available behind
``JOG_ENABLE_TRANSFORMER=true``. Keeping the model lazy and opt-in means the
check-in can run immediately on a laptop without downloading a large model.
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

from ..config import ENABLE_TRANSFORMER, EMOTION_MODEL

EMOTIONS = ("joy", "sadness", "anger", "fear", "surprise", "disgust", "neutral")

# A small transparent baseline for the first runnable product slice. The
# transformer path can replace it when model dependencies and weights exist.
LEXICON = {
    "joy": {"happy", "joy", "joyful", "good", "hopeful", "excited", "grateful", "great", "love", "relieved", "proud"},
    "sadness": {"sad", "down", "lonely", "tired", "cry", "crying", "empty", "hopeless", "unhappy", "low", "blue"},
    "anger": {"angry", "mad", "frustrated", "irritated", "annoyed", "upset", "furious", "resentful"},
    "fear": {"afraid", "scared", "fear", "worried", "worry", "anxious", "panic", "nervous", "unsafe", "overwhelmed"},
    "surprise": {"surprised", "shocked", "unexpected", "suddenly", "wow"},
    "disgust": {"disgusted", "dislike", "gross", "awful", "revolting"},
}

EMOTION_ALIASES = {
    "happy": "joy", "positive": "joy", "good": "joy",
    "sad": "sadness", "low": "sadness",
    "anxious": "fear", "anxiety": "fear", "stressed": "fear",
    "angry": "anger", "frustrated": "anger",
    "okay": "neutral", "fine": "neutral", "calm": "neutral",
}


def _number(responses: dict[str, Any], *keys: str, default: float = 3.0) -> float:
    for key in keys:
        if key in responses:
            try:
                return max(1.0, min(5.0, float(responses[key])))
            except (TypeError, ValueError):
                pass
    return default


def _transformer_scores(text: str) -> dict[str, float] | None:
    if not ENABLE_TRANSFORMER or not text.strip():
        return None
    try:
        from transformers import pipeline  # type: ignore

        classifier = pipeline("text-classification", model=EMOTION_MODEL, top_k=None)
        raw = classifier(text[:2000])
        rows = raw[0] if raw and isinstance(raw[0], list) else raw
        scores = defaultdict(float)
        for row in rows:
            label = EMOTION_ALIASES.get(str(row.get("label", "")).lower(), str(row.get("label", "")).lower())
            if label in EMOTIONS:
                scores[label] += float(row.get("score", 0))
        if scores:
            return _normalize(dict(scores))
    except Exception:
        # Model download, import, or provider failures must not break the check-in.
        return None
    return None


def _normalize(scores: dict[str, float]) -> dict[str, float]:
    total = sum(max(0.0, value) for value in scores.values()) or 1.0
    return {emotion: round(max(0.0, scores.get(emotion, 0.0)) / total, 4) for emotion in EMOTIONS}


def analyze(responses: dict[str, Any], text: str) -> dict[str, Any]:
    clean_text = (text or "").strip().lower()
    transformer_scores = _transformer_scores(clean_text)
    source = "huggingface-transformer" if transformer_scores else "transparent-demo-baseline"

    if transformer_scores:
        scores = transformer_scores
    else:
        scores = {emotion: 0.03 for emotion in EMOTIONS}
        tokens = set(re.findall(r"[a-z']+", clean_text))
        for emotion, words in LEXICON.items():
            hits = len(tokens.intersection(words))
            scores[emotion] += hits * 0.22

        self_report = str(responses.get("self_reported_feeling", "neutral")).lower()
        self_report = EMOTION_ALIASES.get(self_report, self_report)
        if self_report in EMOTIONS:
            scores[self_report] += 0.42

        sleep = _number(responses, "sleep_pattern", "Sleep Pattern", "sleep", default=3)
        energy = _number(responses, "energy_level", "Energy Level", "Energy Levels", "energy", default=3)
        stress = _number(responses, "stress_level", "Stress Level", "stress", default=3)
        scores["sadness"] += max(0, 3 - sleep) * 0.10 + max(0, 3 - energy) * 0.08
        scores["fear"] += max(0, stress - 3) * 0.12
        scores["joy"] += max(0, energy - 3) * 0.08 + max(0, sleep - 3) * 0.05
        scores["neutral"] += 0.24
        scores = _normalize(scores)

    primary = max(scores, key=scores.get)
    confidence = round(min(0.99, max(0.45, scores[primary] + 0.35)), 2)
    sleep = _number(responses, "sleep_pattern", "Sleep Pattern", "sleep", default=3)
    energy = _number(responses, "energy_level", "Energy Level", "Energy Levels", "energy", default=3)
    stress = _number(responses, "stress_level", "Stress Level", "stress", default=3)
    negative = scores.get("sadness", 0) + scores.get("fear", 0) + scores.get("anger", 0)
    high_risk_words = ("hurt myself", "harm myself", "suicide", "kill myself", "not safe", "end my life")
    if any(phrase in clean_text for phrase in high_risk_words) or stress >= 5 or negative >= 0.78:
        risk = "High"
    elif stress >= 4 or sleep <= 2 or energy <= 2 or negative >= 0.48:
        risk = "Medium"
    else:
        risk = "Low"

    mood = "Positive" if scores["joy"] >= 0.34 else "Negative" if negative >= 0.42 else "Neutral"
    return {
        "dominant_mood": mood,
        "primary_emotion": primary,
        "emotion_confidence": confidence,
        "emotion_scores": scores,
        "risk_level": risk,
        "detection_source": source,
    }
