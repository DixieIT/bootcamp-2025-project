from fastapi import FastAPI, Header, HTTPException

from app.models.schemas import PromptCreate, PromptRead, PromptPatch, PredictRequest, PredictResponse
from app.services.prompt_store import FileSnapshotStore, InMemoryStore
from app.services.processor import process_document
from app.core.errors import http_error_handler
from app.core.config import settings
from app.core.logging import setup_logging


store = FileSnapshotStore("var/data.json") if settings.FILE_SNAPSHOT else InMemoryStore()
app = FastAPI(title="Prompted Doc Processor", version="0.1.0")
app.add_exception_handler(Exception, http_error_handler)
setup_logging()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/v1/prompts", response_model=PromptRead)
def create_prompt(
        data: PromptCreate,
        x_user_id: str = Header(default="user_anon")
    ):
    prompt = store.create(
        purpose=data.purpose,
        name=data.name,
        template=data.template,
    )
    return PromptRead.model_validate(prompt)


@app.get("/v1/prompts", response_model=list[PromptRead])
def list_prompts(
        purpose: str | None = None,
        x_user_id: str = Header(default="user_anon")
    ):
    prompts = store.list(purpose=purpose)
    return [PromptRead.model_validate(p) for p in prompts]


@app.patch("/v1/prompts/{prompt_id}", response_model=PromptRead)
def patch_prompt(
        prompt_id: str,
        data: PromptPatch,
        x_user_id: str = Header(default="user_anon")
    ):
    prompt = store.patch(prompt_id=prompt_id, template=data.template)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return PromptRead.model_validate(prompt)


@app.post("/v1/prompts/{prompt_id}/activate")
def activate_prompt(
        prompt_id: str,
        purpose: str,
        x_user_id: str = Header(default="user_anon"),
    ):
    prompt = store.set_active(
        user_id=x_user_id,
        purpose=purpose,
        prompt_id=prompt_id,
    )
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found or purpose mismatch")
    return {"status": "ok"}


@app.post("/v1/predict", response_model=PredictResponse)
def predict(
        req: PredictRequest,
        x_user_id: str = Header(default="user_anon"),
    ):
    active_prompt = store.get_active(user_id=x_user_id, purpose=req.purpose)
    if not active_prompt:
        raise HTTPException(status_code=400, detail=f"No active prompt for purpose '{req.purpose}'")

    output_text, model_info, latency = process_document(
        prompt=active_prompt,
        document_text=req.document_text,
        provider=req.provider,
        params=req.params,
    )

    return PredictResponse(
        output_text=output_text,
        model_info=model_info,
        prompt_id=active_prompt.id,
        prompt_version=active_prompt.version,
        latency_ms=latency,
    )
