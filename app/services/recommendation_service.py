"""Turn an emotion estimate into a gentle, non-diagnostic next step."""

from __future__ import annotations


def make_recommendation(emotion: str, risk_level: str) -> dict[str, str | None]:
    key = emotion.lower()
    risk = risk_level.lower()
    choices = {
        "joy": (
            "Maintain healthy habits",
            "It sounds like you have some positive energy today. Notice what is helping and carry one small part of it into the rest of your day.",
            "cheerful",
        ),
        "surprise": (
            "Pause and orient yourself",
            "A surprising moment can take time to settle. Take a slow breath, name what you know, and choose one manageable next step.",
            "calm",
        ),
        "sadness": (
            "Reach for gentle support",
            "Keep today small and kind: drink some water, take a short pause, and consider telling a trusted person how you are feeling.",
            "supportive",
        ),
        "fear": (
            "Create a calm next step",
            "Try a slow exhale and focus on one thing you can control right now. If worry keeps getting in the way, reaching out for support may help.",
            "calm",
        ),
        "anger": (
            "Give yourself a pause",
            "Before responding to a difficult moment, step away for a minute, loosen your shoulders, and return when you feel more settled.",
            "calm",
        ),
        "disgust": (
            "Reset your surroundings",
            "A brief change of space, fresh air, or a glass of water can help you reset. Choose a simple action that makes the next few minutes easier.",
            "supportive",
        ),
        "neutral": (
            "Maintain healthy habits",
            "Your check-in looks fairly steady. Keep a regular routine, notice your energy, and make room for a small restorative break.",
            "supportive",
        ),
    }
    action, text, tone = choices.get(key, choices["neutral"])
    safety_note = None
    if risk == "high":
        action = "Connect with your care team"
        text = "Your answers suggest that extra support could be useful today. Consider contacting a trusted person or healthcare professional and sharing how you are feeling."
        tone = "calm"
        safety_note = "If you may be in immediate danger or might hurt yourself or someone else, contact local emergency services or a crisis service now."
    elif risk == "medium":
        safety_note = "This is only a screening estimate. If these feelings persist or interfere with daily life, consider talking with a qualified professional."
    return {
        "recommended_action": action,
        "recommendation": text,
        "voice_tone": tone,
        "voice_script": f"{action}. {text}",
        "safety_note": safety_note,
    }
