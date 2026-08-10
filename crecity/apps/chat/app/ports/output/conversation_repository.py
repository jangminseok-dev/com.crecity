from __future__ import annotations

from abc import ABC, abstractmethod

from chat.domain.entities.conversation_entity import Conversation


class ConversationRepository(ABC):
    """대화방 영속성 포트 (도메인어 명명 예외)."""

    @abstractmethod
    async def create(self, brand_user_id: int, creator_user_id: int) -> Conversation: ...

    @abstractmethod
    async def find_by_pair(self, brand_user_id: int, creator_user_id: int) -> Conversation | None: ...

    @abstractmethod
    async def find_by_id(self, conversation_id: int) -> Conversation | None: ...

    @abstractmethod
    async def list_by_participant(self, user_id: int) -> list[Conversation]: ...
