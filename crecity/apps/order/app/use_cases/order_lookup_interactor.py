from __future__ import annotations

import asyncio
from dataclasses import replace

from hub.app.ports.output.creator_ref_port import CreatorRefPort
from hub.app.ports.output.user_directory_port import UserDirectoryPort
from order.app.dtos.order_lookup_dto import MyOrdersQuery, OrderDetailQuery
from order.app.dtos.order_result_dto import OrderResult
from order.app.exceptions import NotOrderParticipantError, OrderNotFoundError
from order.app.ports.input.order_lookup_use_case import OrderLookupUseCase
from order.app.ports.output.order_repository import OrderRepository
from order.domain.entities.order_entity import Order


class OrderLookupInteractor(OrderLookupUseCase):
    """주문 조회 — 결과에 **거래 상대 이름**을 붙인다(갭 #63).

    크리에이터는 72시간 안에 수락 여부를 정해야 하는데 누가 주문했는지 모르면 판단할 수 없다.
    상대 해석은 order가 모르는 정보라 허브 계약(creator·auth)을 경유한다.
    """

    def __init__(
        self,
        orders: OrderRepository,
        creators: CreatorRefPort,
        users: UserDirectoryPort,
    ) -> None:
        self._orders = orders
        self._creators = creators
        self._users = users

    async def list_my_orders(self, query: MyOrdersQuery) -> list[OrderResult]:
        orders = await self._orders.list_by_participant(query.user_id)
        return await self._with_counterparts(orders, query.user_id)

    async def get_order(self, query: OrderDetailQuery) -> OrderResult:
        order = await self._orders.find_by_id(query.order_id)
        if order is None:
            raise OrderNotFoundError(f"주문을 찾을 수 없습니다: {query.order_id}")
        if query.requester_user_id not in (order.brand_user_id, order.creator_user_id):
            raise NotOrderParticipantError("주문 당사자만 조회할 수 있습니다.")
        results = await self._with_counterparts([order], query.requester_user_id)
        return results[0]

    async def _with_counterparts(
        self, orders: list[Order], viewer_user_id: int
    ) -> list[OrderResult]:
        """상대 id를 모아 한 번씩만 조회한다 — 주문 수만큼 부르면 N+1이 된다."""
        creator_ids = {o.creator_user_id for o in orders if o.brand_user_id == viewer_user_id}
        brand_ids = {o.brand_user_id for o in orders if o.creator_user_id == viewer_user_id}

        creator_list, brand_list = await asyncio.gather(
            asyncio.gather(*(self._creators.get_creator_by_user_id(i) for i in creator_ids)),
            asyncio.gather(*(self._users.get_user(i) for i in brand_ids)),
        )
        creators = {ref.creator_user_id: ref for ref in creator_list if ref is not None}
        brands = {ref.user_id: ref for ref in brand_list if ref is not None}

        def to_result(order: Order) -> OrderResult:
            result = OrderResult.from_order(order)
            if order.brand_user_id == viewer_user_id:
                creator = creators.get(order.creator_user_id)
                if creator is None:
                    return result
                return replace(
                    result, counterpart_name=creator.name, counterpart_slug=creator.slug
                )
            brand = brands.get(order.brand_user_id)
            return result if brand is None else replace(result, counterpart_name=brand.name)

        return [to_result(order) for order in orders]
