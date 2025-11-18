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
    ...
