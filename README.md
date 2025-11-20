# AI Bootcamp Project – Prompted Document Processor

## Week 1

A FastAPI service that stores **user prompts by purpose** (e.g., `summarize`, `extract_entities`, `translate`) and applies the active prompt to incoming documents. Minimal persistence (in‑memory with optional JSON file snapshot). Deliverable: **working Dockerized API** + tests + CI skeleton.

---

### 1) Learning Objectives

* **Service design** with FastAPI: routing, request/response schemas, validation, error handling.
* **Patterns**: Strategy/Adapter for model providers; Observer for logging/metrics hooks.
* **Config & logging**: `.env`, structured logs, consistent error responses.
* **Testing**: PyTest with mocked LLM client; snapshot/golden tests for prompt stability.
* **Packaging & CI**: `pyproject.toml`, local package layout, GitHub Actions (lint + tests).
* **Containerization**: Dockerfile and run with environment variables.

> Week 2 teaser: swap the store to a real DB (SQLite → Postgres) and add migrations — interface is already abstracted.

---

### 2) Repository Structure

```
prompted-doc-processor/
├─ README.md
├─ Makefile
├─ pyproject.toml
├─ requirements.txt             # for Dockerfile
├─ .env                         # git-ignored
├─ .gitignore
├─ .github/
│  └─ workflows/
│     └─ ci.yml
├─ docker/
│  └─ Dockerfile
├─ app/                         # FastAPI service (executable layer)
│  ├─ main.py
│  ├─ api/
│  │  ├─ __init__.py
│  │  ├─ routes_prompts.py
│  │  └─ routes_predict.py
│  ├─ core/
│  │  ├─ config.py
│  │  ├─ logging.py
│  │  └─ errors.py
│  ├─ models/
│  │  ├─ schemas.py             # Pydantic models for API
│  │  └─ domain.py              # Domain entities (Prompt, Purpose, User)
│  ├─ services/
│  │  ├─ llm_client.py          # Adapter interface + mock impl
│  │  ├─ prompt_store.py        # InMemoryStore + FileSnapshotStore
│  │  └─ processor.py           # Orchestrates prompt + doc → call LLM
│  └─ instrumentation/
│     └─ observers.py           # hooks for logging/metrics
├─ tests/
│  ├─ conftest.py
│  ├─ test_prompts_api.py
│  ├─ test_predict_api.py
│  └─ fixtures/
│     └─ sample_texts/
│        ├─ article.txt
│        └─ invoice.txt
└─ var/                         # runtime artifacts (git-ignored)
   └─ data.json                 # optional JSON snapshot
```

---

### 3) Endpoints (MVP)

#### Prompts

* `POST /v1/prompts` – create prompt

  * body: `{ purpose: str, name: str, template: str }`
  * returns: `{ id, purpose, name, template, version, active }`
* `GET /v1/prompts?purpose=...` – list prompts (filter by purpose)
* `PATCH /v1/prompts/{id}` – modify `name`/`template` (bumps `version`)
* `POST /v1/prompts/{id}/activate` – set as active for `(user, purpose)`
* `GET /v1/prompts/active?purpose=...` – fetch active prompt for purpose

#### Prediction

* `POST /v1/predict`

  * body: `{ purpose: str, document_text: str, params?: {max_tokens?: int, temperature?: float}, provider?: "mock"|"openai"|"gemini"|"watson" }`
  * behavior: load active prompt for purpose → render → call provider client
  * returns: `{ output_text, model_info: {...}, prompt_id, prompt_version, latency_ms }`

> **MVP simplification**: single “current user” context read from `X-User-Id` header or default `user_anon`.

---

### 4) Lab Plan (Days 3–5)

#### **Day 3 – APIs, Services, Configuration**

**10:45–11:45 – Lab 1: Bootstrap service**

* Scaffold monorepo, add `pyproject`/deps, `app/main.py`, health route `/health`.
* Implement schemas, domain models, `InMemoryStore`.
* **Checkpoint:** `POST /v1/prompts` and `GET /v1/prompts` work locally.

**14:30–15:30 – Lab 2: Config, Logging & Errors**

* Add `Settings`, structured logging, global error handler; propagate `X-User-Id`.
* **Checkpoint:** logs show request flow; 4xx vs 5xx semantics verified.

**17:00–18:00 – Lab 3: Prediction Endpoint**

* Implement `processor.py`, mock LLM, `/v1/predict` with active prompt resolution.
* **Checkpoint:** given a prompt & document, API returns mock output with metadata.

#### **Day 4 – Packaging, CI, Docker**

**10:45–11:45 – Lab 4: Tests & Mocks**

* Write tests for prompt CRUD, activation, predict happy path + errors.
* **Checkpoint:** `pytest` passes (≥8 tests), coverage report optional.

**14:30–15:30 – Lab 5: CI Pipeline**

* Add Ruff + CI workflow; fix lint issues.
* **Checkpoint:** PR triggers green CI.

**17:00–18:00 – Lab 6: Containerization**

* Write Dockerfile, build and run; confirm endpoints via `curl` or client.
* **Checkpoint:** `docker run -p 8080:8080 ...` serves API and persists JSON snapshot.

#### **Day 5 – Integration & Review**

**10:45–11:45 – Lab 7: Improvement Pass**

* Add `PATCH /prompts/{id}` (version bump), `GET /prompts/active`.
* **Checkpoint:** version increments on template change; active prompt visible.

**14:30–15:30 – Lab 8: Perf & Robustness**

* Add request size limit, input validation, timeouts in processor.
* Optional: simple timing and latency field.
* **Checkpoint:** oversized docs rejected; latency captured.

**17:00–18:00 – Lab 9: Showcase & Review**

* Demo containerized service; run rubric; collect logs/metrics snippet.
* **Checkpoint:** ready-to-present microservice.

---

### 5) Quickstart

```
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
curl -X POST localhost:8080/v1/prompts -H 'Content-Type: application/json' \
  -d '{"purpose":"summarize","name":"base","template":"Summarize in 3 bullets: {{document}}"}'
```

---

### 6) Stretch Goals (optional)

* **Async** `/v1/predict/batch` using `asyncio.gather`.
* **A/B compare** endpoint: apply two prompts to the same document, return diff.
* **Templating** via Jinja2 instead of naive `replace`.
* **Basic RBAC**: lock prompt modification to `X-User-Id` owner. **done**
