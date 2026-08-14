from __future__ import annotations

from admin.app.dtos.order_search_dto import (
    OrderSearchItem,
    OrderSearchQuery,
    OrderSearchResultDto,
)
from admin.app.ports.input.order_search_use_case import OrderSearchUseCase
from hub.app.dtos.order_search_dto import OrderSearchCriteria
from hub.app.ports.output.order_search_port import OrderSearchPort

_MAX_LIMIT = 50  # 한 화면 분량 — 더 필요하면 조건을 좁힌다


class OrderSearchInteractor(OrderSearchUseCase):

    def __init__(self, orders: OrderSearchPort) -> None:
        self._orders = orders

    async def search(self, query: OrderSearchQuery) -> OrderSearchResultDto:
        result = await self._orders.search_orders(
            OrderSearchCriteria(
                order_id=query.order_id,
                status=query.status,
                user_id=query.user_id,
                limit=min(query.limit, _MAX_LIMIT),
                offset=query.offset,
            )
        )
        return OrderSearchResultDto(
            items=[
                OrderSearchItem(
                    id=order.id,
                    package_title=order.package_title,
                    brand_user_id=order.brand_user_id,
                    creator_user_id=order.creator_user_id,
                    amount_krw=order.amount_krw,
                    status=order.status,
                    accept_expired=order.accept_expired,
                    cancel_requested_by=order.cancel_requested_by,
                    revisions_used=order.revisions_used,
                    revision_limit=order.revision_limit,
                    deadline_at=order.deadline_at,
                    created_at=order.created_at,
                )
                for order in result.items
            ],
            total=result.total,
        )
