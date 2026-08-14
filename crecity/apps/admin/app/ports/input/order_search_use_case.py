from __future__ import annotations

from abc import ABC, abstractmethod

from admin.app.dtos.order_search_dto import OrderSearchQuery, OrderSearchResultDto


class OrderSearchUseCase(ABC):
    """운영 주문 검색(갭 #56) — 문의가 들어왔을 때 주문을 찾는다. 읽기 전용."""

    @abstractmethod
    async def search(self, query: OrderSearchQuery) -> OrderSearchResultDto: ...
