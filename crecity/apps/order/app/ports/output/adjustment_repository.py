from __future__ import annotations

from abc import ABC, abstractmethod

from order.domain.entities.ledger_entry_entity import LedgerEntryDraft
from order.domain.entities.order_adjustment_entity import AdjustmentStatus, OrderAdjustment
from order.domain.entities.order_entity import Order


class AdjustmentRepository(ABC):
    """금액 변경 요청 영속성 포트."""

    @abstractmethod
    async def create(
        self, order_id: int, extra_amount_krw: int, reason: str
    ) -> OrderAdjustment: ...

    @abstractmethod
    async def find_by_id(self, adjustment_id: int) -> OrderAdjustment | None: ...

    @abstractmethod
    async def list_by_order(self, order_id: int) -> list[OrderAdjustment]:
        """주문의 요청 이력 — 최신순."""
        ...

    @abstractmethod
    async def has_pending(self, order_id: int) -> bool:
        """대기 중(REQUESTED) 요청 존재 여부 — 중복 요청 차단."""
        ...

    @abstractmethod
    async def save_status(self, adjustment_id: int, status: AdjustmentStatus) -> None: ...

    @abstractmethod
    async def apply_payment(
        self, adjustment_id: int, order: Order, entries: list[LedgerEntryDraft]
    ) -> None:
        """추가 결제 반영 — 요청 PAID + 주문 금액 증액 + 예치 기입을 **단일 트랜잭션**으로."""
        ...
