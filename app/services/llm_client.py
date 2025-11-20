from abc import ABC, abstractmethod

class LLMClient(ABC):
    @abstractmethod
    def generate(self, prompt: str, **params) -> dict: ...

class MockLLM(LLMClient):
    def __init__(self, model_info: dict) -> None:
        self.model_info = model_info
        self.version = "1.0-mock"
        self.latency: int = 0
    def generate(self, prompt: str, **params):
        self.latency = 100
        return {"text": f"[MOCK OUTPUT]\n{prompt[:200]} ...", "provider": "mock", "model_version": self.version}, self.model_info, self.latency

PROVIDERS = {"mock": MockLLM}