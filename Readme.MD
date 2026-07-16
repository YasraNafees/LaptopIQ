# LaptopIQ — AI-Powered Laptop Sales Assistant

An intelligent sales assistant built on RAG (Retrieval-Augmented Generation).
Answers customer questions strictly from your uploaded laptop inventory —
no hallucinations, no invented specs or prices.

---

## Project Structure

```
LAPTOPIQ/
├── api.py                      # FastAPI backend — all endpoints
├── config.py                   # Central config (paths, keys, settings)
├── creating_vectordatabase.py  # SHA256-gated index build/load
├── data_ingestion.py           # CSV cleaning + Document creation
├── Reterival_engine.py         # Hybrid retriever (Vector + BM25 + Rerank)
├── file.py                     # CSV upload handling
├── logger.py                   # Centralized backend logging
├── testing.py                  # Manual pipeline tests
├── upload_metadata.json        # Auto-generated — tracks last upload info
├── app.log                     # Auto-generated — runtime logs
├── .env                        # Your API keys — NEVER commit this
├── Data/                       # Your laptop CSV files go here
├── Data_cleaning/              # Intermediate cleaning scripts
├── chroma_db/                  # Auto-generated vector store
├── venv/                       # Python virtual environment
└── ui_app/                     # React + Vite frontend
    ├── src/
    │   └── utils/
    │       └── logger.js       # Frontend console logger (see below)
    ├── public/
    ├── index.html
    ├── vite.config.js
    └── package.json
```

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Backend | FastAPI | REST API for chat + admin |
| RAG Framework | LlamaIndex | Indexing, retrieval, chat engine |
| Vector Database | ChromaDB | Local persistent vector storage |
| Embeddings | OpenAI `text-embedding-3-small` | **Paid API** — cost per embedding call |
| LLM | OpenRouter (`google/gemini-2.5-flash-lite`) | Response generation |
| Hybrid Retrieval | BM25 + Vector Fusion | Keyword + semantic search |
| Reranking | Cohere Rerank v3.5 | Filters top chunks before LLM |
| Frontend | React + Vite | Chat UI + Admin panel |
| Evaluation | RAGAS | Offline hallucination testing |

> **Correction from earlier draft:** this project does **not** use a local/free
> embedding model. `text-embedding-3-small` is an OpenAI API call and is billed
> per token. It is cheap (~$0.02 / 1M tokens as of writing) but **not free** —
> don't advertise it as zero-cost. If you want a genuinely local/free
> alternative, swap in something like `BGE-small-en-v1.5` via
> `sentence-transformers`.

> ✅ **Verified:** `creating_vectordatabase.py` routes `OpenAIEmbedding`
> through OpenRouter (`api_key=Config.OPENROUTER_API_KEY`,
> `api_base=Config.OPENROUTER_API_URL`) — no separate `OPENAI_API_KEY` is
> needed. OpenRouter does support an OpenAI-compatible `/embeddings`
> endpoint, so this setup is structurally correct.
>
> ⚠️ **Actual bug to fix:** OpenRouter requires provider-prefixed model IDs.
> `config.py` currently has:
> ```python
> EMBEDDING_MODEL = "text-embedding-3-small"
> ```
> This is missing the `openai/` prefix and may return a 404 / "model not
> found" when the embedding call hits OpenRouter. It should be:
> ```python
> EMBEDDING_MODEL = "openai/text-embedding-3-small"
> ```
> Test this before relying on the build pipeline — unverified as of this
> writing.

---

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/yourusername/laptopiq.git
cd laptopiq
```

### 2. Create virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 4. Create your .env file
```
OPENROUTER_API_KEY=your_key_here
OPENROUTER_API_BASE_URL=your_base_url_here
COHERE_API_KEY=your_key_here
LAPTOP_CSV_PATH=./Data/your_file.csv
```

### 5. Install frontend dependencies
```bash
cd ui_app
npm install
```

---

## Running the App

### Start backend
```bash
uvicorn api:app --reload --port 8000
```

### Start frontend
```bash
cd ui_app
npm run dev
```

| Interface | URL |
|---|---|
| Customer Chat | http://localhost:5173 |
| Admin Panel | http://localhost:5173/admin |
| API Docs | http://localhost:8000/docs |

---

## How It Works

```
User Query
    │
    ▼
Hybrid Retriever (Vector + BM25)
    │
    ▼
Cohere Reranker — top 3 chunks only
    │
    ▼
Strict Prompt — context only, no hallucination
    │
    ▼
LLM via OpenRouter
    │
    ▼
Response + Chat Memory (multi-turn)
```

**SHA256 Cost Gate:** Embeddings only regenerate when your CSV actually
changes. Every re-run after the first one loads the persisted index from
disk. Note this reduces embedding cost, it does not eliminate it — the
first run (and any run after a CSV change) still calls the paid
`text-embedding-3-small` endpoint.

---

## Admin Panel

1. Go to `/admin`
2. Select your updated CSV
3. Click **Upload & Process Data** — one button does everything
4. Wait for success confirmation

---

## Logging

### Backend — `logger.py`
Centralized Python logging, writes to `app.log`. Controlled by `LOG_LEVEL`
and `LOG_FILE` in `.env`.

### Frontend — `ui_app/src/utils/logger.js`
Lightweight console logger for the React app. Not connected to any backend
or analytics service — output is browser console only.

- `logger.info(message, component)` — green
- `logger.warn(message, component)` — orange
- `logger.error(message, component)` — red
- `logger.debug(message, component)` — gray, **automatically suppressed
  when `NODE_ENV === 'production'`**

Each line is timestamped (`YYYY-MM-DD HH:MM:SS`) and optionally tagged with
a component name, e.g.:

```
[2026-07-16 14:32:01] [INFO] [AdminUpload] - CSV uploaded successfully
```

Usage:
```javascript
import logger from './utils/logger';

logger.info('Chat session started', 'ChatWindow');
logger.error('Failed to fetch response', 'ChatWindow');
```

This is a dev/debug aid, not a production monitoring solution — it does not
persist logs anywhere or send them off-device. If you need real tracking
(error reporting, usage analytics), this file alone won't get you there.

---

## Environment Variables

| Variable | Required | Purpose |
|---|---|---|
| `OPENROUTER_API_KEY` | Yes | LLM calls **and** embeddings (both routed through OpenRouter) |
| `OPENROUTER_API_BASE_URL` | Yes | OpenRouter endpoint |
| `COHERE_API_KEY` | Yes* | Reranking |
| `LAPTOP_CSV_PATH` / `DATA_FILE_PATH` | Yes | Path to your inventory CSV |

No separate OpenAI key is required — see the embeddings model-prefix bug
note above before your first run, though.

\* `config.py` currently raises a `ValueError` on startup if `COHERE_API_KEY`
is missing, despite the original README listing it as optional. It is
effectively required as the code stands.

---

## Running Evaluations

```bash
python testing.py
```

RAGAS evaluation — runs additional LLM calls, costs money.
Run only during development when you change something meaningful.
Never run in production.

---

## Important

- `chroma_db/`, `venv/`, `upload_metadata.json`, `app.log` are
  auto-generated — never commit them
- `.env` has your API keys — never commit it
- Embeddings are **not free**. First run (and any run after a CSV change)
  incurs real OpenAI API cost via `text-embedding-3-small`. Every run after
  that is fast and free until the CSV changes again.