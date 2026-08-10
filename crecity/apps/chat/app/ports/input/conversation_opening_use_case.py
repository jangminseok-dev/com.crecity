from __future__ import annotations

from abc import ABC, abstractmethod

from chat.app.dtos.conversation_listing_dto import ConversationResult
from chat.app.dtos.conversation_opening_dto import OpenConversationCommand


class ConversationOpeningUseCase(ABC):
    """대화 시작 유스케이스 — 브랜드가 크리에이터에게 문의(쌍당 1개, 있으면 재사용)."""

    @abstractmethod
    async def open(self, command: OpenConversationCommand) -> ConversationResult:
        """대화방을 만들거나 기존 방을 돌려준다.

        Raises:
            NotBrandAccountError · CreatorNotFoundError
        """
        ...
