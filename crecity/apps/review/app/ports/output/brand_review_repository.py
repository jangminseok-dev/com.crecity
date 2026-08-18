from __future__ import annotations

from abc import ABC, abstractmethod

from hub.app.dtos.outbox_event_dto import OutboxEvent
from review.app.dtos.brand_review_dto import BrandRatingResult, BrandReviewResult


class BrandReviewRepository(ABC):
    """브랜드 리뷰 영속성 포트(갭 #83) — 완료 주문당 1건."""

    @abstractmethod
    async def create(
        self,
        order_id: int,
        brand_user_id: int,
        creator_user_id: int,
        score: int,
        comment: str,
        events: list[OutboxEvent] | None = None,
    ) -> BrandReviewResult:
        """저장 — 알림 이벤트(갭 #83)를 같은 트랜잭션에 적재한다."""
        ...

    @abstractmethod
    async def find_by_order_id(self, order_id: int) -> BrandReviewResult | None: ...

    @abstractmethod
    async def get_brand_rating(self, brand_user_id: int) -> BrandRatingResult:
        """브랜드 평점 집계 — 리뷰가 없으면 average None."""
        ...
