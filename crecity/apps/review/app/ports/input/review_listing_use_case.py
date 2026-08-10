from __future__ import annotations

from abc import ABC, abstractmethod

from review.app.dtos.review_listing_dto import CreatorReviewsQuery, CreatorReviewsResult


class ReviewListingUseCase(ABC):
    """크리에이터 리뷰 공개 조회 — 집계(3축 평균·종합)는 공개, 원문은 로그인 시에만.

    블러 정책(collabstr §2.3 Freemium Gate): 비로그인 응답은 comment를 잠근다.
    """

    @abstractmethod
    async def list_for_creator(self, query: CreatorReviewsQuery) -> CreatorReviewsResult:
        """슬러그의 크리에이터 리뷰 목록·집계.

        Raises:
            CreatorNotFoundError: 크리에이터 없음.
        """
        ...
