import logging
from .llm_client import PROVIDERS
from .prompt_store import PromptStore
from .db_service import log_prediction
from .template_renderer import render_template
from .llm_client import *

logger = logging.getLogger(__name__)

def process_document(
        store: PromptStore,
        user_id: str,
        purpose: str,
        document_text: str,
        provider: str = "mock",
        **params,
    ):
    if provider not in PROVIDERS:
        logger.error(f"Unsupported provider: {provider}")
        raise ValueError(f"Unsupported provider: {provider}")
    logger.info(f"Processing document with provider={provider}, user_id={user_id}, purpose={purpose}")
    if provider == "mock":
        llm_client = PROVIDERS[provider]({})
    else:
        llm_client = PROVIDERS[provider]()
    prompt = store.get_active(user_id=user_id, purpose=purpose)
    if not prompt:
        logger.error(f"No active prompt for user_id={user_id}, purpose={purpose}")
        raise ValueError(f"No active prompt for purpose '{purpose}'")

    # Render template with Jinja2 (supports backward compatibility)
    filled_prompt = render_template(prompt.template, document_text)
    logger.debug(f"Rendered prompt template for prompt_id={prompt.id}")
    result = llm_client.generate(
        prompt=filled_prompt,
        **params,
    )

    output_dict, duration = result
    logger.info(f"LLM generation completed in {duration}s")

    output_dict["latency"] = int(duration * 1000)
    # Log prediction to database
    log_prediction(
        prompt=filled_prompt,
        response=output_dict["text"],
        user_id=user_id,
        purpose=purpose,
        provider=provider,
        prompt_id=prompt.id,
        latency_ms=output_dict["latency"]
    )

    return output_dict["text"], output_dict["model_info"], output_dict["latency"]