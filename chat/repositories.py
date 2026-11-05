"""Repository pattern: the only module that talks to the ORM.

Services depend on this interface, so storage can change (or be mocked in
tests) without touching business logic.
"""
from .models import Conversation, Message


class ConversationRepository:
    def list_for_session(self, session_key: str):
        return Conversation.objects.filter(session_key=session_key)

    def get(self, session_key: str, conversation_id) -> Conversation | None:
        try:
            return Conversation.objects.get(pk=conversation_id, session_key=session_key)
        except (Conversation.DoesNotExist, ValueError, TypeError):
            return None

    def create(self, session_key: str, title: str = "New chat") -> Conversation:
        return Conversation.objects.create(session_key=session_key, title=title[:80])

    def delete(self, conversation: Conversation) -> None:
        conversation.delete()

    def add_message(self, conversation: Conversation, role: str, content: str) -> Message:
        conversation.save(update_fields=["updated_at"])  # bump for sidebar ordering
        return Message.objects.create(conversation=conversation, role=role, content=content)

    def recent_messages(self, conversation: Conversation, limit: int) -> list[Message]:
        latest = list(conversation.messages.order_by("-created_at", "-id")[:limit])
        return latest[::-1]
