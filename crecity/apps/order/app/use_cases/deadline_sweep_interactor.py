from __future__ import annotations

from datetime import datetime, timezone

from order.app.dtos.deadline_sweep_dto import SweepOutcome, SweepResult
from order.app.ports.input.deadline_sweep_use_case import DeadlineSweepUseCase
from order.app.ports.output.order_repository import OrderRepository

# 1회 스캔 상한 — 밀린 만료가 많아도 한 번에 다 처리하지 않는다(다음 주기가 이어받음)
_SWEEP_BATCH_LIMIT = 100


class DeadlineSweepInteractor(DeadlineSweepUseCase):

    def __init__(self, orders: OrderRepository) -> None:
        self._orders = orders

    async def sweep(self) -> SweepResult:
        now = datetime.now(timezone.utc)
        expired_orders = await self._orders.find_expired(now, limit=_SWEEP_BATCH_LIMIT)
        outcomes: list[SweepOutcome] = []
        for order in expired_orders:
            outcome = order.expire(now)
            if outcome is None:  # 경합으로 이미 전이된 경우 등
                continue
            updated, entries = outcome
            await self._orders.save_transition(updated, entries)
            outcomes.append(SweepOutcome(order_id=updated.id, status=updated.status.value))
        return SweepResult(outcomes=outcomes)
