from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from order.adapter.outbound.orm.order_revision_request_orm import OrderRevisionRequestOrm
from order.app.dtos.revision_lookup_dto import RevisionRequestResult
from order.app.ports.output.revision_request_repository import RevisionRequestRepository


class RevisionRequestPgRepository(RevisionRequestRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_order(self, order_id: int) -> list[RevisionRequestResult]:
        result = await self._session.execute(
            select(OrderRevisionRequestOrm)
            .where(OrderRevisionRequestOrm.order_id == order_id)
            .order_by(OrderRevisionRequestOrm.id)
        )
        return [
            RevisionRequestResult(
                id=orm.id,
                requested_in=orm.requested_in,
                comment=orm.comment,
                created_at=orm.created_at,
            )
            for orm in result.scalars()
        ]
