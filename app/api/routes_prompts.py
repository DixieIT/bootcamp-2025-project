from fastapi import APIRouter, Header, HTTPException
from app.models.schemas import PromptCreate, PromptRead, PromptPatch
from app.services.prompt_store import FileSnapshotStore, InMemoryStore
from app.core.config import settings

prompt = APIRouter()

store = FileSnapshotStore("var/data.json") if settings.FILE_SNAPSHOT else InMemoryStore()

@prompt.post("/", response_model=PromptRead)
def create_prompt(
        data: PromptCreate,
        x_user_id: str = Header(default="user_anon")
    ):
    prompt = store.create(
        purpose=data.purpose,
        name=data.name,
        template=data.template,
        user_id=x_user_id)

    response_model=PromptRead(
        id=prompt.id,
        purpose=prompt.purpose,
        name=prompt.name,
        template=prompt.template,
        version=1,
        active=False,
    )


    return response_model


@prompt.get("/", response_model=list[PromptRead])
def list_prompts(
        purpose: str | None = None,
        x_user_id: str = Header(default="user_anon")
    ):
    return store.list(purpose=purpose)


@prompt.patch("/{prompt_id}", response_model=PromptRead)
def patch_prompt(
        prompt_id: str,
        data: PromptPatch,
        x_user_id: str = Header(default="user_anon")
    ):
    prompt = store.patch(prompt_id=prompt_id, template=data.template, user_id=x_user_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return PromptRead.model_validate(prompt)


@prompt.post("/{prompt_id}/activate")
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