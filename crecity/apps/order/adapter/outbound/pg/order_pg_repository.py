from datetime import datetime

from sqlalchemy import func, insert, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from hub.adapter.outbound.pg.outbox_pg_store import enqueue_events
from hub.app.dtos.outbox_event_dto import OutboxEvent
from order.adapter.outbound.mappers.order_mapper import OrderMapper
from order.adapter.outbound.orm.dispute_orm import DisputeOrm
from order.adapter.outbound.orm.ledger_entry_orm import LedgerEntryOrm
from order.adapter.outbound.orm.order_orm import OrderOrm
from order.adapter.outbound.pg.ledger_pg_repository import _SIGNED_AMOUNT
from order.app.ports.output.order_repository import OrderRepository
from order.domain.entities.dispute_entity import DisputeStatus
from order.domain.entities.ledger_entry_entity import LedgerEntryDraft
from order.domain.entities.order_entity import Order, OrderStatus

# 만료 스캔 대상 상태 — deadline_at을 갖는 상태만
_EXPIRABLE_STATUSES = (OrderStatus.PENDING_ACCEPT.value, OrderStatus.IN_REVIEW.value)


class OrderPgRepository(OrderRepository):
    """전이+원장 기입을 단일 커밋으로 저장한다(BOUNDARIES §1 — 같은 스포크, 같은 트랜잭션)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _insert_entries(self, order_id: int, entries: list[LedgerEntryDraft]) -> None:
        for entry in entries:
            await self._session.execute(
                insert(LedgerEntryOrm).values(
                    order_id=order_id,
                    entry_type=entry.entry_type.value,
                    user_id=entry.user_id,
                    amount_krw=entry.amount_krw,
                )
            )

    async def _has_credit_balance(self, credit_spend: LedgerEntryDraft) -> bool:
        """advisory lock 후 잔액 재검증 — 동시 사용(인출·중복 결제)의 초과 차감을 차단한다."""
        await self._session.execute(
            text("SELECT pg_advisory_xact_lock(:key)").bindparams(key=credit_spend.user_id)
        )
        balance = await self._session.execute(
            select(func.coalesce(func.sum(_SIGNED_AMOUNT), 0)).where(
                LedgerEntryOrm.user_id == credit_spend.user_id
            )
        )
        return int(balance.scalar_one()) >= credit_spend.amount_krw

    async def _insert_order(
        self, order: Order, entries: list[LedgerEntryDraft], events: list[OutboxEvent]
    ) -> OrderOrm:
        """주문 1건 + 원장 기입 + 이벤트를 세션에 적재한다(커밋은 호출자 몫)."""
        result = await self._session.execute(
            insert(OrderOrm)
            .values(
                package_id=order.package_id,
                package_title=order.package_title,
                brand_user_id=order.brand_user_id,
                creator_user_id=order.creator_user_id,
                amount_krw=order.amount_krw,
                brand_fee_percent=order.brand_fee_percent,
                creator_fee_percent=order.creator_fee_percent,
                requirements=order.requirements,
                status=order.status.value,
                deadline_at=order.deadline_at,
                revision_limit=order.revision_limit,
                revisions_used=order.revisions_used,
                usage_rights=order.usage_rights,
            )
            .returning(OrderOrm)
        )
        orm = result.scalar_one()
        await self._insert_entries(orm.id, entries)
        # 이벤트 payload에 발급된 주문 id를 채워 같은 트랜잭션에 적재한다
        enqueue_events(
            self._session,
            [OutboxEvent(e.event_type, {**e.payload, "order_id": orm.id}) for e in events],
        )
        return orm

    async def create(
        self,
        order: Order,
        entries: list[LedgerEntryDraft],
        events: list[OutboxEvent],
        credit_spend: LedgerEntryDraft | None = None,
    ) -> Order | None:
        if credit_spend is not None:
            if not await self._has_credit_balance(credit_spend):
                await self._session.rollback()
                return None
            entries = [*entries, credit_spend]
        orm = await self._insert_order(order, entries, events)
        await self._session.commit()
        return OrderMapper.to_entity(orm)

    async def create_many(
        self,
        drafts: list[tuple[Order, list[LedgerEntryDraft], list[OutboxEvent]]],
        credit_spend: LedgerEntryDraft | None = None,
    ) -> list[Order] | None:
        if credit_spend is not None and not await self._has_credit_balance(credit_spend):
            await self._session.rollback()
            return None
        orms = []
        for index, (order, entries, events) in enumerate(drafts):
            # 크레딧 차감은 결제 1건 몫 — 감사 추적을 위해 배치의 첫 주문에 귀속시킨다
            if index == 0 and credit_spend is not None:
                entries = [*entries, credit_spend]
            orms.append(await self._insert_order(order, entries, events))
        await self._session.commit()
        return [OrderMapper.to_entity(orm) for orm in orms]

    async def find_by_id(self, order_id: int) -> Order | None:
        result = await self._session.execute(select(OrderOrm).where(OrderOrm.id == order_id))
        orm = result.scalar_one_or_none()
        return OrderMapper.to_entity(orm) if orm is not None else None

    async def save_transition(
        self, order: Order, entries: list[LedgerEntryDraft], events: list[OutboxEvent]
    ) -> None:
        await self._session.execute(
            update(OrderOrm)
            .where(OrderOrm.id == order.id)
            .values(
                status=order.status.value,
                deadline_at=order.deadline_at,
                cancel_requested_by=order.cancel_requested_by,
                revisions_used=order.revisions_used,
                accept_expired=order.accept_expired,
            )
        )
        await self._insert_entries(order.id, entries)
        enqueue_events(self._session, events)  # 전이·원장과 단일 커밋(BOUNDARIES §1)
        await self._session.commit()

    async def list_by_participant(self, user_id: int) -> list[Order]:
        result = await self._session.execute(
            select(OrderOrm)
            .where((OrderOrm.brand_user_id == user_id) | (OrderOrm.creator_user_id == user_id))
            .order_by(OrderOrm.created_at.desc(), OrderOrm.id.desc())
        )
        return [OrderMapper.to_entity(orm) for orm in result.scalars()]

    async def find_expired(self, now: datetime, limit: int) -> list[Order]:
        # 처리 대기 분쟁이 있으면 만료 처리(자동 승인·환불)를 보류한다 — 판정이 우선(갭 #4)
        open_dispute = (
            select(DisputeOrm.id)
            .where(
                DisputeOrm.order_id == OrderOrm.id,
                DisputeOrm.status == DisputeStatus.OPEN.value,
            )
            .exists()
        )
        result = await self._session.execute(
            select(OrderOrm)
            .where(
                OrderOrm.status.in_(_EXPIRABLE_STATUSES),
                OrderOrm.deadline_at < now,
                ~open_dispute,
            )
            .order_by(OrderOrm.deadline_at)
            .limit(limit)
        )
        return [OrderMapper.to_entity(orm) for orm in result.scalars()]
