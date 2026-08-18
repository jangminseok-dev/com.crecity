from __future__ import annotations

from order.app.dtos.revision_lookup_dto import RevisionListQuery, RevisionRequestResult
from order.app.exceptions import NotOrderParticipantError, OrderNotFoundError
from order.app.ports.input.revision_lookup_use_case import RevisionLookupUseCase
from order.app.ports.output.order_repository import OrderRepository
from order.app.ports.output.revision_request_repository import RevisionRequestRepository


class RevisionLookupInteractor(RevisionLookupUseCase):

    def __init__(self, orders: OrderRepository, revisions: RevisionRequestRepository) -> None:
        self._orders = orders
        self._revisions = revisions

    async def list_revisions(self, query: RevisionListQuery) -> list[RevisionRequestResult]:
        order = await self._orders.find_by_id(query.order_id)
        if order is None:
            raise OrderNotFoundError(f"주문을 찾을 수 없습니다: {query.order_id}")
        if query.requester_user_id not in (order.brand_user_id, order.creator_user_id):
            raise NotOrderParticipantError("주문 당사자만 조회할 수 있습니다.")
        return await self._revisions.list_by_order(order.id)
