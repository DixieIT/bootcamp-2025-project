from fastapi import FastAPI, Header, HTTPException

from app.models.schemas import PromptCreate, PromptRead, PromptPatch, PredictRequest, PredictResponse
from app.services.prompt_store import FileSnapshotStore, InMemoryStore
from app.services.processor import process_document
from app.services.db_service import init_db
from app.core.errors import http_error_handler
from app.core.logging import setup_logging
from app.core.config import settings
from app.api import routes_predict
from app.api import routes_prompts
from app.api import routes_history

app = FastAPI(title="Prompted Doc Processor", version="0.1.0")
app.add_exception_handler(Exception, http_error_handler)
setup_logging()
init_db()  # Initialize database tables on startup
app.include_router(routes_prompts.prompt, prefix="/v1/prompts")
app.include_router(routes_predict.predictrouter, prefix="/v1/predict")
app.include_router(routes_history.router, prefix="/v1")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/history")
def get_history(limit: int = 10, level: str = ""):
    """
    Get application logs from database

    Query params:
    - limit: Number of logs to return (default 10)
    - level: Filter by log level (INFO, WARNING, ERROR, DEBUG)
    """
    from app.services.db_service import get_logs
    history = get_logs(limit=limit, level=level)
    return {"history": history}

@app.get("/config")
def get_config():
    config_dump = {
        "FILE_SNAPSHOT": settings.FILE_SNAPSHOT,
        "LOG_LEVEL": settings.LOG_LEVEL,
        "GOOGLE_API_KEY": "***" + settings.GOOGLE_API_KEY[-4:] if settings.GOOGLE_API_KEY else None,
        "OPENAI_API_KEY": "***" + settings.OPENAI_API_KEY[-4:] if settings.OPENAI_API_KEY else None,
        "database_path": "var/database.db",
        "log_file_path": "logs/app.log",
        "snapshot_path": "var/data.json" if settings.FILE_SNAPSHOT else None
    }
    return config_dump

