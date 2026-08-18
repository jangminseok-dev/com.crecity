from __future__ import annotations

from hub.app.dtos.outbox_event_dto import OutboxEvent
from hub.app.ports.output.order_participants_port import OrderParticipantsPort
from review.app.dtos.brand_review_dto import (
    BrandRatingResult,
    BrandReviewResult,
    BrandReviewSubmissionCommand,
)
from review.app.exceptions import (
    NotOrderCreatorError,
    OrderNotCompletedError,
    OrderNotFoundError,
    ReviewAlreadyExistsError,
    ReviewNotFoundError,
)
from review.app.ports.input.brand_review_use_case import BrandReviewUseCase
from review.app.ports.output.brand_review_repository import BrandReviewRepository
from review.domain.entities.review_entity import validate_score


class BrandReviewInteractor(BrandReviewUseCase):
    """브랜드 리뷰(갭 #83) — 자격 규칙은 크리에이터 리뷰와 대칭(완료 주문·본인·1회)."""

    def __init__(self, reviews: BrandReviewRepository, orders: OrderParticipantsPort) -> None:
        self._reviews = reviews
        self._orders = orders

    async def submit(self, command: BrandReviewSubmissionCommand) -> BrandReviewResult:
        order = await self._orders.get_order_participants(command.order_id)
        if order is None:
            raise OrderNotFoundError(f"주문을 찾을 수 없습니다: {command.order_id}")
        if order.creator_user_id != command.requester_user_id:
            raise NotOrderCreatorError("주문을 수행한 크리에이터만 브랜드를 평가할 수 있습니다.")
        if order.status != "COMPLETED":
            raise OrderNotCompletedError("구매 확정(완료)된 주문만 평가할 수 있습니다.")
        if await self._reviews.find_by_order_id(command.order_id) is not None:
            raise ReviewAlreadyExistsError("이미 브랜드 평가를 작성한 주문입니다.")

        return await self._reviews.create(
            order_id=command.order_id,
            brand_user_id=order.brand_user_id,
            creator_user_id=order.creator_user_id,
            score=validate_score("평점", command.score),
            comment=command.comment,
            # 평가 받은 사실은 브랜드도 알아야 한다 — 저장과 같은 트랜잭션(BOUNDARIES §1)
            events=[
                OutboxEvent(
                    event_type="review.brand_received",
                    payload={"brand_user_id": order.brand_user_id, "order_id": order.order_id},
                )
            ],
        )

    async def get_order_brand_review(
        self, order_id: int, requester_user_id: int
    ) -> BrandReviewResult:
        order = await self._orders.get_order_participants(order_id)
        if order is None:
            raise OrderNotFoundError(f"주문을 찾을 수 없습니다: {order_id}")
        if requester_user_id not in (order.brand_user_id, order.creator_user_id):
            raise NotOrderCreatorError("주문 당사자만 조회할 수 있습니다.")
        review = await self._reviews.find_by_order_id(order_id)
        if review is None:
            raise ReviewNotFoundError("아직 작성된 브랜드 평가가 없습니다.")
        return review

    async def get_brand_rating(self, brand_user_id: int) -> BrandRatingResult:
        return await self._reviews.get_brand_rating(brand_user_id)
