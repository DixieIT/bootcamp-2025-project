from .llm_client import PROVIDERS
from .prompt_store import PromptStore

def process_document(
        store: PromptStore,
        user_id: str,
        purpose: str,
        document_text: str,
        provider: str = "mock",
        **params,
    ):
    if provider not in PROVIDERS:
        raise ValueError(f"Unsupported provider: {provider}")
    llm_client = PROVIDERS[provider]({})
    prompt = store.get_active(user_id=user_id, purpose=purpose)
    if not prompt:
        raise ValueError(f"No active prompt for purpose '{purpose}'")
    filled_prompt = prompt.template.replace("{document}", document_text)
    output_text = llm_client.generate(
        prompt=filled_prompt,
        **params,
    )
    return output_text["text"], output_text["model_info"], output_text["latency"]