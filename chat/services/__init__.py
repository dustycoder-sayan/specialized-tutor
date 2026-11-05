from functools import lru_cache

from django.conf import settings

from ..repositories import ConversationRepository
from .guardrails import build_input_chain
from .llm import OpenAIProvider
from .tutor import TutorService


@lru_cache(maxsize=1)
def get_tutor_service() -> TutorService:
    """Composition root: the one place where concrete classes are wired together."""
    provider = OpenAIProvider(settings.OPENAI_API_KEY, settings.OPENAI_MODEL,
                              settings.TUTOR_MAX_OUTPUT_TOKENS)
    return TutorService(
        repo=ConversationRepository(),
        llm=provider,
        guardrails=build_input_chain(provider, settings.TUTOR_MAX_INPUT_CHARS),
        history_limit=settings.TUTOR_HISTORY_LIMIT,
    )
