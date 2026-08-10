from __future__ import annotations

from abc import ABC, abstractmethod

from hub.app.dtos.order_participants_dto import OrderParticipants


class OrderParticipantsPort(ABC):
    """주문 당사자 조회 포트 — 구현은 order가 제공하고 main.py가 조립한다."""

    @abstractmethod
    async def get_order_participants(self, order_id: int) -> OrderParticipants | None:
        """주문의 상태·당사자 — 없으면 None."""
        ...
