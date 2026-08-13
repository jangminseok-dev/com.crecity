from __future__ import annotations

from abc import ABC, abstractmethod

from order.domain.entities.deliverable_entity import Deliverable, DeliverableKind


class DeliverableRepository(ABC):
    """납품물 영속성 포트 (도메인어 명명 예외) — append-only(수정·삭제 없음)."""

    @abstractmethod
    async def add(
        self,
        order_id: int,
        kind: DeliverableKind,
        file_name: str | None,
        original_name: str | None,
        url: str | None,
        caption: str | None,
    ) -> Deliverable:
        """납품물을 기록한다 — id는 새로 발급된다."""
        ...

    @abstractmethod
    async def list_by_order(self, order_id: int) -> list[Deliverable]:
        """주문의 납품물 — 등록순."""
        ...

    @abstractmethod
    async def count_by_order(self, order_id: int) -> int:
        """주문의 납품물 개수 — 제출(submit) 가능 여부 판단에 쓰인다."""
        ...
