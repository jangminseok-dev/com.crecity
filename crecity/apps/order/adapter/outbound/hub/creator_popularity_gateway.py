from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select

from core.database import session_scope
from hub.app.dtos.creator_popularity_dto import CreatorOrderCount
from hub.app.ports.output.creator_popularity_port import CreatorPopularityPort
from order.adapter.outbound.orm.order_orm import OrderOrm
from order.domain.entities.order_entity import OrderStatus

# 인기 집계에서 제외하는 상태 — 성사되지 않은 거래
_EXCLUDED = (OrderStatus.REFUNDED.value, OrderStatus.CANCELLED.value)


class OrderCreatorPopularityGateway(CreatorPopularityPort):
    """허브 CreatorPopularityPort 계약의 order 구현 — main.py가 조립한다.

    호출자(creator 인기 목록) 트랜잭션과 무관한 읽기 전용 조회라 자체 세션을 연다.
    """

    async def top_creators_by_recent_orders(self, days: int, limit: int) -> list[CreatorOrderCount]:
        cutoff = datetime.now(UTC) - timedelta(days=days)
        async with session_scope() as session:
            result = await session.execute(
                select(OrderOrm.creator_user_id, func.count())
                .where(OrderOrm.created_at >= cutoff)
                .where(OrderOrm.status.not_in(_EXCLUDED))
                .group_by(OrderOrm.creator_user_id)
                .order_by(func.count().desc(), OrderOrm.creator_user_id)
                .limit(limit)
            )
            return [
                CreatorOrderCount(creator_user_id=user_id, order_count=int(count))
                for user_id, count in result
            ]
