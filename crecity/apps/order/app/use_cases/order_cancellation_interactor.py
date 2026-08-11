from __future__ import annotations

from order.app.dtos.order_cancellation_dto import CancellationCommand
from order.app.dtos.order_result_dto import OrderResult
from order.app.events import order_event
from order.app.exceptions import OrderNotFoundError
from order.app.ports.input.order_cancellation_use_case import OrderCancellationUseCase
from order.app.ports.output.order_repository import OrderRepository
from order.domain.entities.order_entity import Order


class OrderCancellationInteractor(OrderCancellationUseCase):

    def __init__(self, orders: OrderRepository) -> None:
        self._orders = orders

    async def _get(self, order_id: int) -> Order:
        order = await self._orders.find_by_id(order_id)
        if order is None:
            raise OrderNotFoundError(f"주문을 찾을 수 없습니다: {order_id}")
        return order

    async def request(self, command: CancellationCommand) -> OrderResult:
        order = (await self._get(command.order_id)).request_cancellation(command.actor_user_id)
        await self._orders.save_transition(
            order,
            [],
            [order_event("order.cancel_requested", order, requested_by=command.actor_user_id)],
        )
        return OrderResult.from_order(order)

    async def consent(self, command: CancellationCommand) -> OrderResult:
        order, entries = (await self._get(command.order_id)).consent_cancellation(
            command.actor_user_id
        )
        await self._orders.save_transition(
            order, entries, [order_event("order.cancelled", order)]
        )
        return OrderResult.from_order(order)

    async def decline(self, command: CancellationCommand) -> OrderResult:
        current = await self._get(command.order_id)
        requested_by = current.cancel_requested_by
        order = current.decline_cancellation(command.actor_user_id)
        await self._orders.save_transition(
            order,
            [],
            # 요청 해제 후에는 요청자 정보가 사라지므로 이벤트에 스냅샷으로 싣는다
            [order_event("order.cancel_declined", order, requested_by=requested_by or 0)],
        )
        return OrderResult.from_order(order)
