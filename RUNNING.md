# Running the Application

This guide covers how to run the Prompted Doc Processor with its Streamlit dashboard.

## Quick Start (Docker Compose)

The easiest way to run both the API and dashboard:

```bash
# Start both services
make compose-up

# View logs
make compose-logs

# Stop services
make compose-down
```

**Access:**
- **API**: http://localhost:8080
- **Streamlit Dashboard**: http://localhost:8501

## Local Development

### Option 1: Run Both Locally

```bash
# Terminal 1 - Start the API
make dev

# Terminal 2 - Start Streamlit
streamlit run streamlit_app.py
```

### Option 2: API in Docker, Streamlit Local

```bash
# Terminal 1 - Build and run API in Docker
make docker-build
make docker-run

# Terminal 2 - Run Streamlit locally
streamlit run streamlit_app.py
```

## Environment Configuration

Create a `.env` file in the project root:

```env
# Storage
FILE_SNAPSHOT=true

# Logging
LOG_LEVEL=INFO

# LLM Providers (optional)
GOOGLE_API_KEY=your-google-api-key
OPENAI_API_KEY=your-openai-api-key
```

## Available Commands

| Command | Description |
|---------|-------------|
| `make dev` | Run API locally with hot reload (port 8080) |
| `make test` | Run pytest tests |
| `make lint` | Run ruff linter |
| `make docker-build` | Build API Docker image |
| `make docker-run` | Run API container |
| `make compose-up` | Start API + Streamlit with Docker Compose |
| `make compose-down` | Stop Docker Compose services |
| `make compose-logs` | Follow Docker Compose logs |

## Architecture

```
                    +------------------+
                    |    Streamlit     |
                    |   Dashboard      |
                    |   (port 8501)    |
                    +--------+---------+
                             |
                             | HTTP
                             v
                    +------------------+
                    |    FastAPI       |
                    |      API         |
                    |   (port 8080)    |
                    +--------+---------+
                             |
              +--------------+--------------+
              |              |              |
              v              v              v
        +---------+    +---------+    +---------+
        |  Mock   |    | Google  |    | OpenAI  |
        |   LLM   |    |  Gemini |    |   API   |
        +---------+    +---------+    +---------+
```

## Dashboard Features

The Streamlit dashboard provides:

- **Create Prompts**: Create and manage prompt templates
- **Manage Active**: Activate prompts per user and purpose
- **Run Predictions**: Process documents using active prompts
- **View History**: Browse prediction history and logs
- **Config**: View system configuration and health status

## API Endpoints

### Health Check
```bash
curl http://localhost:8080/health
```

### Create a Prompt
```bash
curl -X POST http://localhost:8080/v1/prompts/ \
  -H "Content-Type: application/json" \
  -H "X-User-Id: demo_user" \
  -d '{
    "purpose": "summarize",
    "name": "Basic Summarizer",
    "template": "Summarize the following:\n\n{document}"
  }'
```

### List Prompts
```bash
curl http://localhost:8080/v1/prompts/ \
  -H "X-User-Id: demo_user"
```

### Activate a Prompt
```bash
curl -X POST "http://localhost:8080/v1/prompts/{prompt_id}/activate?purpose=summarize" \
  -H "X-User-Id: demo_user"
```

### Run Prediction
```bash
curl -X POST http://localhost:8080/v1/predict/ \
  -H "Content-Type: application/json" \
  -H "X-User-Id: demo_user" \
  -d '{
    "purpose": "summarize",
    "document_text": "Your document text here...",
    "provider": "mock"
  }'
```

## Troubleshooting

### Streamlit can't connect to API
- Ensure the API is running on port 8080
- Check if `API_BASE_URL` environment variable is set correctly
- In Docker Compose, the Streamlit container uses `http://api:8080`

### Port already in use
```bash
# Find and kill process on port 8080
lsof -i :8080
kill -9 <PID>
```

### Docker Compose health check fails
- The API container needs curl installed (already configured)
- Check API logs: `docker compose logs api`

### Reset data
```bash
# Remove persisted data
rm var/data.json
rm var/predictions.db
```
