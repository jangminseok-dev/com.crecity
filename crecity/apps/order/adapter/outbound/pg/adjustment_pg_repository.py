from __future__ import annotations

from sqlalchemy import exists, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from order.adapter.outbound.orm.ledger_entry_orm import LedgerEntryOrm
from order.adapter.outbound.orm.order_adjustment_orm import OrderAdjustmentOrm
from order.adapter.outbound.orm.order_orm import OrderOrm
from order.app.ports.output.adjustment_repository import AdjustmentRepository
from order.domain.entities.ledger_entry_entity import LedgerEntryDraft
from order.domain.entities.order_adjustment_entity import AdjustmentStatus, OrderAdjustment
from order.domain.entities.order_entity import Order


def _to_entity(orm: OrderAdjustmentOrm) -> OrderAdjustment:
    return OrderAdjustment(
        id=orm.id,
        order_id=orm.order_id,
        extra_amount_krw=orm.extra_amount_krw,
        reason=orm.reason,
        status=AdjustmentStatus(orm.status),
        created_at=orm.created_at,
    )


class AdjustmentPgRepository(AdjustmentRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self, order_id: int, extra_amount_krw: int, reason: str
    ) -> OrderAdjustment:
        result = await self._session.execute(
            insert(OrderAdjustmentOrm)
            .values(
                order_id=order_id,
                extra_amount_krw=extra_amount_krw,
                reason=reason,
                status=AdjustmentStatus.REQUESTED.value,
            )
            .returning(OrderAdjustmentOrm)
        )
        orm = result.scalar_one()
        await self._session.commit()
        return _to_entity(orm)

    async def find_by_id(self, adjustment_id: int) -> OrderAdjustment | None:
        orm = await self._session.get(OrderAdjustmentOrm, adjustment_id)
        return _to_entity(orm) if orm is not None else None

    async def list_by_order(self, order_id: int) -> list[OrderAdjustment]:
        result = await self._session.execute(
            select(OrderAdjustmentOrm)
            .where(OrderAdjustmentOrm.order_id == order_id)
            .order_by(OrderAdjustmentOrm.created_at.desc(), OrderAdjustmentOrm.id.desc())
        )
        return [_to_entity(orm) for orm in result.scalars()]

    async def has_pending(self, order_id: int) -> bool:
        result = await self._session.execute(
            select(
                exists().where(
                    OrderAdjustmentOrm.order_id == order_id,
                    OrderAdjustmentOrm.status == AdjustmentStatus.REQUESTED.value,
                )
            )
        )
        return bool(result.scalar())

    async def save_status(self, adjustment_id: int, status: AdjustmentStatus) -> None:
        await self._session.execute(
            update(OrderAdjustmentOrm)
            .where(OrderAdjustmentOrm.id == adjustment_id)
            .values(status=status.value)
        )
        await self._session.commit()

    async def apply_payment(
        self, adjustment_id: int, order: Order, entries: list[LedgerEntryDraft]
    ) -> None:
        # 요청 확정·주문 증액·예치 기입은 같은 스포크라 한 트랜잭션으로 묶는다(BOUNDARIES §1)
        await self._session.execute(
            update(OrderAdjustmentOrm)
            .where(OrderAdjustmentOrm.id == adjustment_id)
            .values(status=AdjustmentStatus.PAID.value)
        )
        await self._session.execute(
            update(OrderOrm).where(OrderOrm.id == order.id).values(amount_krw=order.amount_krw)
        )
        for entry in entries:
            await self._session.execute(
                insert(LedgerEntryOrm).values(
                    order_id=order.id,
                    entry_type=entry.entry_type.value,
                    user_id=entry.user_id,
                    amount_krw=entry.amount_krw,
                )
            )
        await self._session.commit()
