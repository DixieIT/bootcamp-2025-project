from fastapi import APIRouter, Header, HTTPException
import logging
from app.models.schemas import PromptCreate, PromptRead, PromptPatch
from app.services.prompt_store import FileSnapshotStore, InMemoryStore
from app.core.config import settings

logger = logging.getLogger(__name__)
prompt = APIRouter()

store = FileSnapshotStore("var/data.json") if settings.FILE_SNAPSHOT else InMemoryStore()

@prompt.post("/", response_model=PromptRead)
def create_prompt(
        data: PromptCreate,
        x_user_id: str = Header(default="user_anon")
    ):
    logger.info(f"Creating prompt for user={x_user_id}, purpose={data.purpose}, name={data.name}")
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

    logger.info(f"Created prompt id={prompt.id}")
    return response_model


@prompt.get("/", response_model=list[PromptRead])
def list_prompts(
        purpose: str | None = None,
        x_user_id: str = Header(default="user_anon")
    ):
    logger.info(f"Listing prompts for user={x_user_id}, purpose={purpose}")
    prompts = store.list(purpose=purpose)
    response_model: list[PromptRead] = []
    for prompt in prompts:
        response_model.append(
            PromptRead(
                id=prompt.id,
                purpose=prompt.purpose,
                name=prompt.name,
                template=prompt.template,
                version=prompt.version,
                active=(store.get_active(user_id=x_user_id, purpose=prompt.purpose) == prompt)
            )
        )
    return response_model


@prompt.patch("/{prompt_id}", response_model=PromptRead)
def patch_prompt(
        prompt_id: str,
        data: PromptPatch,
        x_user_id: str = Header(default="user_anon")
    ):
    logger.info(f"Patching prompt id={prompt_id} for user={x_user_id}")
    prompt = store.patch(prompt_id=prompt_id, template=data.template, user_id=x_user_id)
    if not prompt:
        logger.warning(f"Prompt not found or unauthorized: id={prompt_id}, user={x_user_id}")
        raise HTTPException(status_code=404, detail="Prompt not found")
    response_model: PromptRead = PromptRead(
        id=prompt.id,
        purpose=prompt.purpose,
        name=prompt.name,
        template=prompt.template,
        version=prompt.version,
        active=(store.get_active(user_id=x_user_id, purpose=prompt.purpose) == prompt)
    )
    return response_model


@prompt.post("/{prompt_id}/activate")
def activate_prompt(
        prompt_id: str,
        purpose: str,
        x_user_id: str = Header(default="user_anon"),
    ):
    logger.info(f"Activating prompt id={prompt_id} for user={x_user_id}, purpose={purpose}")
    prompt = store.set_active(
        user_id=x_user_id,
        purpose=purpose,
        prompt_id=prompt_id,
    )
    if not prompt:
        logger.warning(f"Failed to activate prompt: id={prompt_id}, user={x_user_id}, purpose={purpose}")
        raise HTTPException(status_code=404, detail="Prompt not found or purpose mismatch")
    logger.info(f"Successfully activated prompt id={prompt_id}")
    return {"status": "ok"}