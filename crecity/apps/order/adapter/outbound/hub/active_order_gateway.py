from __future__ import annotations

from sqlalchemy import exists, select

from core.database import session_scope
from hub.app.ports.output.active_order_port import ActiveOrderPort
from order.adapter.outbound.orm.order_orm import OrderOrm
from order.domain.entities.order_entity import OrderStatus

# 종결되지 않은 상태 — 이 주문이 남아 있으면 계정을 삭제할 수 없다(§3.8)
_ACTIVE_STATUSES = (
    OrderStatus.PENDING_ACCEPT.value,
    OrderStatus.IN_PROGRESS.value,
    OrderStatus.IN_REVIEW.value,
)


class OrderActiveOrderGateway(ActiveOrderPort):
    """허브 ActiveOrderPort 계약의 order 구현 — main.py가 조립한다."""

    async def has_active_orders(self, user_id: int) -> bool:
        async with session_scope() as session:
            result = await session.execute(
                select(
                    exists().where(
                        OrderOrm.status.in_(_ACTIVE_STATUSES),
                        (OrderOrm.brand_user_id == user_id)
                        | (OrderOrm.creator_user_id == user_id),
                    )
                )
            )
            return bool(result.scalar())
