from __future__ import annotations

from abc import ABC, abstractmethod

from review.app.dtos.brand_review_dto import (
    BrandRatingResult,
    BrandReviewResult,
    BrandReviewSubmissionCommand,
)


class BrandReviewUseCase(ABC):
    """브랜드 리뷰(갭 #83) — 크리에이터도 브랜드를 평가한다(크리에이터 보호 장치).

    Raises:
        OrderNotFoundError · NotOrderCreatorError · OrderNotCompletedError ·
        ReviewAlreadyExistsError · ReviewNotFoundError
    """

    @abstractmethod
    async def submit(self, command: BrandReviewSubmissionCommand) -> BrandReviewResult: ...

    @abstractmethod
    async def get_order_brand_review(
        self, order_id: int, requester_user_id: int
    ) -> BrandReviewResult: ...

    @abstractmethod
    async def get_brand_rating(self, brand_user_id: int) -> BrandRatingResult:
        """공개 집계 — 평점·건수만(원문은 비공개)."""
        ...
