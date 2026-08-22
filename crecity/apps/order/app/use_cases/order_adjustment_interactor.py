from __future__ import annotations

from order.app.events import order_event
from order.app.dtos.order_adjustment_dto import (
    AdjustmentListQuery,
    AdjustmentResult,
    DeclineAdjustmentCommand,
    RequestAdjustmentCommand,
)
from order.app.exceptions import (
    AdjustmentNotFoundError,
    DuplicateAdjustmentError,
    NotOrderParticipantError,
    OrderNotFoundError,
)
from order.app.ports.input.order_adjustment_use_case import OrderAdjustmentUseCase
from order.app.ports.output.adjustment_repository import AdjustmentRepository
from order.app.ports.output.order_repository import OrderRepository
from order.domain.entities.order_entity import NotOrderActorError, Order

_MAX_REASON = 500


class OrderAdjustmentInteractor(OrderAdjustmentUseCase):

    def __init__(self, orders: OrderRepository, adjustments: AdjustmentRepository) -> None:
        self._orders = orders
        self._adjustments = adjustments

    async def _get_order(self, order_id: int) -> Order:
        order = await self._orders.find_by_id(order_id)
        if order is None:
            raise OrderNotFoundError(f"주문을 찾을 수 없습니다: {order_id}")
        return order

    async def request(self, command: RequestAdjustmentCommand) -> AdjustmentResult:
        reason = command.reason.strip()
        if command.extra_amount_krw <= 0:
            raise ValueError("추가 금액은 0보다 커야 합니다.")
        if not reason or len(reason) > _MAX_REASON:
            raise ValueError(f"사유를 1~{_MAX_REASON}자로 입력해 주세요.")

        order = await self._get_order(command.order_id)
        order.ensure_can_request_adjustment(command.actor_user_id)  # 권한·상태는 도메인
        if await self._adjustments.has_pending(order.id):
            raise DuplicateAdjustmentError("이미 대기 중인 금액 변경 요청이 있습니다.")

        adjustment = await self._adjustments.create(
            order_id=order.id,
            extra_amount_krw=command.extra_amount_krw,
            reason=reason,
            # 요청 사실을 모르면 추가 결제를 할 수 없다(갭 #104) — 요청 저장과 같은 커밋
            events=[
                order_event(
                    "order.adjustment_requested",
                    order,
                    extra_amount_krw=command.extra_amount_krw,
                )
            ],
        )
        return AdjustmentResult.from_entity(adjustment)

    async def decline(self, command: DeclineAdjustmentCommand) -> AdjustmentResult:
        adjustment = await self._adjustments.find_by_id(command.adjustment_id)
        if adjustment is None:
            raise AdjustmentNotFoundError(f"요청을 찾을 수 없습니다: {command.adjustment_id}")
        order = await self._get_order(adjustment.order_id)
        if command.actor_user_id != order.brand_user_id:
            raise NotOrderActorError("주문한 브랜드만 거절할 수 있습니다.")

        declined = adjustment.decline()  # 이미 처리됐으면 InvalidAdjustmentError
        await self._adjustments.save_status(
            declined.id,
            declined.status,
            events=[
                order_event(
                    "order.adjustment_declined", order, extra_amount_krw=declined.extra_amount_krw
                )
            ],
        )
        return AdjustmentResult.from_entity(declined)

    async def list_by_order(self, query: AdjustmentListQuery) -> list[AdjustmentResult]:
        order = await self._get_order(query.order_id)
        if query.requester_user_id not in (order.brand_user_id, order.creator_user_id):
            raise NotOrderParticipantError("주문 당사자만 조회할 수 있습니다.")
        rows = await self._adjustments.list_by_order(order.id)
        return [AdjustmentResult.from_entity(row) for row in rows]
