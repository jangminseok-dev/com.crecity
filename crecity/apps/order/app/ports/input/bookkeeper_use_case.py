from __future__ import annotations

from abc import ABC, abstractmethod

from order.app.dtos.bookkeeper_dto import BookkeeperQuery, BookkeeperResponse


class BookkeeperUseCase(ABC):
    """주문 (order) 유스케이스 — 주문 상태머신·에스크로/잔액 원장 담당."""

    @abstractmethod
    async def introduce_myself(self, query: BookkeeperQuery) -> BookkeeperResponse:
        """주문 (order)의 자기소개 메소드."""
        ...
