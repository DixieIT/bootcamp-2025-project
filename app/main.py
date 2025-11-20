from fastapi import FastAPI, Header, HTTPException

from app.models.schemas import PromptCreate, PromptRead, PromptPatch, PredictRequest, PredictResponse
from app.services.prompt_store import FileSnapshotStore, InMemoryStore
from app.services.processor import process_document
from app.core.errors import http_error_handler
from app.core.logging import setup_logging
from app.api import routes_predict
from app.api import routes_prompts


app = FastAPI(title="Prompted Doc Processor", version="0.1.0")
app.add_exception_handler(Exception, http_error_handler)
setup_logging()
app.include_router(routes_prompts.prompt, prefix="/v1/prompts")
app.include_router(routes_predict.predictrouter, prefix="/v1/predict")


@app.get("/health")
def health():
    return {"status": "ok"}


