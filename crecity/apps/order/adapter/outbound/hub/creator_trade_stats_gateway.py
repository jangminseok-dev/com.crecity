from __future__ import annotations

from core.database import session_scope
from hub.app.dtos.creator_trade_stats_dto import CreatorTradeStats
from hub.app.ports.output.creator_trade_stats_port import CreatorTradeStatsPort
from order.adapter.outbound.pg.order_pg_repository import OrderPgRepository


class OrderCreatorTradeStatsGateway(CreatorTradeStatsPort):
    """허브 CreatorTradeStatsPort 계약의 order 구현(갭 #66) — 읽기 전용."""

    async def get_creator_stats(self, creator_user_id: int) -> CreatorTradeStats:
        async with session_scope() as session:
            stats = await OrderPgRepository(session).get_party_stats(
                creator_user_id, as_brand=False
            )
        # 받은 주문 중 거절·만료로 끝난 것(REFUNDED)을 뺀 나머지가 '수락해 진행한' 주문이다
        return CreatorTradeStats(
            completed_orders=stats.completed_orders,
            accepted_orders=stats.total_orders - stats.refunded_orders,
            received_orders=stats.total_orders,
            accept_expired_orders=stats.accept_expired_orders,
        )
