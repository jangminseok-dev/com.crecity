from __future__ import annotations

from abc import ABC, abstractmethod

from review.app.dtos.review_submission_dto import ReviewResult, ReviewSubmissionCommand


class ReviewSubmissionUseCase(ABC):
    """리뷰 작성 유스케이스 — 완료(COMPLETED) 주문의 브랜드가 주문당 1회 작성한다."""

    @abstractmethod
    async def submit(self, command: ReviewSubmissionCommand) -> ReviewResult:
        """리뷰를 작성한다.

        Raises:
            OrderNotFoundError · NotOrderBrandError · OrderNotCompletedError ·
            ReviewAlreadyExistsError · InvalidScoreError(도메인, 422)
        """
        ...

    @abstractmethod
    async def get_order_review(self, order_id: int, requester_user_id: int) -> ReviewResult:
        """주문의 리뷰 조회(당사자 확인은 주문 화면에서 이미 됨 — 작성 여부 판단용).

        Raises:
            ReviewNotFoundError: 아직 리뷰 없음.
        """
        ...
