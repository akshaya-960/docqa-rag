# DocQA — A Retrieval-Augmented Question Answering Microservice

A small, honest RAG service: upload documents, ask questions in plain English, get
answers grounded in your own text with cited sources — not a general chatbot.

> Built as a portfolio project to demonstrate a production-shaped GenAI backend:
> FastAPI, PostgreSQL + pgvector, local embeddings, Google Gemini for answer
> generation, a minimal tool-routing agent step, and a React front end.

---

## Table of Contents

- [Problem Statement](#problem-statement)
- [Architecture](#architecture)
- [Why These Choices](#why-these-choices)
- [Setup & Installation](#setup--installation)
- [Running the Project](#running-the-project)
- [API Reference](#api-reference)
- [Repository Structure](#repository-structure)
- [Limitations](#limitations)
- [Future Work](#future-work)

---

## Problem Statement

Large language models are fluent but not grounded — asked about a specific internal
document, they either refuse or confidently hallucinate. Retrieval-Augmented Generation
(RAG) fixes this by fetching the relevant passages from your own corpus first, then asking
the model to answer *using only that context*.

This project builds the smallest complete version of that pipeline that still reflects
real production decisions: a real database (not an in-memory list), a real embedding
model, chunking with overlap, similarity search with a distance metric, and a prompt that
forces the model to say "I don't know" rather than guess.

## Architecture

```
                    ┌─────────────┐
   PDF / text  ───► │   /ingest   │──► chunk ──► embed ──► store in Postgres (pgvector)
                    └─────────────┘

                    ┌─────────────┐
   Question    ───► │    /ask     │──► embed query
                    └─────────────┘        │
                                            ▼
                                   tool router (agent.py)
                                    │                │
                        needs a calculation?    needs document context?
                                    │                │
                                    ▼                ▼
                            calculator tool    pgvector similarity search (top-k)
                                    │                │
                                    └───────┬────────┘
                                            ▼
                                  build grounded prompt
                                            ▼
                                     call Gemini (LLM)
                                            ▼
                              answer + cited source chunks
```

React front end (`frontend/`) talks to the FastAPI backend over `fetch` — a single chat
box, a document upload control, and inline source citations under each answer.

## Why These Choices

Documenting trade-offs honestly, the way any real design doc should:

- **pgvector over a dedicated vector DB (Pinecone/Weaviate/Chroma).** Postgres is
  already the JD's required skill, it's one fewer moving part to run locally, and at this
  corpus size (hundreds to low-thousands of chunks) an IVFFlat/HNSW index in Postgres is
  more than fast enough. A dedicated vector DB earns its complexity at a scale this
  project doesn't need.
- **Local sentence-transformer embeddings (`all-MiniLM-L6-v2`) over an embeddings API.**
  No per-call cost or external dependency for the ingest path, fully reproducible, and
  384 dimensions keeps the Postgres index small. The trade-off: lower embedding quality
  than a large hosted model — acceptable for a portfolio corpus, called out below as a
  limitation rather than hidden.
- **A tool-router, not a full agent framework.** `agent.py` is a deliberately small,
  auditable decision: "does this question need a calculator, or does it need retrieved
  context?" It demonstrates the *concept* of an agent workflow (route to a tool based on
  the query) without pulling in a framework's worth of abstraction for a project this
  size. LangChain/LlamaIndex-style orchestration is listed under Future Work rather than
  bolted on for the sake of a resume line.
- **Google Gemini for generation.** Called via the `google-genai` SDK with a system
  prompt that explicitly instructs the model to answer only from the provided context and
  say when it can't. Chosen for a free, no-credit-card-required API key, which keeps this
  project runnable by anyone who clones it without a billing setup.

## Setup & Installation

**Requirements:** Python 3.11 (newer versions may lack prebuilt wheels for some
dependencies), Docker (for Postgres+pgvector), Node 18+ (for the frontend), and a
free Gemini API key from [aistudio.google.com/apikey](https://aistudio.google.com/apikey).

```bash
git clone https://github.com/<your-username>/docqa-rag.git
cd docqa-rag
```

**1. Start Postgres with pgvector:**

```bash
docker compose up -d
```

> This project maps the container to host port `5433` (not Postgres's usual `5432`) to
> avoid clashing with a Postgres install or another project already using `5432`. If
> `5433` is also taken on your machine, change the port in both `docker-compose.yml`
> and `.env`'s `DATABASE_URL` to something free.

**2. Create a virtual environment and install backend dependencies:**

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**3. Configure environment variables:**

```bash
cp .env.example .env
# then edit .env and set GEMINI_API_KEY (get one free at https://aistudio.google.com/apikey)
```

**4. Install frontend dependencies:**

```bash
cd frontend
npm install
cd ..
```

## Running the Project

**Start the backend:**

```bash
uvicorn backend.main:app --reload --port 8000
```

On startup, the app creates the `vector` extension and the `documents`/`chunks` tables if
they don't already exist — no separate migration step needed for this project's scope.

**Ingest a document:**

```bash
curl -X POST http://localhost:8000/ingest \
  -F "file=@data/sample_docs/your_file.pdf"
```

Or ingest everything in `data/sample_docs/` at once:

```bash
python scripts/ingest_docs.py
```

**Ask a question:**

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What does the document say about onboarding?"}'
```

**Start the frontend:**

```bash
cd frontend
npm run dev
```

Opens at `http://localhost:5173` and talks to the backend at `http://localhost:8000`.

**Run tests:**

```bash
pytest
```

## API Reference

| Method | Endpoint  | Description                                                |
| ------ | --------- | ------------------------------------------------------------ |
| GET    | `/health` | Liveness check, also confirms DB connectivity                |
| POST   | `/ingest` | Upload a PDF or `.txt` file; chunks, embeds, and stores it    |
| POST   | `/ask`    | `{"question": "..."}` → grounded answer + cited source chunks |

`/ask` response shape:

```json
{
  "answer": "...",
  "used_tool": "retrieval",
  "sources": [
    {"document": "handbook.pdf", "chunk_index": 4, "text": "..."}
  ]
}
```

## Repository Structure

```
docqa-rag/
├── backend/
│   ├── main.py          # FastAPI app, routes, startup DB init
│   ├── config.py         # Settings via pydantic-settings
│   ├── database.py       # SQLAlchemy engine/session, pgvector setup
│   ├── models.py         # Document, Chunk ORM models
│   ├── schemas.py        # Pydantic request/response models
│   ├── embeddings.py     # Sentence-transformer loader + encode()
│   ├── ingest.py         # PDF/text extraction, chunking, storage
│   ├── retrieval.py      # pgvector similarity search
│   ├── agent.py          # Minimal tool router (calculator vs retrieval)
│   └── llm.py            # Prompt construction + Gemini API call (with retry on 503s)
├── scripts/
│   └── ingest_docs.py    # Bulk-ingest everything in data/sample_docs/
├── tests/
│   └── test_api.py       # FastAPI TestClient tests (LLM call mocked)
├── frontend/             # Vite + React chat UI
├── data/sample_docs/     # Drop PDFs/txt files here
├── docker-compose.yml    # Postgres + pgvector
├── requirements.txt
└── .env.example
```

## Limitations

Documented honestly, not as an afterthought:

- **Local embeddings are lower-quality than hosted large embedding models.** Expect
  weaker retrieval on subtle or paraphrased questions compared to, say, OpenAI's
  `text-embedding-3-large` or Voyage AI embeddings.
- **No re-ranking step.** Retrieval returns raw top-k by cosine distance; a cross-encoder
  re-ranker would improve precision on borderline matches.
- **Chunking is naive (fixed-size with overlap), not structure-aware.** It doesn't respect
  headings, tables, or semantic boundaries — a document-aware splitter would help on
  long, structured PDFs.
- **The agent step is a single if/else router, not a planning agent.** It picks one tool
  per question and doesn't chain multiple tool calls or retries.
- **No conversation memory.** Each `/ask` call is stateless; there's no multi-turn context
  carried between questions.
- **No evaluation harness.** There's no retrieval-quality or answer-quality benchmark yet
  (e.g. hit rate@k, faithfulness scoring) — accuracy claims would need one before being
  taken as anything more than "it works on the examples I tried."

## Future Work

- Add a cross-encoder re-ranking stage after initial retrieval
- Swap the naive chunker for a structure-aware splitter (headings, tables)
- Add conversation memory for multi-turn follow-up questions
- Build a small retrieval-eval set (query → expected chunk) and report hit-rate@k
- Migrate the tool router to LangChain or LangGraph once more than two tools are needed
- Add streaming responses (SSE) from `/ask` for a more responsive chat UI

---

*Built as a portfolio project. Not affiliated with any employer.*