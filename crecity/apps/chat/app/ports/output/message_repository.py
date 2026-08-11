from __future__ import annotations

from abc import ABC, abstractmethod

from chat.domain.entities.conversation_entity import Message


class MessageRepository(ABC):
    """메시지 영속성 포트 — append-only(분쟁 근거 보존)."""

    @abstractmethod
    async def create(
        self,
        conversation_id: int,
        sender_user_id: int,
        body: str,
        image_file_name: str | None = None,
    ) -> Message: ...

    @abstractmethod
    async def list_by_conversation(self, conversation_id: int, limit: int) -> list[Message]:
        """오래된 순 최근 limit개."""
        ...

    @abstractmethod
    async def last_by_conversation(self, conversation_id: int) -> Message | None: ...

    @abstractmethod
    async def unread_counts(self, user_id: int, conversation_ids: list[int]) -> dict[int, int]:
        """대화방별 안 읽음 수(갭 #35) — 읽음 시각 이후 도착한 상대 메시지만 센다."""
        ...

    @abstractmethod
    async def mark_read(self, conversation_id: int, user_id: int) -> None:
        """대화방을 지금 시각으로 읽음 처리(없으면 생성)."""
        ...
