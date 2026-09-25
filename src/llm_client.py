"""LLM abstraction so agents don't care which backend answers them.

Swaps between a real LLM-backed client (Anthropic or OpenAI) and a
dependency-free fallback, so the whole system still runs end-to-end
without an API key (tests and first-run demos), while using a real model
whenever one is configured.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from src import config


class LLMClient(ABC):
    @abstractmethod
    def complete(self, prompt: str, system: Optional[str] = None) -> str:
        """Return a text completion for the given prompt."""


class AnthropicLLMClient(LLMClient):
    def __init__(self, model: str = config.ANTHROPIC_MODEL):
        from anthropic import Anthropic

        self._client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
        self._model = model

    def complete(self, prompt: str, system: Optional[str] = None) -> str:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            temperature=0.2,
            system=system or "",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()


class OpenAILLMClient(LLMClient):
    def __init__(self, model: str = config.OPENAI_CHAT_MODEL):
        from openai import OpenAI

        self._client = OpenAI(api_key=config.OPENAI_API_KEY)
        self._model = model

    def complete(self, prompt: str, system: Optional[str] = None) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        response = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()


class FallbackLLMClient(LLMClient):
    """No-network stand-in used when no API key is configured.

    It does not "generate" in any real sense -- it just formats whatever
    context it was given so the rest of the pipeline (retrieval, SQL
    execution, routing, citations) is still exercised end-to-end.
    """

    def complete(self, prompt: str, system: Optional[str] = None) -> str:
        return (
            "[No LLM configured -- set ANTHROPIC_API_KEY or OPENAI_API_KEY "
            f"for generated answers]\n{prompt}"
        )


def get_llm_client() -> LLMClient:
    if config.ANTHROPIC_API_KEY:
        return AnthropicLLMClient()
    if config.OPENAI_API_KEY:
        return OpenAILLMClient()
    return FallbackLLMClient()
