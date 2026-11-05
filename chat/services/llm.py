"""Strategy + Adapter: the app depends on LLMProvider, not on OpenAI directly."""
from abc import ABC, abstractmethod
from typing import Iterator

from openai import OpenAI


class LLMProvider(ABC):
    @abstractmethod
    def stream(self, messages: list[dict]) -> Iterator[str]:
        """Yield response text chunks."""

    @abstractmethod
    def is_flagged(self, text: str) -> bool:
        """Return True if the text violates content policy."""


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str, max_tokens: int = 900):
        self._client = OpenAI(api_key=api_key)
        self._model = model
        self._max_tokens = max_tokens

    def stream(self, messages):
        response = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            stream=True,
            temperature=0.4,
            max_tokens=self._max_tokens,
        )
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def is_flagged(self, text):
        result = self._client.moderations.create(model="omni-moderation-latest", input=text)
        return result.results[0].flagged
