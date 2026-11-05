"""Chain of Responsibility: each guardrail validates, then hands off to the next."""
from abc import ABC, abstractmethod

from .llm import LLMProvider


class GuardrailViolation(Exception):
    """Raised with a user-safe message when input is rejected."""


class Guardrail(ABC):
    def __init__(self):
        self._next: Guardrail | None = None

    def set_next(self, nxt: "Guardrail") -> "Guardrail":
        self._next = nxt
        return nxt

    def check(self, text: str) -> None:
        self._validate(text)
        if self._next:
            self._next.check(text)

    @abstractmethod
    def _validate(self, text: str) -> None: ...


class LengthGuardrail(Guardrail):
    def __init__(self, max_chars: int):
        super().__init__()
        self._max = max_chars

    def _validate(self, text):
        if not text.strip():
            raise GuardrailViolation("Type a question first.")
        if len(text) > self._max:
            raise GuardrailViolation(f"Keep messages under {self._max} characters.")


class PromptInjectionGuardrail(Guardrail):
    PATTERNS = ("ignore previous instructions", "ignore all previous", "reveal your system prompt")

    def _validate(self, text):
        lowered = text.lower()
        if any(p in lowered for p in self.PATTERNS):
            raise GuardrailViolation("That request tries to override the tutor's instructions.")


class ModerationGuardrail(Guardrail):
    def __init__(self, provider: LLMProvider):
        super().__init__()
        self._provider = provider

    def _validate(self, text):
        if self._provider.is_flagged(text):
            raise GuardrailViolation("That message was flagged by content moderation.")


def build_input_chain(provider: LLMProvider, max_chars: int) -> Guardrail:
    head = LengthGuardrail(max_chars)
    head.set_next(PromptInjectionGuardrail()).set_next(ModerationGuardrail(provider))
    return head
