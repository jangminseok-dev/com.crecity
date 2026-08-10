from __future__ import annotations

from core.database import session_scope
from hub.app.dtos.order_participants_dto import OrderParticipants
from hub.app.ports.output.order_participants_port import OrderParticipantsPort
from order.adapter.outbound.pg.order_pg_repository import OrderPgRepository


class OrderParticipantsGateway(OrderParticipantsPort):
    """허브 OrderParticipantsPort 계약의 order 구현 — main.py가 조립한다."""

    async def get_order_participants(self, order_id: int) -> OrderParticipants | None:
        async with session_scope() as session:
            order = await OrderPgRepository(session).find_by_id(order_id)
        if order is None:
            return None
        return OrderParticipants(
            order_id=order.id,
            status=order.status.value,
            brand_user_id=order.brand_user_id,
            creator_user_id=order.creator_user_id,
        )
