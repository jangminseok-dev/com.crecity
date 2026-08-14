from __future__ import annotations

from sqlalchemy import func, or_, select

from core.database import session_scope
from hub.app.dtos.order_search_dto import (
    AdminOrderSummary,
    OrderSearchCriteria,
    OrderSearchResult,
)
from hub.app.ports.output.order_search_port import OrderSearchPort
from order.adapter.outbound.orm.order_orm import OrderOrm


def _conditions(criteria: OrderSearchCriteria) -> list:
    """목록·총계가 공유하는 조건 — 둘이 항상 같은 집합을 본다."""
    conditions = []
    if criteria.order_id is not None:
        conditions.append(OrderOrm.id == criteria.order_id)
    if criteria.status:
        conditions.append(OrderOrm.status == criteria.status)
    if criteria.user_id is not None:
        conditions.append(
            or_(
                OrderOrm.brand_user_id == criteria.user_id,
                OrderOrm.creator_user_id == criteria.user_id,
            )
        )
    return conditions


class OrderSearchGateway(OrderSearchPort):
    """허브 OrderSearchPort 계약의 order 구현(운영 문의 대응, 갭 #56) — 읽기 전용."""

    async def search_orders(self, criteria: OrderSearchCriteria) -> OrderSearchResult:
        conditions = _conditions(criteria)
        async with session_scope() as session:
            rows = await session.execute(
                select(OrderOrm)
                .where(*conditions)
                .order_by(OrderOrm.id.desc())
                .limit(criteria.limit)
                .offset(criteria.offset)
            )
            orders = list(rows.scalars())
            total = await session.scalar(
                select(func.count()).select_from(OrderOrm).where(*conditions)
            )

        return OrderSearchResult(
            items=[
                AdminOrderSummary(
                    id=order.id,
                    package_title=order.package_title,
                    brand_user_id=order.brand_user_id,
                    creator_user_id=order.creator_user_id,
                    amount_krw=order.amount_krw,
                    status=order.status,
                    accept_expired=order.accept_expired,
                    cancel_requested_by=order.cancel_requested_by,
                    revisions_used=order.revisions_used,
                    revision_limit=order.revision_limit,
                    deadline_at=order.deadline_at,
                    created_at=order.created_at,
                )
                for order in orders
            ],
            total=int(total or 0),
        )
