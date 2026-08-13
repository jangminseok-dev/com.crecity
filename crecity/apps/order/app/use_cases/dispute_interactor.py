from __future__ import annotations

from order.app.dtos.dispute_dto import DisputeListQuery, DisputeResult, RaiseDisputeCommand
from order.app.events import order_event
from order.app.exceptions import NotOrderParticipantError, OrderNotFoundError
from order.app.ports.input.dispute_use_case import DisputeUseCase
from order.app.ports.output.dispute_repository import DisputeRepository
from order.app.ports.output.order_repository import OrderRepository
from order.domain.entities.order_entity import InvalidOrderTransitionError, Order
from order.domain.value_objects.dispute_reason import DisputeReason


class DisputeInteractor(DisputeUseCase):

    def __init__(self, orders: OrderRepository, disputes: DisputeRepository) -> None:
        self._orders = orders
        self._disputes = disputes

    async def _get(self, order_id: int) -> Order:
        order = await self._orders.find_by_id(order_id)
        if order is None:
            raise OrderNotFoundError(f"주문을 찾을 수 없습니다: {order_id}")
        return order

    async def raise_dispute(self, command: RaiseDisputeCommand) -> DisputeResult:
        reason = DisputeReason(text=command.reason)
        order = await self._get(command.order_id)
        order.ensure_can_raise_dispute(command.actor_user_id)
        if await self._disputes.find_open_by_order(order.id) is not None:
            raise InvalidOrderTransitionError("이미 처리 대기 중인 분쟁이 있습니다.")

        dispute = await self._disputes.add(
            order_id=order.id,
            raised_by_user_id=command.actor_user_id,
            reason=reason.text,
            events=[order_event("order.dispute_raised", order, raised_by=command.actor_user_id)],
        )
        return DisputeResult.from_dispute(dispute)

    async def list_disputes(self, query: DisputeListQuery) -> list[DisputeResult]:
        order = await self._get(query.order_id)
        if query.requester_user_id not in (order.brand_user_id, order.creator_user_id):
            raise NotOrderParticipantError("주문 당사자만 조회할 수 있습니다.")
        disputes = await self._disputes.list_by_order(order.id)
        return [DisputeResult.from_dispute(d) for d in disputes]
