# JOG guided emotion check-in and voice profile

This slice connects the two capabilities as a clear four-step user journey:

```text
Emotion questions → emotion estimate → personalized recommendation
                                      ↓
                        consent + recorded voice sample
                                      ↓
                             voice profile test
```

## Start it

From the repository root:

```bash
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000`. The browser UI is served by the same FastAPI app, so it uses relative API URLs and does not depend on a separate localhost frontend.

## The four screens

1. **Check in** — sleep, energy, stress, a self-reported feeling, and optional free text.
2. **Recommendation** — primary emotion, confidence, risk flag, emotion scores, and a supportive next step.
3. **Voice profile** — profile name, explicit permission checkbox, browser recording or audio upload.
4. **Test** — test text and tone, saved sample playback, and a browser speech fallback.

The API stores demo records in `data/assessments.json`, `data/voice_profiles.json`, and `data/voice_profiles/`. These paths are ignored by Git because they can contain sensitive text and voice data.

## Real voice cloning

The default demo deliberately does **not** pretend that playing a sample is voice cloning. Without an installed voice model it:

- saves the consented sample;
- plays the saved reference sample back as a profile check; and
- offers the browser's speech synthesis for reading the test text.

For an actual cloned reading, install the optional Coqui TTS dependency and enable it explicitly:

```bash
python -m pip install -r requirements-voice-cloning.txt
# PowerShell: $env:JOG_ENABLE_XTTS="true"
# macOS/Linux: export JOG_ENABLE_XTTS=true
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The first XTTS test may download a large model. Use only an authorized voice sample and follow the model/provider license. The implementation uses a lazy import so normal check-ins do not load XTTS.

## Emotion detection mode

The default `transparent-demo-baseline` is intentionally lightweight and makes its source visible in the recommendation screen. To opt into the model named in the original README, set `JOG_ENABLE_TRANSFORMER=true` after installing the existing Transformers/Torch requirements. If the model cannot load, the app safely falls back to the baseline.

Emotion results are screening estimates, not medical diagnoses. The high-risk message asks the user to connect with a trusted professional or emergency support when appropriate.
