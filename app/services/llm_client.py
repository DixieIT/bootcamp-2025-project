from abc import ABC, abstractmethod
from dataclasses import dataclass
import time
import asyncio
from google import genai
from google.genai.types import GenerateContentConfig
from openai import OpenAI, AsyncOpenAI
from abc import ABC, abstractmethod

import app

from ..models.provider import Provider
from ..instrumentation import timed, timed_sync
import os


class LLMClient(ABC):
    @abstractmethod
    def generate(self, prompt: str, **params) -> dict: ...

class MockLLM(LLMClient):
    def __init__(self, model_info: dict) -> None:
        self.model_info = model_info
        self.version = "1.0-mock"
        self.latency: int = 0

    @timed
    def generate(self, prompt: str, **params):
        self.latency = 100
        return {"text": f"[MOCK OUTPUT]\n{prompt[:200]} ...", "provider": "mock", "model_version": self.version, "model_info": self.model_info, "latency": self.latency}
    

@dataclass
class GoogleAIClient(LLMClient):
    provider: Provider = Provider.GOOGLE
    model: str = "gemini-2.5-flash"
    temperature: float = 0.7
    max_tokens: int = 3000
    retries: int = 3
    backoff: float = 0.8
    context: str = ""

    def __post_init__(self):
        self.client = None
        self.config = GenerateContentConfig(
            temperature=self.temperature,
            max_output_tokens=self.max_tokens,
            )

    def _ensure_client(self):
        if self.client is None:
            api_key = os.getenv("GOOGLE_API_KEY", "")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY environment variable is not set")
            self.client = genai.Client(api_key=api_key)
            
    @timed_sync
    async def generate_async(self, prompt: str, id: str = ""):
        """Call the chat completion API with basic retries and timing.
        Returns the model's answer as plain text.
        """
        self._ensure_client()
        context_str = self.context if isinstance(self.context, str) else ""
        full_prompt = f"{context_str}\n{prompt}" if context_str else prompt

        for attempt in range(self.retries + 1):
            try:
                response = await self.client.aio.models.generate_content(#type: ignore
                    model="gemini-2.5-flash",
                    contents=full_prompt,
                    config=self.config,
                )
                print(f"finitoh async {id}")
                return (response.text, id)
            except Exception as e:
                if attempt == self.retries:
                    raise
                sleep_time = self.backoff * (2 ** attempt)
                print(f"Attempt {attempt + 1} failed: {e}. Retrying in {sleep_time:.2f} seconds...")
                await asyncio.sleep(sleep_time)
        raise RuntimeError("Failed to get a response after multiple attempts.")
    
            
    @timed
    def generate(self, prompt: str, **params):
        """Call the chat completion API with basic retries and timing.
        Returns the model's answer as plain text.
        """
        self._ensure_client()
        self.context = self.context + prompt
        full_prompt = f"{self.context}\n{prompt}" if self.context else prompt
        for attempt in range(self.retries + 1):
            try:
                response = self.client.models.generate_content(#type: ignore
                    model="gemini-2.5-flash",
                    contents=full_prompt,
                    config=self.config,
                )
                return {"text" : response.text, "model_info": {"model": self.model}, "latency": 0}
            except Exception as e:
                if attempt == self.retries:
                    raise
                sleep_time = self.backoff * (2 ** attempt)
                print(f"Attempt {attempt + 1} failed: {e}. Retrying in {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
        raise RuntimeError("Failed to get a response after multiple attempts.")
    

@dataclass
class OpenAIClient(LLMClient):
    provider: Provider = Provider.OPENAI
    model: str = "gpt-5-nano"
    temperature: float = 0.7
    max_tokens: int = 3000
    retries: int = 3
    backoff: float = 0.8
    context: str = ""

    def __post_init__(self):
        self.client = None
        self.async_client = None

    def _ensure_client(self):
        if self.client is None:
            api_key = os.getenv("OPENAI_API_KEY", "")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is not set")
            self.client = OpenAI(api_key=api_key)

    def _ensure_async_client(self):
        if self.async_client is None:
            api_key = os.getenv("OPENAI_API_KEY", "")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is not set")
            self.async_client = AsyncOpenAI(api_key=api_key)

    @timed_sync
    async def generate_async(self, prompt: str, id: str = ""):
        """Call the chat completion API with basic retries and timing.
        Returns the model's answer as plain text.
        """
        self._ensure_async_client()
        context_str = self.context if isinstance(self.context, str) else ""
        full_prompt = f"{context_str}\n{prompt}" if context_str else prompt
        for attempt in range(self.retries + 1):
            try:
                response = await self.async_client.chat.completions.create(#type: ignore
                model="gpt-5-nano",
                messages=[
                    {"role": "user", "content": full_prompt}
                ],
                )
                print(f"finitoh async {id}")
                return (response.choices[0].message.content, id)

            except Exception as e:
                if attempt == self.retries:
                    raise
                sleep_time = self.backoff * (2 ** attempt)
                print(f"Attempt {attempt + 1} failed: {e}. Retrying in {sleep_time:.2f} seconds...")
                await asyncio.sleep(sleep_time)
        raise RuntimeError("Failed to get a response after multiple attempts.")
        
    @timed
    def generate(self, prompt: str, **params):
        """Call the chat completion API with basic retries and timing.
        Returns the model's answer as plain text.
        """
        self._ensure_client()
        context_str = self.context if isinstance(self.context, str) else ""
        full_prompt = f"{context_str}\n{prompt}" if context_str else prompt

        for attempt in range(self.retries + 1):
            try:
                response = self.client.chat.completions.create(#type: ignore
                model="gpt-5-nano",
                messages=[
                    {"role": "user", "content": full_prompt}
                ],
                )
                return {"text" : response.choices[0].message.content, "model_info": {"model": self.model}, "latency": 0}#type: ignore

            except Exception as e:
                if attempt == self.retries:
                    raise
                sleep_time = self.backoff * (2 ** attempt)
                print(f"Attempt {attempt + 1} failed: {e}. Retrying in {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
        raise RuntimeError("Failed to get a response after multiple attempts.")
    

PROVIDERS = {"mock": MockLLM, "openai": OpenAIClient, "google": GoogleAIClient}