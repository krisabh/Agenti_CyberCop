# Agentic CyberCop — Scam Detection Honeypot API

An API-first **honeypot system** that engages suspected scammers like a realistic user, extracts actionable fraud intelligence, and reports final results to the GUVI evaluation endpoint.

---

## 1) What this project does

This service exposes a `/honeypot` endpoint that:

1. Authenticates incoming requests via API key.
2. Accepts scam conversation input (legacy format and panel scenario format).
3. Detects scam intent.
4. Generates human-like replies to keep scammers engaged.
5. Extracts intelligence artifacts (UPI IDs, account numbers, links, phone, IFSC, PAN, etc.).
6. Sends final callback payload to GUVI after completion criteria are met.

---

## 2) Current key capabilities

- ✅ API key protected endpoints
- ✅ Scam detection with sticky session behavior
- ✅ In-memory session state tracking (`messages`, `scam_detected`, finalized)
- ✅ Extraction of structured scam indicators
- ✅ Asynchronous GUVI callback dispatch from request flow (non-blocking)
- ✅ Support for both:
  - Existing payload (`sessionId + message.text`)
  - Panel scenario payload (`scenarioId + initialMessage`), including list input

---

## 3) Tech stack

- **FastAPI** / Uvicorn / Gunicorn
- **Google Gemini** for detection + response generation + notes
- **Regex-based intelligence extraction**
- **Requests** for GUVI callback
- Optional RAG modules are present in repo (not required for core submission flow)

---

## 4) Project structure

```text
app/
  main.py               # API routes + orchestration
  detector.py           # Scam detection
  agent.py              # Reply generation persona
  extractor.py          # Structured intel extraction
  agent_notes.py        # One-line scam tactic summary
  memory.py             # Session memory and lifecycle flags
  guvi_callback.py      # Final result callback sender
  rag.py                # Optional retrieval helper
  rag_ingest.py         # Optional ingestion script
knowledge/              # Optional knowledge docs (RAG)
requirements.txt
Procfile
```

---

## 5) Environment variables

Create `.env` in project root.

```env
API_KEY=your_api_key_here
GEMINI_API_KEY=your_gemini_key_here

# Optional runtime tuning
DETECT_TIMEOUT_SECONDS=28
REPLY_TIMEOUT_SECONDS=28

# Optional hybrid-finalization tuning (if enabled in your main.py)
MIN_INTEL_SCORE=7
FALLBACK_MIN_TURNS=17

# Optional RAG controls (only if you use RAG)
USE_RAG=false
CHROMA_PERSIST_DIR=./data/chroma_db
RAG_COLLECTION_NAME=scam_knowledge
RAG_TOP_K=3
RAG_EMBEDDING_MODEL=models/embedding-001
```

---

## 6) Install and run locally

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run API (dev)

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Health check

```bash
curl http://127.0.0.1:8000/
```

Expected:

```json
{"status":"ok"}
```

---

## 7) API contract

### GET `/honeypot`
Checks endpoint reachability (requires `x-api-key`).

---

### POST `/honeypot`

#### Headers

- `x-api-key: <API_KEY>`
- `Content-Type: application/json`

#### A) Legacy request format

```json
{
  "sessionId": "demo-session-1",
  "message": {
    "sender": "scammer",
    "text": "Your account will be blocked. Share OTP now.",
    "timestamp": 1770005528731
  },
  "metadata": {
    "channel": "SMS",
    "language": "English",
    "locale": "IN"
  }
}
```

#### B) Panel scenario format (single object)

```json
{
  "scenarioId": "bank_fraud",
  "initialMessage": "URGENT: Your SBI account has been compromised...",
  "metadata": {
    "channel": "SMS",
    "language": "English",
    "locale": "IN"
  }
}
```

#### C) Panel scenario format (array)

```json
[
  {
    "scenarioId": "bank_fraud",
    "initialMessage": "URGENT: Your SBI account has been compromised...",
    "metadata": {"channel": "SMS", "language": "English", "locale": "IN"}
  },
  {
    "scenarioId": "upi_fraud",
    "initialMessage": "You won cashback. Verify UPI details...",
    "metadata": {"channel": "WhatsApp", "language": "English", "locale": "IN"}
  }
]
```

#### Standard response shape

```json
{
  "status": "success",
  "reply": "<agent reply or empty string>"
}
```

For list payload mode, implementation may return per-scenario `results` depending on current `main.py` behavior.

---

## 8) Extraction fields produced

The pipeline can return these fields internally and in final callback payload:

- `bankAccounts`
- `upiIds`
- `phishingLinks`
- `phoneNumbers`
- `emailAddresses`
- `ifscCodes`
- `panNumbers`
- `suspiciousKeywords`

---

## 9) Performance guidance for panel evaluation

Panel runs multiple scenarios and turns; latency matters heavily.

To keep per-turn response low:

1. Keep callback **non-blocking** (fire-and-forget background call).
2. Use bounded model timeouts.
3. Keep prompts concise.
4. Avoid heavy operations in request path.
5. Reuse network sessions for callback requests.
6. Use optimized finalization criteria (hybrid evidence + fallback turns) where applicable.

---

## 10) Cloud Run notes

- Deploy with Gunicorn/Uvicorn worker (see `Procfile`).
- Ensure `.env`/secrets are configured in Cloud Run variables.
- If disabling a service temporarily, remove public invoker or delete service.

---

## 11) Submission checklist

- [ ] `README.md` present
- [ ] API key auth working
- [ ] `/honeypot` supports panel request format
- [ ] callback payload structure aligned
- [ ] response latency under target
- [ ] deployment URL reachable by evaluator

---

## 12) License / ownership

Add your team/project license policy here (MIT/Apache/Proprietary as applicable).
