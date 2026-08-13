from __future__ import annotations

from abc import ABC, abstractmethod

from hub.app.dtos.outbox_event_dto import OutboxEvent
from order.domain.entities.dispute_entity import Dispute
from order.domain.entities.ledger_entry_entity import LedgerEntryDraft
from order.domain.entities.order_entity import Order


class DisputeRepository(ABC):
    """분쟁 영속성 포트 (도메인어 명명 예외).

    판정은 분쟁 갱신 + 주문 전이 + 원장 기입 + 이벤트가 반드시 같은 트랜잭션이다
    (BOUNDARIES §1) — 그래서 resolve가 넷을 함께 받는다.
    """

    @abstractmethod
    async def add(
        self, order_id: int, raised_by_user_id: int, reason: str, events: list[OutboxEvent]
    ) -> Dispute:
        """분쟁을 OPEN 상태로 기록한다(알림 이벤트와 단일 커밋) — id는 새로 발급된다."""
        ...

    @abstractmethod
    async def find_by_id(self, dispute_id: int) -> Dispute | None: ...

    @abstractmethod
    async def find_open_by_order(self, order_id: int) -> Dispute | None:
        """주문의 처리 대기 분쟁 — 중복 신고 차단·자동 승인 보류 판단에 쓰인다."""
        ...

    @abstractmethod
    async def list_by_order(self, order_id: int) -> list[Dispute]:
        """주문의 분쟁 이력 — 등록순."""
        ...

    @abstractmethod
    async def list_open(self) -> list[Dispute]:
        """처리 대기 분쟁 전체 — 오래된 순(운영 처리용)."""
        ...

    @abstractmethod
    async def resolve(
        self,
        dispute: Dispute,
        order: Order | None,
        entries: list[LedgerEntryDraft],
        events: list[OutboxEvent],
    ) -> Dispute:
        """판정을 저장한다 — order가 있으면 주문 전이·원장·이벤트까지 단일 커밋.

        기각(DISMISS)은 주문을 건드리지 않으므로 order=None으로 호출한다.
        """
        ...
