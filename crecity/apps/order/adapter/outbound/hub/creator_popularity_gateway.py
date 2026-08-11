from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select

from core.config import RANKING_ACCEPT_EXPIRY_PENALTY
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
        # 같은 창에서 성사 주문과 수락 만료를 한 번에 세고, 점수(성사 − 만료×가중치)로 세운다.
        # 만료가 잦은 크리에이터는 노출에서 밀린다(§3.8 — 72h 무응답 페널티, 갭 #32).
        fulfilled = func.count().filter(OrderOrm.status.not_in(_EXCLUDED))
        expired = func.count().filter(OrderOrm.accept_expired.is_(True))
        score = fulfilled - expired * RANKING_ACCEPT_EXPIRY_PENALTY
        async with session_scope() as session:
            result = await session.execute(
                select(OrderOrm.creator_user_id, fulfilled, expired, score)
                .where(OrderOrm.created_at >= cutoff)
                .group_by(OrderOrm.creator_user_id)
                .having(score > 0)  # 점수가 남지 않으면 인기 목록에 올리지 않는다
                .order_by(score.desc(), OrderOrm.creator_user_id)
                .limit(limit)
            )
            return [
                CreatorOrderCount(
                    creator_user_id=user_id,
                    order_count=int(order_count),
                    expired_count=int(expired_count),
                    score=int(total),
                )
                for user_id, order_count, expired_count, total in result
            ]
