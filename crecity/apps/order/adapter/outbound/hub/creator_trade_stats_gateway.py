from __future__ import annotations

from core.config import ORDER_FAST_RESPONSE_HOURS, ORDER_FAST_RESPONSE_MIN_SAMPLES
from core.database import session_scope
from hub.app.dtos.creator_trade_stats_dto import CreatorTradeStats
from hub.app.ports.output.creator_trade_stats_port import CreatorTradeStatsPort
from order.adapter.outbound.pg.order_pg_repository import OrderPgRepository
from order.domain.value_objects.response_speed import avg_accept_hours, is_fast_responder


class OrderCreatorTradeStatsGateway(CreatorTradeStatsPort):
    """허브 CreatorTradeStatsPort 계약의 order 구현(갭 #66·#80) — 읽기 전용."""

    async def get_creator_stats(self, creator_user_id: int) -> CreatorTradeStats:
        async with session_scope() as session:
            repository = OrderPgRepository(session)
            stats = await repository.get_party_stats(creator_user_id, as_brand=False)
            response = await repository.get_creator_response_stats(creator_user_id)
            refund_disputes = await repository.count_creator_refund_disputes(creator_user_id)
        # 받은 주문 중 거절·만료로 끝난 것(REFUNDED)을 뺀 나머지가 '수락해 진행한' 주문이다
        return CreatorTradeStats(
            completed_orders=stats.completed_orders,
            accepted_orders=stats.total_orders - stats.refunded_orders,
            received_orders=stats.total_orders,
            accept_expired_orders=stats.accept_expired_orders,
            avg_accept_hours=avg_accept_hours(response.avg_accept_seconds),
            fast_responder=is_fast_responder(
                response.avg_accept_seconds,
                response.responded_exits,
                response.expired_exits,
                threshold_hours=ORDER_FAST_RESPONSE_HOURS,
                min_samples=ORDER_FAST_RESPONSE_MIN_SAMPLES,
            ),
            dispute_refund_orders=refund_disputes,
        )
