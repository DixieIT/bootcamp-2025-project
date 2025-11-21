# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a FastAPI-based microservice for document processing using LLM prompts. It allows users to:
- Store and version prompts by purpose (e.g., "summarize", "extract_entities")
- Activate prompts per user and purpose
- Apply active prompts to documents via LLM providers

This is a Week 1 bootcamp deliverable with minimal persistence (in-memory or JSON snapshot). Week 2 will add database migrations and swap to SQLite/Postgres.

## Common Commands

### Development
```bash
make dev              # Run locally with hot reload on port 8080
make test             # Run pytest tests
make lint             # Run ruff linter
make typecheck        # Run mypy type checking (if configured)
```

### Docker
```bash
make docker-build     # Build Docker image as prompted-doc-processor:local
make docker-run       # Run containerized service with .env file
```

### Direct Commands
```bash
# Run app directly
uvicorn app.main:app --reload --port 8080

# Run single test file
PYTHONPATH=. pytest tests/test_prompts_api.py -v

# Run specific test
PYTHONPATH=. pytest tests/test_prompts_api.py::test_create_prompt -v
```

## Architecture

### Core Pattern: Strategy + Adapter

**LLM Client Abstraction** (`app/services/llm_client.py`):
- Abstract `LLMClient` interface with `generate()` method
- Multiple provider implementations (currently only `MockLLM`)
- `PROVIDERS` registry maps provider names to client classes
- Future providers: OpenAI, Gemini, Watson

**Prompt Store Abstraction** (`app/services/prompt_store.py`):
- Abstract `PromptStore` interface defines CRUD operations
- `InMemoryStore`: Fast ephemeral storage
- `FileSnapshotStore`: Extends InMemoryStore, persists to `var/data.json` on writes
- Store selection controlled by `FILE_SNAPSHOT` env var in `app/core/config.py`

**Dual Store Instance Issue**: Currently both `routes_prompts.py` and `routes_predict.py` create their own store instances. This means changes in one router won't be visible to the other unless using `FileSnapshotStore`. This is acceptable for the Week 1 MVP but should be refactored to use a singleton or dependency injection in Week 2.

### Document Processing Flow

1. User calls `POST /v1/predict` with purpose and document text
2. `routes_predict.py` retrieves active prompt for (user_id, purpose) from store
3. `processor.py` orchestrates: selects LLM provider, renders prompt template, calls LLM
4. Template rendering uses simple string replacement: `{document}` placeholder
5. Returns output with metadata (prompt_id, version, latency, model_info)

### User Context

- User identity propagated via `X-User-Id` header (defaults to "user_anon")
- Each user can have one active prompt per purpose
- RBAC stretch goal implemented: users can only patch their own prompts

### Prompt Versioning

- Prompts start at version 1
- Template changes increment version (intended but not fully implemented in `patch()`)
- Version field exists in domain model but version bumping logic needs completion

## Key Files

- `app/main.py` - FastAPI app setup, routers, error handling
- `app/api/routes_prompts.py` - Prompt CRUD endpoints
- `app/api/routes_predict.py` - Document prediction endpoint
- `app/services/processor.py` - Core orchestration logic
- `app/services/prompt_store.py` - Storage abstraction and implementations
- `app/services/llm_client.py` - LLM provider interface
- `app/models/domain.py` - Domain entity (Prompt)
- `app/models/schemas.py` - Pydantic request/response models
- `app/core/config.py` - Environment-based settings
- `app/core/logging.py` - Structured logging setup
- `app/core/errors.py` - Global error handler

## Configuration

Settings loaded via `pydantic-settings` from `.env` file:
- `FILE_SNAPSHOT` (bool, default=True) - Use JSON file persistence vs in-memory
- `LOG_LEVEL` (str, default="INFO") - Logging level

## Testing

Tests use `httpx` TestClient to make API calls:
- `tests/test_prompts_api.py` - Prompt management endpoints
- `tests/test_predict_api.py` - Document prediction endpoint
- `tests/conftest.py` - Shared fixtures
- `tests/fixtures/sample_texts/` - Sample documents for testing

When adding tests, remember to set `PYTHONPATH=.` to ensure proper imports.

## Known Issues & Limitations

1. **Dual Store Instances**: Each router creates its own store instance. Use `FileSnapshotStore` to share state.
2. **Version Bumping**: `Prompt.update()` method exists but isn't called in `patch()` endpoint.
3. **Template Rendering**: Uses naive string `.replace("{document}", ...)` - Week 1 acceptable, consider Jinja2 later.
4. **No Async**: All I/O is synchronous. Stretch goal: async LLM calls with `asyncio.gather`.
5. **Minimal Validation**: No request size limits, timeout handling, or input sanitization yet.

## CI/CD

GitHub Actions workflow (`.github/workflows/ci.yml`):
- Runs on push and PR
- Python 3.11
- Installs dependencies, pytest, ruff, httpx
- Runs tests and linter

## Future Enhancements (Week 2+)

- Database migrations (SQLite → Postgres)
- Real LLM providers (OpenAI, Gemini, Watson)
- Jinja2 template rendering
- Async batch prediction endpoint
- Request size limits and timeouts
- Observer pattern for metrics/logging hooks
- Proper version bumping on patch
