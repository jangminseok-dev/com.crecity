from __future__ import annotations

from datetime import datetime, timedelta, timezone

from order.app.dtos.order_progress_dto import OrderTransitionCommand, RevisionRequestCommand
from order.app.dtos.order_result_dto import OrderResult
from order.app.events import order_event
from order.app.exceptions import OrderNotFoundError
from order.app.ports.input.order_progress_use_case import OrderProgressUseCase
from order.app.ports.output.deliverable_repository import DeliverableRepository
from order.app.ports.output.order_repository import OrderRepository
from order.domain.entities.order_entity import Order


class OrderProgressInteractor(OrderProgressUseCase):

    def __init__(
        self,
        orders: OrderRepository,
        deliverables: DeliverableRepository,
        review_deadline: timedelta,
    ) -> None:
        self._orders = orders
        self._deliverables = deliverables
        self._review_deadline = review_deadline

    async def _get(self, order_id: int) -> Order:
        order = await self._orders.find_by_id(order_id)
        if order is None:
            raise OrderNotFoundError(f"주문을 찾을 수 없습니다: {order_id}")
        return order

    async def accept(self, command: OrderTransitionCommand) -> OrderResult:
        order = (await self._get(command.order_id)).accept(command.actor_user_id)
        await self._orders.save_transition(order, [], [order_event("order.accepted", order)])
        return OrderResult.from_order(order)

    async def reject(self, command: OrderTransitionCommand) -> OrderResult:
        order, entries = (await self._get(command.order_id)).reject(command.actor_user_id)
        await self._orders.save_transition(
            order, entries, [order_event("order.rejected", order)]
        )
        return OrderResult.from_order(order)

    async def submit_draft(self, command: OrderTransitionCommand) -> OrderResult:
        now = datetime.now(timezone.utc)
        deliverable_count = await self._deliverables.count_by_order(command.order_id)
        order = (await self._get(command.order_id)).submit_draft(
            command.actor_user_id, now, self._review_deadline, deliverable_count
        )
        await self._orders.save_transition(
            order, [], [order_event("order.draft_submitted", order)]
        )
        return OrderResult.from_order(order)

    async def approve_draft(self, command: OrderTransitionCommand) -> OrderResult:
        order = (await self._get(command.order_id)).approve_draft(command.actor_user_id)
        await self._orders.save_transition(
            order, [], [order_event("order.draft_approved", order)]
        )
        return OrderResult.from_order(order)

    async def submit(self, command: OrderTransitionCommand) -> OrderResult:
        now = datetime.now(timezone.utc)
        deliverable_count = await self._deliverables.count_by_order(command.order_id)
        order = (await self._get(command.order_id)).submit(
            command.actor_user_id, now, self._review_deadline, deliverable_count
        )
        await self._orders.save_transition(order, [], [order_event("order.submitted", order)])
        return OrderResult.from_order(order)

    async def request_revision(self, command: RevisionRequestCommand) -> OrderResult:
        order = (await self._get(command.order_id)).request_revision(command.actor_user_id)
        # 피드백 본문은 전이와 같은 트랜잭션으로 남는다(갭 #84) — 횟수만 늘고 본문이 없는
        # 요청이 생기지 않게 한다
        await self._orders.save_transition(
            order,
            [],
            [order_event("order.revision_requested", order)],
            revision_comment=command.comment,
        )
        return OrderResult.from_order(order)

    async def approve(self, command: OrderTransitionCommand) -> OrderResult:
        order, entries = (await self._get(command.order_id)).approve(command.actor_user_id)
        await self._orders.save_transition(
            order,
            entries,
            [order_event("order.completed", order, payout_krw=order.creator_payout_krw())],
        )
        return OrderResult.from_order(order)
