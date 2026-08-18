from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timedelta

from hub.app.dtos.outbox_event_dto import OutboxEvent
from order.app.dtos.party_stats_dto import PartyTradeStats
from order.domain.entities.ledger_entry_entity import LedgerEntryDraft
from order.domain.entities.order_entity import Order


class OrderRepository(ABC):
    """주문 영속성 포트 (도메인어 명명 예외).

    전이·원장 기입·Outbox 이벤트는 반드시 같은 DB 트랜잭션이다(BOUNDARIES §1) —
    그래서 entries·events를 함께 받아 단일 커밋으로 저장한다.
    """

    @abstractmethod
    async def create(
        self,
        order: Order,
        entries: list[LedgerEntryDraft],
        events: list[OutboxEvent],
        credit_spend: LedgerEntryDraft | None = None,
    ) -> Order | None:
        """주문(+원장 기입+이벤트)을 원자적으로 생성한다 — order.id는 새로 발급된다.

        credit_spend(크레딧 차감 기입)가 있으면 advisory lock으로 잔액을 재검증한 뒤
        함께 기입한다 — 잔액 부족이면 아무것도 저장하지 않고 None(호출자가 보정).
        """
        ...

    @abstractmethod
    async def create_many(
        self,
        drafts: list[tuple[Order, list[LedgerEntryDraft], list[OutboxEvent]]],
        credit_spend: LedgerEntryDraft | None = None,
    ) -> list[Order] | None:
        """여러 주문(+각 원장 기입+이벤트)을 **단일 트랜잭션**으로 생성한다(장바구니 §3.8).

        credit_spend가 있으면 create와 동일하게 advisory lock 잔액 재검증 후 함께 기입 —
        부족하면 아무것도 저장하지 않고 None.
        """
        ...

    @abstractmethod
    async def find_by_id(self, order_id: int) -> Order | None: ...

    @abstractmethod
    async def save_transition(
        self,
        order: Order,
        entries: list[LedgerEntryDraft],
        events: list[OutboxEvent],
        revision_comment: str | None = None,
    ) -> None:
        """전이 결과(상태·마감)·원장 기입·이벤트를 원자적으로 저장한다.

        revision_comment(갭 #84)가 있으면 수정 요청 이력도 **같은 트랜잭션**으로 남긴다 —
        갈라지면 횟수만 늘고 피드백이 없는 요청이 생긴다.
        """
        ...

    @abstractmethod
    async def list_by_participant(self, user_id: int) -> list[Order]:
        """브랜드 또는 크리에이터로 참여한 주문 — 최신순."""
        ...

    @abstractmethod
    async def get_party_stats(self, user_id: int, as_brand: bool) -> PartyTradeStats:
        """당사자 거래 이력 집계(갭 #65·#66) — as_brand면 브랜드로 참여한 주문 기준."""
        ...

    @abstractmethod
    async def find_deadline_warning_targets(
        self, now: datetime, threshold: timedelta, limit: int
    ) -> list[Order]:
        """마감이 임계 안으로 들어왔고 아직 알리지 않은 주문(갭 #76)."""
        ...

    @abstractmethod
    async def record_deadline_warnings(
        self, order_ids: list[int], now: datetime, events: list[OutboxEvent]
    ) -> None:
        """임박 표식과 알림 이벤트를 **한 트랜잭션으로** 남긴다.

        따로 커밋하면 표식만 남고 알림이 안 가거나(영영 못 받음), 알림만 가고 표식이
        없어 매 주기 중복 발송된다.
        """
        ...

    @abstractmethod
    async def find_expired(self, now: datetime, limit: int) -> list[Order]:
        """마감시각이 지난 주문(PENDING_ACCEPT·IN_REVIEW) — 주기 스캔 전용."""
        ...
