# Self-RAG

A production-ready **Self-Retrieval-Augmented Generation** API. Unlike standard RAG, every step is graded — the system decides whether to retrieve, which docs are relevant, whether the answer is grounded, and whether it actually answers the question. If any check fails, it corrects itself before responding.

Built with **FastAPI**, **LangGraph**, **PostgreSQL + pgvector**, and **Google Gemini**.

---

## Graph

```mermaid
---
config:
  flowchart:
    curve: linear
---
graph TD;
    __start__([__start__]):::first
    upsert_thread(upsert_thread)
    should_retrieve(should_retrieve)
    generate_direct(generate_direct)
    context_retriever(context_retriever)
    context_relevance_checker(context_relevance_checker)
    no_answer_found(no_answer_found)
    generate_from_context(generate_from_context)
    answer_relevance_checker(answer_relevance_checker)
    rewrite_answer(rewrite_answer)
    stream_answer(stream_answer)
    check_answer_usefulness(check_answer_usefulness)
    rewrite_question(rewrite_question)
    __end__([__end__]):::last

    __start__ --> upsert_thread
    upsert_thread --> should_retrieve
    should_retrieve -. True .-> context_retriever
    should_retrieve -. False .-> generate_direct
    generate_direct --> __end__
    context_retriever --> context_relevance_checker
    context_relevance_checker -. True .-> generate_from_context
    context_relevance_checker -. False .-> no_answer_found
    generate_from_context --> answer_relevance_checker
    answer_relevance_checker -.-> check_answer_usefulness
    answer_relevance_checker -.-> rewrite_answer
    rewrite_answer --> answer_relevance_checker
    check_answer_usefulness -.-> stream_answer
    check_answer_usefulness -.-> no_answer_found
    check_answer_usefulness -.-> rewrite_question
    rewrite_question --> context_retriever
    stream_answer --> __end__
    no_answer_found --> __end__

    classDef default fill:#f2f0ff,line-height:1.2
    classDef first fill-opacity:0
    classDef last fill:#bfb6fc
```

---

## How It Works

### 1. Retrieval Gating
The LLM first decides if retrieval is even needed. Conversational or general questions bypass the vector search entirely and go straight to `generate_direct`.

### 2. Context Grading
Retrieved documents are checked for relevance in **parallel** — each doc gets an independent LLM call. Only relevant docs pass through to generation.

### 3. Answer Grounding (Self-RAG core)
After generation, the answer is graded against the context:
- `FULLY_SUPPORTED` → pass
- `PARTIALLY_SUPPORTED` / `NOT_SUPPORTED` → rewrite the answer (up to 3 iterations)

### 4. Usefulness Check
Even a grounded answer might not actually answer the question. A final usefulness check catches this case and either accepts the answer, rewrites the **query** for better retrieval, or gives up with `no_answer_found`.

### 5. Streaming
The final approved answer is streamed to the client in one shot. The answer is held in state during the grading/rewriting loops — streaming mid-loop would be irreversible.

---

## Stack

| | |
|---|---|
| API | FastAPI |
| Graph / Orchestration | LangGraph |
| LLM | Google Gemini |
| Vector store | PostgreSQL + pgvector |
| ORM | SQLAlchemy 2 (async) |
| Migrations | Alembic |
| Background tasks | Celery + Redis |
| Python | 3.12+ |

---

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Python 3.12+
- [uv](https://github.com/astral-sh/uv)

### Setup

```bash
# 1. Clone and install
git clone <repo-url>
cd self-rag
uv sync

# 2. Configure environment
cp .env.example .env
# Fill in: DATABASE_URL, GOOGLE_API_KEY, REDIS_URL, etc.

# 3. Start services (Postgres + Redis)
docker-compose up -d

# 4. Run migrations
alembic upgrade head

# 5. Start the API
uvicorn app.main:app --reload

# 6. Start the Celery worker (for document ingestion)
celery -A app.celery_app worker --loglevel=info
```

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/threads` | Create a new conversation thread |
| `POST` | `/threads/{id}/chat` | Send a message (streaming response) |
| `POST` | `/documents` | Upload a document for ingestion |
| `GET` | `/health` | Health check |

---

## Project Structure

```
app/
├── api/            # Routers, controllers, request/response models
├── bot/
│   ├── nodes/      # One file per graph node
│   ├── state.py    # RAGState definition
│   └── llm.py      # Shared LLM + parser instances
├── rag/
│   ├── graph.py    # Graph builder (RAGGraph)
│   ├── retriever.py
│   └── ingestor/   # PDF ingestion pipeline
├── db/
│   ├── models/     # SQLAlchemy ORM models
│   └── services/   # Async DB service layer
├── worker/         # Celery tasks
├── core/           # Config, logging, exception handling
└── middlewares/    # Auth, API tracing
```