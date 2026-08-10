from __future__ import annotations

from abc import ABC, abstractmethod

from order.app.dtos.order_lookup_dto import MyOrdersQuery, OrderDetailQuery
from order.app.dtos.order_result_dto import OrderResult


class OrderLookupUseCase(ABC):
    """주문 조회 유스케이스 — 주문은 당사자(브랜드·크리에이터)에게만 보인다."""

    @abstractmethod
    async def list_my_orders(self, query: MyOrdersQuery) -> list[OrderResult]:
        """내가 참여한 주문 — 최신순."""
        ...

    @abstractmethod
    async def get_order(self, query: OrderDetailQuery) -> OrderResult:
        """주문 상세.

        Raises:
            OrderNotFoundError: 주문 없음.
            NotOrderParticipantError: 당사자 아님.
        """
        ...
