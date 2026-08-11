from __future__ import annotations

from order.app.dtos.deliverable_submission_dto import (
    DeliverableListQuery,
    DeliverableResult,
    SubmitDeliverableFileCommand,
    SubmitDeliverableLinkCommand,
)
from order.app.exceptions import NotOrderParticipantError, OrderNotFoundError
from order.app.ports.input.deliverable_submission_use_case import DeliverableSubmissionUseCase
from order.app.ports.output.deliverable_file_storage import DeliverableFileStorage
from order.app.ports.output.deliverable_repository import DeliverableRepository
from order.app.ports.output.order_repository import OrderRepository
from order.domain.entities.deliverable_entity import DeliverableKind
from order.domain.entities.order_entity import Order
from order.domain.value_objects.deliverable_file import DeliverableFile
from order.domain.value_objects.deliverable_link import DeliverableLink

_ORIGINAL_NAME_MAX = 255


class DeliverableSubmissionInteractor(DeliverableSubmissionUseCase):

    def __init__(
        self,
        orders: OrderRepository,
        deliverables: DeliverableRepository,
        storage: DeliverableFileStorage,
    ) -> None:
        self._orders = orders
        self._deliverables = deliverables
        self._storage = storage

    async def _get(self, order_id: int) -> Order:
        order = await self._orders.find_by_id(order_id)
        if order is None:
            raise OrderNotFoundError(f"주문을 찾을 수 없습니다: {order_id}")
        return order

    async def submit_file(self, command: SubmitDeliverableFileCommand) -> DeliverableResult:
        file = DeliverableFile(content=command.content, content_type=command.content_type)
        order = await self._get(command.order_id)
        order.ensure_can_attach_deliverable(command.actor_user_id)

        file_name = self._storage.save(file.content, file.extension)
        deliverable = await self._deliverables.add(
            order_id=order.id,
            kind=DeliverableKind.FILE,
            file_name=file_name,
            original_name=command.original_name[:_ORIGINAL_NAME_MAX] or None,
            url=None,
        )
        return DeliverableResult.from_deliverable(deliverable)

    async def submit_link(self, command: SubmitDeliverableLinkCommand) -> DeliverableResult:
        link = DeliverableLink(url=command.url)
        order = await self._get(command.order_id)
        order.ensure_can_attach_deliverable(command.actor_user_id)

        deliverable = await self._deliverables.add(
            order_id=order.id,
            kind=DeliverableKind.LINK,
            file_name=None,
            original_name=None,
            url=link.url,
        )
        return DeliverableResult.from_deliverable(deliverable)

    async def list_deliverables(self, query: DeliverableListQuery) -> list[DeliverableResult]:
        order = await self._get(query.order_id)
        if query.requester_user_id not in (order.brand_user_id, order.creator_user_id):
            raise NotOrderParticipantError("주문 당사자만 조회할 수 있습니다.")
        deliverables = await self._deliverables.list_by_order(order.id)
        return [DeliverableResult.from_deliverable(d) for d in deliverables]
