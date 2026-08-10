from __future__ import annotations

from datetime import datetime, timedelta, timezone

from order.app.dtos.order_progress_dto import OrderTransitionCommand
from order.app.dtos.order_result_dto import OrderResult
from order.app.events import order_event
from order.app.exceptions import OrderNotFoundError
from order.app.ports.input.order_progress_use_case import OrderProgressUseCase
from order.app.ports.output.order_repository import OrderRepository
from order.domain.entities.order_entity import Order


class OrderProgressInteractor(OrderProgressUseCase):

    def __init__(self, orders: OrderRepository, review_deadline: timedelta) -> None:
        self._orders = orders
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

    async def submit(self, command: OrderTransitionCommand) -> OrderResult:
        now = datetime.now(timezone.utc)
        order = (await self._get(command.order_id)).submit(
            command.actor_user_id, now, self._review_deadline
        )
        await self._orders.save_transition(order, [], [order_event("order.submitted", order)])
        return OrderResult.from_order(order)

    async def request_revision(self, command: OrderTransitionCommand) -> OrderResult:
        order = (await self._get(command.order_id)).request_revision(command.actor_user_id)
        await self._orders.save_transition(
            order, [], [order_event("order.revision_requested", order)]
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
