from abc import ABC, abstractmethod

class LLMClient(ABC):
    @abstractmethod
    def generate(self, prompt: str, **params) -> dict: ...

class MockLLM(LLMClient):
    def generate(self, prompt: str, **params):
        return {"text": f"[MOCK OUTPUT]\n{prompt[:200]} ...", "provider": "mock"}

PROVIDERS = {"mock": MockLLM}