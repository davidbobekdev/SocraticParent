# Technical Specification

## 1. Backend: Python/FastAPI
- **Endpoints:**
  - `POST /analyze`: Receives Base64 image + Metadata (Grade).
  - `GET /health`: Basic system check.
- **Processing Logic:**
  - Compress image for API cost/speed.
  - Call Google Gemini 2.0/3.0 Flash API with high `top_p` for diverse, creative questioning.
- **Security:** Use `.env` for `GEMINI_API_KEY`. No local storage of images (Privacy-first).

## 2. Frontend: Vanilla Web Stack
- **Stack:** HTML5, Tailwind CSS, JavaScript.
- **Key Features:**
  - Drag-and-drop file upload.
  - Camera API integration (Native mobile feel).
  - "Typing..." state to manage AI latency expectations.
  - Result rendering using a "Card" layout.

## 3. Data Schema (Internal JSON)
```json
{
  "subject": "String",
  "questions": {
    "foundation": "String",
    "bridge": "String",
    "mastery": "String"
  },
  "behavioral_tip": "String"
}