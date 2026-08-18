from datetime import datetime, timedelta

from sqlalchemy import func, insert, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from hub.adapter.outbound.pg.outbox_pg_store import enqueue_events
from hub.app.dtos.outbox_event_dto import OutboxEvent
from order.adapter.outbound.mappers.order_mapper import OrderMapper
from order.adapter.outbound.orm.dispute_orm import DisputeOrm
from order.adapter.outbound.orm.ledger_entry_orm import LedgerEntryOrm
from order.adapter.outbound.orm.order_orm import OrderOrm
from order.adapter.outbound.orm.order_status_transition_orm import OrderStatusTransitionOrm
from order.adapter.outbound.pg.ledger_pg_repository import _SIGNED_AMOUNT
from order.app.dtos.party_stats_dto import PartyTradeStats
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
        # 전이 이력(갭 #79) — from은 저장 시점의 DB 상태를 읽는다(엔티티의 옛 상태보다 정확).
        # 상태가 실제로 바뀐 저장만 이력이 된다(취소 요청 등 상태 유지 저장은 제외).
        current = await self._session.execute(
            select(OrderOrm.status).where(OrderOrm.id == order.id)
        )
        from_status = current.scalar_one()
        if from_status != order.status.value:
            await self._session.execute(
                insert(OrderStatusTransitionOrm).values(
                    order_id=order.id,
                    from_status=from_status,
                    to_status=order.status.value,
                )
            )
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

    async def get_party_stats(self, user_id: int, as_brand: bool) -> PartyTradeStats:
        """상태별 건수와 수정 횟수 합을 한 번에 센다 — 화면마다 다시 훑지 않게."""
        party_column = OrderOrm.brand_user_id if as_brand else OrderOrm.creator_user_id
        row = (
            await self._session.execute(
                select(
                    func.count(),
                    func.count().filter(OrderOrm.status == OrderStatus.COMPLETED.value),
                    func.count().filter(OrderOrm.status == OrderStatus.CANCELLED.value),
                    func.count().filter(OrderOrm.status == OrderStatus.REFUNDED.value),
                    func.count().filter(OrderOrm.accept_expired.is_(True)),
                    func.coalesce(func.sum(OrderOrm.revisions_used), 0),
                ).where(party_column == user_id)
            )
        ).one()
        return PartyTradeStats(
            total_orders=int(row[0]),
            completed_orders=int(row[1]),
            cancelled_orders=int(row[2]),
            refunded_orders=int(row[3]),
            accept_expired_orders=int(row[4]),
            total_revisions=int(row[5]),
        )

    async def find_deadline_warning_targets(
        self, now: datetime, threshold: timedelta, limit: int
    ) -> list[Order]:
        result = await self._session.execute(
            select(OrderOrm)
            .where(
                OrderOrm.status.in_(
                    (OrderStatus.PENDING_ACCEPT.value, OrderStatus.IN_REVIEW.value)
                ),
                OrderOrm.deadline_warned_at.is_(None),
                OrderOrm.deadline_at.is_not(None),
                OrderOrm.deadline_at > now,
                OrderOrm.deadline_at <= now + threshold,
            )
            .order_by(OrderOrm.deadline_at.asc())
            .limit(limit)
        )
        return [OrderMapper.to_entity(orm) for orm in result.scalars()]

    async def record_deadline_warnings(
        self, order_ids: list[int], now: datetime, events: list[OutboxEvent]
    ) -> None:
        if not order_ids:
            return
        await self._session.execute(
            update(OrderOrm).where(OrderOrm.id.in_(order_ids)).values(deadline_warned_at=now)
        )
        enqueue_events(self._session, events)  # 커밋은 아래에서 함께(단일 트랜잭션)
        await self._session.commit()

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
