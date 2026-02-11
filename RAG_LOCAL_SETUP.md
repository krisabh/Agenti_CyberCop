# RAG + Vector Database Local Setup (Kid-Friendly)

Think of this as giving your bot a **small library**.

- **RAG** = the bot can read from that library before replying.
- **Vector DB** = smart bookshelf that finds the most relevant pages quickly.

This guide is copy-paste friendly.

---

## 1) Install dependencies

Open terminal in project root and run:

```bash
pip install -r requirements.txt
```

What this does:

- installs FastAPI app packages
- installs LangChain + Chroma packages for RAG

---

## 2) Create or update `.env`

Add these lines:

```env
API_KEY=your_api_key_here
GEMINI_API_KEY=your_gemini_key_here

# RAG switch
USE_RAG=true

# vector DB settings
CHROMA_PERSIST_DIR=./data/chroma_db
RAG_COLLECTION_NAME=scam_knowledge
RAG_TOP_K=3
RAG_EMBEDDING_MODEL=models/text-embedding-004

# ingestion settings
RAG_KNOWLEDGE_DIR=./knowledge
RAG_CHUNK_SIZE=700
RAG_CHUNK_OVERLAP=120
```

Important:

- `USE_RAG=true` = turn ON RAG.
- If `USE_RAG=false`, app behaves like before (no retrieval context).

---

## 3) Add knowledge files (your library)

Folder structure:

```text
knowledge/
  scam_playbooks/
    upi_collect_scam.md
  response_strategies/
    human_like_probing.md
  policy/
    ethical_guardrails.md
```

You can add more `.md` or `.txt` files later.

---

## 4) Ingest knowledge into vector DB

Run this one-time command after creating/updating knowledge files:

```bash
python -m app.rag_ingest
```

What happens:

1. reads all `.md` / `.txt` files from `knowledge/`
2. splits long text into chunks
3. creates embeddings
4. stores vectors in Chroma at `./data/chroma_db`

---

## 5) Start your API

```bash
uvicorn app.main:app --reload
```

Health check:

```bash
curl http://127.0.0.1:8000/
```

Expected:

```json
{ "status": "ok" }
```

---

## 6) Test honeypot endpoint

```bash
curl -X POST "http://127.0.0.1:8000/honeypot" \
  -H "x-api-key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "demo-session-1",
    "message": {
      "sender": "scammer",
      "text": "Your account will be blocked today. Share your UPI ID now.",
      "timestamp": 1770005528731
    },
    "conversationHistory": [],
    "metadata": {
      "channel": "SMS",
      "language": "English",
      "locale": "IN"
    }
  }'
```

---

## 7) How to add more knowledge later

1. Put new `.md`/`.txt` files inside `knowledge/` folders.
2. Re-run ingestion:

```bash
python -m app.rag_ingest
```

That’s it. Your vector DB is updated.

---

## 8) New files and purpose

- `app/rag.py` → retrieves relevant knowledge for current message.
- `app/rag_ingest.py` → loads knowledge files into Chroma DB.
- `knowledge/...` → starter knowledge files.

---

## 9) Quick troubleshooting

### Problem: `ModuleNotFoundError` for langchain/chroma

Run:

```bash
pip install -r requirements.txt
```

### Problem: No context being retrieved

Check:

- `USE_RAG=true` in `.env`
- You ran `python -m app.rag_ingest`
- `knowledge/` has `.md` or `.txt` files

### Problem: API key error

Use same value in:

- `.env` -> `API_KEY`
- request header -> `x-api-key`

---

## 10) See exactly what changed (diff)

```bash
git diff -- app/main.py app/agent.py app/memory.py app/detector.py requirements.txt app/rag.py app/rag_ingest.py knowledge/
```

RAG_LOCAL_SETUP.md
