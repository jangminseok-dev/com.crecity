from __future__ import annotations

from abc import ABC, abstractmethod

from chat.domain.entities.conversation_entity import Message


class MessageRepository(ABC):
    """메시지 영속성 포트 — append-only(분쟁 근거 보존)."""

    @abstractmethod
    async def create(self, conversation_id: int, sender_user_id: int, body: str) -> Message: ...

    @abstractmethod
    async def list_by_conversation(self, conversation_id: int, limit: int) -> list[Message]:
        """오래된 순 최근 limit개."""
        ...

    @abstractmethod
    async def last_by_conversation(self, conversation_id: int) -> Message | None: ...
