from __future__ import annotations

from order.app.dtos.order_lookup_dto import MyOrdersQuery, OrderDetailQuery
from order.app.dtos.order_result_dto import OrderResult
from order.app.exceptions import NotOrderParticipantError, OrderNotFoundError
from order.app.ports.input.order_lookup_use_case import OrderLookupUseCase
from order.app.ports.output.order_repository import OrderRepository


class OrderLookupInteractor(OrderLookupUseCase):

    def __init__(self, orders: OrderRepository) -> None:
        self._orders = orders

    async def list_my_orders(self, query: MyOrdersQuery) -> list[OrderResult]:
        orders = await self._orders.list_by_participant(query.user_id)
        return [OrderResult.from_order(order) for order in orders]

    async def get_order(self, query: OrderDetailQuery) -> OrderResult:
        order = await self._orders.find_by_id(query.order_id)
        if order is None:
            raise OrderNotFoundError(f"주문을 찾을 수 없습니다: {query.order_id}")
        if query.requester_user_id not in (order.brand_user_id, order.creator_user_id):
            raise NotOrderParticipantError("주문 당사자만 조회할 수 있습니다.")
        return OrderResult.from_order(order)
