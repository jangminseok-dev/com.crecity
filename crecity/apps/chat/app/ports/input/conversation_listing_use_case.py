from __future__ import annotations

from abc import ABC, abstractmethod

from chat.app.dtos.conversation_listing_dto import ConversationResult


class ConversationListingUseCase(ABC):
    """대화 목록·상세 유스케이스 — 참여자 본인 것만."""

    @abstractmethod
    async def list_mine(self, user_id: int) -> list[ConversationResult]:
        """내 대화 목록 — 마지막 메시지 시각 내림차순."""
        ...

    @abstractmethod
    async def get_conversation(self, conversation_id: int, requester_user_id: int) -> ConversationResult:
        """대화방 상세(헤더 표시용).

        Raises:
            ConversationNotFoundError · NotParticipantError(도메인, 403)
        """
        ...
