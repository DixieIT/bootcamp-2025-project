from fastapi import APIRouter, Header, HTTPException
from app.models.schemas import PredictRequest, PredictResponse
from app.services.processor import process_document
from app.services.prompt_store import FileSnapshotStore, InMemoryStore
from app.core.config import settings

predictrouter = APIRouter()

store = FileSnapshotStore("var/data.json") if settings.FILE_SNAPSHOT else InMemoryStore()

@predictrouter.post("/", response_model=PredictResponse)
def predict(
        req: PredictRequest,
        x_user_id: str = Header(default="user_anon"),
    ):
    active_prompt = store.get_active(user_id=x_user_id, purpose=req.purpose)
    if not active_prompt:
        raise HTTPException(status_code=400, detail=f"No active prompt for purpose '{req.purpose}'")

    stored_prompt = store.get(active_prompt.id)
    if not stored_prompt or stored_prompt.version != active_prompt.version:
        raise HTTPException(status_code=400, detail="Active prompt version mismatch")
    
    output_text, model_info, latency = process_document(
        store=store,
        user_id=x_user_id,
        purpose=req.purpose,
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
