from datetime import datetime

from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from order.adapter.outbound.mappers.order_mapper import OrderMapper
from order.adapter.outbound.orm.ledger_entry_orm import LedgerEntryOrm
from order.adapter.outbound.orm.order_orm import OrderOrm
from order.app.ports.output.order_repository import OrderRepository
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

    async def create(self, order: Order, entries: list[LedgerEntryDraft]) -> Order:
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
            )
            .returning(OrderOrm)
        )
        orm = result.scalar_one()
        await self._insert_entries(orm.id, entries)
        await self._session.commit()
        return OrderMapper.to_entity(orm)

    async def find_by_id(self, order_id: int) -> Order | None:
        result = await self._session.execute(select(OrderOrm).where(OrderOrm.id == order_id))
        orm = result.scalar_one_or_none()
        return OrderMapper.to_entity(orm) if orm is not None else None

    async def save_transition(self, order: Order, entries: list[LedgerEntryDraft]) -> None:
        await self._session.execute(
            update(OrderOrm)
            .where(OrderOrm.id == order.id)
            .values(status=order.status.value, deadline_at=order.deadline_at)
        )
        await self._insert_entries(order.id, entries)
        await self._session.commit()

    async def list_by_participant(self, user_id: int) -> list[Order]:
        result = await self._session.execute(
            select(OrderOrm)
            .where((OrderOrm.brand_user_id == user_id) | (OrderOrm.creator_user_id == user_id))
            .order_by(OrderOrm.created_at.desc(), OrderOrm.id.desc())
        )
        return [OrderMapper.to_entity(orm) for orm in result.scalars()]

    async def find_expired(self, now: datetime, limit: int) -> list[Order]:
        result = await self._session.execute(
            select(OrderOrm)
            .where(OrderOrm.status.in_(_EXPIRABLE_STATUSES), OrderOrm.deadline_at < now)
            .order_by(OrderOrm.deadline_at)
            .limit(limit)
        )
        return [OrderMapper.to_entity(orm) for orm in result.scalars()]
