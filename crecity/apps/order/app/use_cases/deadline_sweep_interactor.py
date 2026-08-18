from __future__ import annotations

from datetime import datetime, timedelta, timezone

from order.app.dtos.deadline_sweep_dto import SweepOutcome, SweepResult
from order.app.events import order_event
from order.app.ports.input.deadline_sweep_use_case import DeadlineSweepUseCase
from order.app.ports.output.order_repository import OrderRepository
from order.domain.entities.order_entity import OrderStatus

# 1회 스캔 상한 — 밀린 만료가 많아도 한 번에 다 처리하지 않는다(다음 주기가 이어받음)
_SWEEP_BATCH_LIMIT = 100


class DeadlineSweepInteractor(DeadlineSweepUseCase):

    def __init__(self, orders: OrderRepository, warning_threshold: timedelta) -> None:
        self._orders = orders
        self._warning_threshold = warning_threshold

    async def sweep(self) -> SweepResult:
        now = datetime.now(timezone.utc)
        warned = await self._warn_soon_expiring(now)
        expired_orders = await self._orders.find_expired(now, limit=_SWEEP_BATCH_LIMIT)
        outcomes: list[SweepOutcome] = []
        for order in expired_orders:
            outcome = order.expire(now)
            if outcome is None:  # 경합으로 이미 전이된 경우 등
                continue
            updated, entries = outcome
            if updated.status is OrderStatus.COMPLETED:
                event_type = "order.completed"
                extra: dict[str, int | str] = {"payout_krw": updated.creator_payout_krw()}
            elif updated.status is OrderStatus.IN_PROGRESS:
                # 초안 검토 만료 → 자동 컨펌(갭 #85) — 컨펌과 같은 알림을 보낸다
                event_type = "order.draft_approved"
                extra = {}
            else:
                event_type = "order.rejected"
                extra = {}
            await self._orders.save_transition(
                updated, entries, [order_event(event_type, updated, **extra)]
            )
            outcomes.append(SweepOutcome(order_id=updated.id, status=updated.status.value))
        return SweepResult(outcomes=outcomes, warned_order_ids=warned)

    async def _warn_soon_expiring(self, now: datetime) -> list[int]:
        """마감 전에 한 번 알린다(갭 #76) — 만료 처리보다 먼저 훑어 같은 주기에서 겹치지 않게."""
        targets = await self._orders.find_deadline_warning_targets(
            now, self._warning_threshold, limit=_SWEEP_BATCH_LIMIT
        )
        pending = [
            order
            for order in targets
            if order.needs_deadline_warning(now, self._warning_threshold)
        ]
        if not pending:
            return []
        events = [
            order_event(
                "order.deadline_soon",
                order,
                recipient_user_id=order.deadline_warning_recipient(),
                # 문구를 가르는 값이라 payload에 명시한다(기본 payload엔 상태가 없다)
                order_status=order.status.value,
                hours_left=max(1, int((order.deadline_at - now).total_seconds() // 3600)),
            )
            for order in pending
        ]
        order_ids = [order.id for order in pending]
        # 표식과 이벤트는 함께 남긴다 — 갈라지면 알림 유실이나 중복 발송이 된다
        await self._orders.record_deadline_warnings(order_ids, now, events)
        return order_ids
