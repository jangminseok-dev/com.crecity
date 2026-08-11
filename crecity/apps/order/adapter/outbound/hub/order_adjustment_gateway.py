from __future__ import annotations

import logging

from core.database import session_scope
from hub.app.dtos.order_adjustment_dto import OrderAdjustmentSummary
from hub.app.ports.output.order_adjustment_port import OrderAdjustmentPort
from order.adapter.outbound.pg.adjustment_pg_repository import AdjustmentPgRepository
from order.adapter.outbound.pg.order_pg_repository import OrderPgRepository
from order.domain.entities.order_entity import InvalidOrderTransitionError

logger = logging.getLogger(__name__)


class OrderAdjustmentGateway(OrderAdjustmentPort):
    """허브 OrderAdjustmentPort 계약의 order 구현 — main.py가 조립한다."""

    async def get_payable_adjustment(
        self, adjustment_id: int
    ) -> OrderAdjustmentSummary | None:
        async with session_scope() as session:
            adjustment = await AdjustmentPgRepository(session).find_by_id(adjustment_id)
            if adjustment is None or not adjustment.is_payable():
                return None
            order = await OrderPgRepository(session).find_by_id(adjustment.order_id)
        if order is None:  # FK가 보장 — 데이터 손상 신호
            return None
        return OrderAdjustmentSummary(
            adjustment_id=adjustment.id,
            order_id=order.id,
            order_title=order.package_title,
            extra_amount_krw=adjustment.extra_amount_krw,
            brand_user_id=order.brand_user_id,
        )

    async def apply_paid_adjustment(self, adjustment_id: int) -> int | None:
        async with session_scope() as session:
            adjustments = AdjustmentPgRepository(session)
            adjustment = await adjustments.find_by_id(adjustment_id)
            if adjustment is None or not adjustment.is_payable():
                return None
            order = await OrderPgRepository(session).find_by_id(adjustment.order_id)
            if order is None:
                return None
            try:
                increased, entries = order.apply_adjustment(adjustment.extra_amount_krw)
            except InvalidOrderTransitionError as error:
                # 결제 사이에 주문이 종결된 경우 — payment가 PG 취소로 보정한다
                logger.warning("금액 변경 반영 불가: adjustment=%s (%s)", adjustment_id, error)
                return None
            await adjustments.apply_payment(adjustment.id, increased, entries)
        return order.id
