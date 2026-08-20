from __future__ import annotations

from abc import ABC, abstractmethod

from chat.app.dtos.conversation_listing_dto import ConversationResult
from chat.app.dtos.order_conversation_dto import OpenOrderConversationCommand


class OrderConversationUseCase(ABC):
    """주문 당사자 간 대화 열기(갭 #95) — 주문 상세의 '대화 열기'."""

    @abstractmethod
    async def open(self, command: OpenOrderConversationCommand) -> ConversationResult: ...
