from __future__ import annotations

from sqlalchemy import func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from order.adapter.outbound.orm.deliverable_orm import DeliverableOrm
from order.app.ports.output.deliverable_repository import DeliverableRepository
from order.domain.entities.deliverable_entity import Deliverable, DeliverableKind


def _to_entity(orm: DeliverableOrm) -> Deliverable:
    return Deliverable(
        id=orm.id,
        order_id=orm.order_id,
        kind=DeliverableKind(orm.kind),
        file_name=orm.file_name,
        original_name=orm.original_name,
        url=orm.url,
        caption=orm.caption,
        created_at=orm.created_at,
    )


class DeliverablePgRepository(DeliverableRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(
        self,
        order_id: int,
        kind: DeliverableKind,
        file_name: str | None,
        original_name: str | None,
        url: str | None,
        caption: str | None,
    ) -> Deliverable:
        result = await self._session.execute(
            insert(DeliverableOrm)
            .values(
                order_id=order_id,
                kind=kind.value,
                file_name=file_name,
                original_name=original_name,
                url=url,
                caption=caption,
            )
            .returning(DeliverableOrm)
        )
        orm = result.scalar_one()
        await self._session.commit()
        return _to_entity(orm)

    async def list_by_order(self, order_id: int) -> list[Deliverable]:
        result = await self._session.execute(
            select(DeliverableOrm)
            .where(DeliverableOrm.order_id == order_id)
            .order_by(DeliverableOrm.created_at, DeliverableOrm.id)
        )
        return [_to_entity(orm) for orm in result.scalars()]

    async def count_by_order(self, order_id: int) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(DeliverableOrm)
            .where(DeliverableOrm.order_id == order_id)
        )
        return int(result.scalar_one())
