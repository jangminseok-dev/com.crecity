from __future__ import annotations

from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from hub.adapter.outbound.pg.outbox_pg_store import enqueue_events
from hub.app.dtos.outbox_event_dto import OutboxEvent
from order.adapter.outbound.orm.dispute_orm import DisputeOrm
from order.adapter.outbound.pg.order_pg_repository import OrderPgRepository
from order.app.ports.output.dispute_repository import DisputeRepository
from order.domain.entities.dispute_entity import Dispute, DisputeResolution, DisputeStatus
from order.domain.entities.ledger_entry_entity import LedgerEntryDraft
from order.domain.entities.order_entity import Order


def _to_entity(orm: DisputeOrm) -> Dispute:
    return Dispute(
        id=orm.id,
        order_id=orm.order_id,
        raised_by_user_id=orm.raised_by_user_id,
        reason=orm.reason,
        status=DisputeStatus(orm.status),
        resolution=DisputeResolution(orm.resolution) if orm.resolution else None,
        resolved_by_user_id=orm.resolved_by_user_id,
        created_at=orm.created_at,
        resolved_at=orm.resolved_at,
    )


class DisputePgRepository(DisputeRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(
        self, order_id: int, raised_by_user_id: int, reason: str, events: list[OutboxEvent]
    ) -> Dispute:
        result = await self._session.execute(
            insert(DisputeOrm)
            .values(
                order_id=order_id,
                raised_by_user_id=raised_by_user_id,
                reason=reason,
                status=DisputeStatus.OPEN.value,
            )
            .returning(DisputeOrm)
        )
        orm = result.scalar_one()
        enqueue_events(self._session, events)  # 신고 기록과 단일 커밋(BOUNDARIES §1)
        await self._session.commit()
        return _to_entity(orm)

    async def find_by_id(self, dispute_id: int) -> Dispute | None:
        result = await self._session.execute(
            select(DisputeOrm).where(DisputeOrm.id == dispute_id)
        )
        orm = result.scalar_one_or_none()
        return _to_entity(orm) if orm is not None else None

    async def find_open_by_order(self, order_id: int) -> Dispute | None:
        result = await self._session.execute(
            select(DisputeOrm).where(
                DisputeOrm.order_id == order_id, DisputeOrm.status == DisputeStatus.OPEN.value
            )
        )
        orm = result.scalars().first()
        return _to_entity(orm) if orm is not None else None

    async def list_by_order(self, order_id: int) -> list[Dispute]:
        result = await self._session.execute(
            select(DisputeOrm)
            .where(DisputeOrm.order_id == order_id)
            .order_by(DisputeOrm.created_at, DisputeOrm.id)
        )
        return [_to_entity(orm) for orm in result.scalars()]

    async def list_open(self) -> list[Dispute]:
        return await self.list_by_status(DisputeStatus.OPEN)

    async def list_by_status(self, status: DisputeStatus) -> list[Dispute]:
        """대기는 오래된 순, 판정 완료는 최근 순(갭 #71 — 최근 판단부터 본다)."""
        statement = select(DisputeOrm).where(DisputeOrm.status == status.value)
        statement = (
            statement.order_by(DisputeOrm.created_at, DisputeOrm.id)
            if status is DisputeStatus.OPEN
            else statement.order_by(DisputeOrm.resolved_at.desc(), DisputeOrm.id.desc())
        )
        result = await self._session.execute(statement)
        return [_to_entity(orm) for orm in result.scalars()]

    async def resolve(
        self,
        dispute: Dispute,
        order: Order | None,
        entries: list[LedgerEntryDraft],
        events: list[OutboxEvent],
    ) -> Dispute:
        await self._session.execute(
            update(DisputeOrm)
            .where(DisputeOrm.id == dispute.id)
            .values(
                status=dispute.status.value,
                resolution=dispute.resolution.value if dispute.resolution else None,
                resolved_by_user_id=dispute.resolved_by_user_id,
                resolved_at=dispute.resolved_at,
            )
        )
        if order is None:
            await self._session.commit()  # 기각 — 주문은 그대로
        else:
            # 같은 세션이므로 분쟁 갱신까지 함께 커밋된다(BOUNDARIES §1)
            await OrderPgRepository(self._session).save_transition(order, entries, events)
        return dispute
