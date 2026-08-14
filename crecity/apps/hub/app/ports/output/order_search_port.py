from __future__ import annotations

from abc import ABC, abstractmethod

from hub.app.dtos.order_search_dto import OrderSearchCriteria, OrderSearchResult


class OrderSearchPort(ABC):
    """운영 주문 검색 포트 — 구현은 order가 제공한다(문의 대응용, 갭 #56).

    주문의 소유자는 order다 — admin은 이 계약으로만 들여다보며 상태를 바꾸지 않는다
    (전이는 분쟁 판정 `DisputeResolutionPort` 같은 별도 계약으로만).
    """

    @abstractmethod
    async def search_orders(self, criteria: OrderSearchCriteria) -> OrderSearchResult: ...
