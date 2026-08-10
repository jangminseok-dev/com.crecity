from __future__ import annotations

from abc import ABC, abstractmethod

from chat.app.dtos.courier_dto import CourierQuery, CourierResponse


class CourierUseCase(ABC):
    """채팅 (chat) 유스케이스 — 주문 전 협상 메시징 담당."""

    @abstractmethod
    async def introduce_myself(self, query: CourierQuery) -> CourierResponse:
        """채팅 (chat)의 자기소개 메소드."""
        ...
