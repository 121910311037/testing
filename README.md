
# 🧠 JOG AI – Guided Mood Check-in + Voice Profile

## Current guided experience

The repository now has a runnable browser flow that uses the two capabilities as separate but connected steps:

```text
emotion questions → emotion estimate → personalized recommendation
                                      ↓
                         consent + voice sample
                                      ↓
                             voice profile test
```

Start it from the repository root:

```bash
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Then open `http://localhost:8000`. The same FastAPI app serves the frontend and API. Detailed behavior and optional true voice cloning are documented in [`docs/GUIDED_CHECKIN.md`](docs/GUIDED_CHECKIN.md).

The default demo is transparent: it runs a lightweight emotion baseline, stores an explicitly consented voice sample, replays that sample as a profile check, and offers browser speech for the test text. Coqui XTTS can be enabled separately for a true cloned-speech preview; the app never labels a sample replay as cloning.

## Overview

It is a proof-of-concept AI-powered Mood Analysis and Emotion Detection system developed for the JOG Medication Reminder Application.

The system analyzes patient questionnaire responses together with free-text input to determine:

- Mood Analysis
- Emotion Detection
- Risk Assessment
- Personalized Recommendations

The application consists of a FastAPI backend and an HTML/CSS/JavaScript frontend.

---

# Features

## Mood Analysis

Analyzes questionnaire responses including:

- Sleep Pattern
- Energy Level
- Stress Level

Generates:

- Positive Score
- Neutral Score
- Negative Score
- Dominant Mood
- Risk Level

---

## Emotion Detection

Uses Hugging Face Transformer model:

```
michellejieli/emotion_text_classifier
```

Detects:

- Joy
- Sadness
- Anger
- Fear
- Surprise
- Disgust
- Neutral

Returns:

- Primary Emotion
- Emotion Confidence
- Complete Emotion Scores

---

## Recommendation System

Based on

- Mood
- Risk Level
- Primary Emotion

Generates personalized wellness recommendations.

Example:

- Maintain Healthy Habits
- Monitor Closely
- Immediate Follow-up

---

## Patient History

Stores every assessment in JSON format.

Example:

```
patient_data/
    12345.json
```

Allows viewing:

- Complete History
- Latest Assessment
- Assessment Summary

---

## Dashboard

Displays:

- Total Patients
- Total Assessments
- High Risk Patients
- Mood Distribution
- Recent Assessments

---

## Report Generation

Supports exporting

- Excel (.xlsx)
- PDF (.pdf)

for each patient.

---

# Project Structure

```

Emotion Detection api/

│
├── app/
│
├── api/
│ ├── assessments.py
│ ├── dashboard.py
│ ├── history.py
│ └── reports.py
│
├── services/
│ ├── emotion_service.py
│ ├── questionnaire_service.py
│ ├── recommendation_service.py
│ ├── report_service.py
│ └── history_service.py
│
├── models/
├── config.py
├── main.py
│
├── patient_data/
├── reports/
│
├── frontend/
│ ├── index.html
│ ├── assessment.html
│ ├── history.html
│ ├── reports.html
│ │
│ ├── css/
│ │ └── style.css
│ │
│ └── js/
│ ├── app.js
│ ├── dashboard.js
│ ├── history.js
│ └── reports.js
│
├── requirements.txt
└── README.md

````

---

# Technologies Used

## Backend

* Python
* FastAPI
* Uvicorn
* Hugging Face Transformers
* PyTorch
* Pydantic

---

## Frontend

* HTML5
* CSS3
* Bootstrap 5
* JavaScript

---

## Reports

* OpenPyXL
* ReportLab

---

# AI Model

Emotion Detection Model

```
michellejieli/emotion_text_classifier
```

Source:

Hugging Face Transformers

---

# Installation

## Clone the project

```bash

cd Emotion Detection api
```

---

## Create Virtual Environment

Windows

```bash
python -m venv .venv
```

Activate

```bash
.venv\Scripts\activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Running the Backend

Open Terminal 1

```bash
cd "Emotion Detection api"

.venv\Scripts\activate

python -m uvicorn app.main:app --reload
```

Backend URL

```
http://127.0.0.1:8000
```

Swagger Documentation

```
http://127.0.0.1:8000/docs
```

---

# Running the Frontend

Open Terminal 2

```bash
cd frontend

python -m http.server 5500
```

Open browser

```
http://localhost:5500
```

---

# API Endpoints

## Root

```
GET /
```

---

## Health

```
GET /health
```

---

## Mood Assessment

```
POST /api/assessments/
```

Request

```json
{
    "patient_id":"12345",
    "responses":{
        "Sleep Pattern":1,
        "Energy Levels":3,
        "Stress Level":2
    },
    "text":"I feel tired but hopeful today."
}
```

---

## Patient History

```
GET /api/history/{patient_id}
```

---

## Latest Assessment

```
GET /api/history/{patient_id}/latest
```

---

## History Summary

```
GET /api/history/{patient_id}/summary
```

---

## Dashboard

```
GET /api/dashboard/
```

---

## Excel Report

```
GET /api/reports/excel/{patient_id}
```

---

## PDF Report

```
GET /api/reports/pdf/{patient_id}
```

---

# Workflow

```
User

↓

Frontend

↓

FastAPI Backend

↓

Mood Analysis

↓

Emotion Detection

↓

Risk Assessment

↓

Recommendation Engine

↓

Patient History

↓

Dashboard / Reports
```

---

# Sample Output

```json
{
    "status":"success",

    "dominant_mood":"Neutral",

    "risk_level":"Low",

    "primary_emotion":"Neutral",

    "emotion_confidence":0.81,

    "recommendation":{

        "recommended_action":"Maintain Healthy Habits",

        "recommendation":"Your emotional wellbeing appears stable."
    }

}
```

---


