# LaptopIQ — AI Powered Laptop Sales Assistant

An intelligent sales assistant built on RAG (Retrieval-Augmented Generation).
Answers customer questions strictly from your uploaded laptop inventory 
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
├── logger.py                   # Centralized logging
├── testing.py                  # Manual pipeline tests
├── upload_metadata.json        # Auto-generated — tracks last upload info
├── app.log                     # Auto-generated — runtime logs
├── .env                        # Your API keys — NEVER commit this
├── Data/                       # Your laptop CSV files go here
├── Data_cleaning/              # Intermediate cleaning scripts
├── chroma_db/                  # Auto-generated vector store
├── venv/                       # Python virtual environment
└── ui_app/                     # React + Vite frontend
    ├── src/                    # All React components
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
| Embeddings | BGE-small-en-v1.5 | Local — zero embedding API cost |
| LLM | OpenRouter (Gemini Flash Lite) | Response generation |
| Hybrid Retrieval | BM25 + Vector Fusion | Keyword + semantic search |
| Reranking | Cohere Rerank v3.5 | Filters top chunks before LLM |
| Frontend | React + Vite | Chat UI + Admin panel |
| Evaluation | RAGAS | Offline hallucination testing |

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
disk — zero extra cost.

---

## Admin Panel

1. Go to `/admin`
2. Select your updated CSV
3. Click **Upload & Process Data** — one button does everything
4. Wait for success confirmation

---

## Environment Variables

| Variable | Required | Purpose |
|---|---|---|
| `OPENROUTER_API_KEY` | Yes | LLM calls |
| `COHERE_API_KEY` | No | Reranking (better accuracy) |
| `LAPTOP_CSV_PATH` | Yes | Path to your inventory CSV |

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
- First run is slow (embedding generation). Every run after is fast
  unless CSV changes.
