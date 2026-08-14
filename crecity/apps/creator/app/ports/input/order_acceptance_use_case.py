from __future__ import annotations

from abc import ABC, abstractmethod

from creator.app.dtos.order_acceptance_dto import OrderAcceptanceCommand, OrderAcceptanceResult


class OrderAcceptanceUseCase(ABC):
    """주문 수신 전환(갭 #64) — 휴가·마감 중 무응답 페널티(갭 #32)를 피하는 수단."""

    @abstractmethod
    async def set_accepting(self, command: OrderAcceptanceCommand) -> OrderAcceptanceResult: ...
