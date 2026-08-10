from __future__ import annotations

from hub.app.ports.output.order_participants_port import OrderParticipantsPort
from review.app.dtos.review_submission_dto import ReviewResult, ReviewSubmissionCommand
from review.app.exceptions import (
    NotOrderBrandError,
    OrderNotCompletedError,
    OrderNotFoundError,
    ReviewAlreadyExistsError,
    ReviewNotFoundError,
)
from review.app.ports.input.review_submission_use_case import ReviewSubmissionUseCase
from review.app.ports.output.review_repository import ReviewRepository
from review.domain.entities.review_entity import Review, validate_score


def _to_result(review: Review) -> ReviewResult:
    return ReviewResult(
        id=review.id,
        order_id=review.order_id,
        communication_score=review.communication_score,
        timeliness_score=review.timeliness_score,
        satisfaction_score=review.satisfaction_score,
        overall_score=review.overall_score(),
        comment=review.comment,
        created_at=review.created_at,
    )


class ReviewSubmissionInteractor(ReviewSubmissionUseCase):

    def __init__(self, reviews: ReviewRepository, orders: OrderParticipantsPort) -> None:
        self._reviews = reviews
        self._orders = orders

    async def submit(self, command: ReviewSubmissionCommand) -> ReviewResult:
        order = await self._orders.get_order_participants(command.order_id)
        if order is None:
            raise OrderNotFoundError(f"주문을 찾을 수 없습니다: {command.order_id}")
        if order.brand_user_id != command.requester_user_id:
            raise NotOrderBrandError("주문한 브랜드만 리뷰를 작성할 수 있습니다.")
        if order.status != "COMPLETED":
            raise OrderNotCompletedError("구매 확정(완료)된 주문만 리뷰를 작성할 수 있습니다.")
        if await self._reviews.find_by_order_id(command.order_id) is not None:
            raise ReviewAlreadyExistsError("이미 리뷰를 작성한 주문입니다.")

        review = await self._reviews.create(
            order_id=command.order_id,
            brand_user_id=order.brand_user_id,
            creator_user_id=order.creator_user_id,
            communication_score=validate_score("소통", command.communication_score),
            timeliness_score=validate_score("기한 준수", command.timeliness_score),
            satisfaction_score=validate_score("만족도", command.satisfaction_score),
            comment=command.comment,
        )
        return _to_result(review)

    async def get_order_review(self, order_id: int, requester_user_id: int) -> ReviewResult:
        review = await self._reviews.find_by_order_id(order_id)
        if review is None:
            raise ReviewNotFoundError("아직 작성된 리뷰가 없습니다.")
        return _to_result(review)
