from __future__ import annotations

from abc import ABC, abstractmethod

from order.app.dtos.revision_lookup_dto import RevisionRequestResult


class RevisionRequestRepository(ABC):
    """수정 요청 이력 조회 포트(갭 #84) — 기록은 OrderRepository.save_transition이 한다."""

    @abstractmethod
    async def list_by_order(self, order_id: int) -> list[RevisionRequestResult]:
        """주문의 수정 요청 이력 — 요청순."""
        ...
