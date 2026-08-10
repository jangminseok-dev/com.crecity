from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from order.domain.entities.ledger_entry_entity import LedgerEntryDraft
from order.domain.entities.order_entity import Order


class OrderRepository(ABC):
    """주문 영속성 포트 (도메인어 명명 예외).

    전이와 원장 기입은 반드시 같은 DB 트랜잭션이다(BOUNDARIES §1) —
    그래서 entries를 함께 받아 단일 커밋으로 저장한다.
    """

    @abstractmethod
    async def create(self, order: Order, entries: list[LedgerEntryDraft]) -> Order:
        """주문(+원장 기입)을 원자적으로 생성한다 — order.id는 무시되고 새 id가 발급된다."""
        ...

    @abstractmethod
    async def find_by_id(self, order_id: int) -> Order | None: ...

    @abstractmethod
    async def save_transition(self, order: Order, entries: list[LedgerEntryDraft]) -> None:
        """전이 결과(상태·마감)와 원장 기입을 원자적으로 저장한다."""
        ...

    @abstractmethod
    async def list_by_participant(self, user_id: int) -> list[Order]:
        """브랜드 또는 크리에이터로 참여한 주문 — 최신순."""
        ...

    @abstractmethod
    async def find_expired(self, now: datetime, limit: int) -> list[Order]:
        """마감시각이 지난 주문(PENDING_ACCEPT·IN_REVIEW) — 주기 스캔 전용."""
        ...
