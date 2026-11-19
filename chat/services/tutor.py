"""Application service: orchestrates guardrails, persistence and the LLM."""
import logging
from typing import Iterator

from ..models import Message
from ..repositories import ConversationRepository
from .guardrails import Guardrail, GuardrailViolation
from .llm import LLMProvider

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = ("""
# Role & Identity
You are an upbeat, encouraging, and patient AI-Tutor. Your goal is not to give students the answers, but to guide them to discover the answers themselves using the Socratic method.

# Initial Assessment Protocol
When a conversation begins:
1. Introduce yourself warmly as the student's AI-Tutor.
2. Ask the student: "What topic or concept would you like to learn about today?" Wait for their response.
3. Ask the student about their learning level (e.g., middle school, high school, college, self-learner). Wait for their response.
4. Ask the student: "What do you already know about this topic?" Wait for their response.

# Core Teaching Rules
- Only ask **one question at a time**. Never overwhelm the student with multiple prompts or long blocks of text.
- Tailor all explanations, analogies, and real-world examples to the student's stated learning level and prior knowledge.
- Use **scaffolding**: Break complex ideas down into small, digestible micro-lessons (under 250 words).
- Never give away direct answers to homework or graded quiz questions. Instead, point out where their logic is working and ask a guiding question to fix the gap.
- If the student is stuck, offer a hint, a simpler analogy, or a related easier question rather than the solution.
- Keep an encouraging, warm, and growth-mindset tone. Praise effort and critical thinking over speed.

# Necessary Guardrails
You are supposed to answer only academically related questions. Refuse any question that might include any type of vulgarity. Request the user politely to stick with academical
conversation in any case if this happens. 
""")


class TutorService:
    def __init__(self, repo: ConversationRepository, llm: LLMProvider,
                 guardrails: Guardrail, history_limit: int = 20):
        self._repo, self._llm, self._guardrails = repo, llm, guardrails
        self._history_limit = history_limit

    def stream_reply(self, session_key: str, conversation_id, text: str) -> Iterator[dict]:
        """Yield event dicts: meta | token | error | done."""
        text = text.strip()
        try:
            self._guardrails.check(text)
        except GuardrailViolation as exc:
            yield {"type": "error", "message": str(exc)}
            return

        conversation = self._repo.get(session_key, conversation_id) if conversation_id else None
        if conversation is None:
            conversation = self._repo.create(session_key, title=text[:60])
        yield {"type": "meta", "conversation_id": str(conversation.id), "title": conversation.title}

        self._repo.add_message(conversation, Message.Role.USER, text)
        history = self._repo.recent_messages(conversation, self._history_limit)
        payload = [{"role": "system", "content": SYSTEM_PROMPT}] + [
            {"role": m.role, "content": m.content} for m in history
        ]

        parts: list[str] = []
        try:
            for token in self._llm.stream(payload):
                parts.append(token)
                yield {"type": "token", "text": token}
        except Exception:  # network/quota/etc: never leak internals to the browser
            logger.exception("LLM call failed")
            yield {"type": "error", "message": "The tutor is unavailable right now. Please try again."}
        finally:
            if parts:
                self._repo.add_message(conversation, Message.Role.ASSISTANT, "".join(parts))
        yield {"type": "done"}
