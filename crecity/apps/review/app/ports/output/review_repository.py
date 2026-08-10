from __future__ import annotations

from abc import ABC, abstractmethod

from review.domain.entities.review_entity import Review


class ReviewRepository(ABC):
    """리뷰 영속성 포트 (도메인어 명명 예외) — 수정·삭제 없는 작성 전용."""

    @abstractmethod
    async def create(
        self,
        order_id: int,
        brand_user_id: int,
        creator_user_id: int,
        communication_score: int,
        timeliness_score: int,
        satisfaction_score: int,
        comment: str,
    ) -> Review: ...

    @abstractmethod
    async def find_by_order_id(self, order_id: int) -> Review | None: ...

    @abstractmethod
    async def list_by_creator(self, creator_user_id: int) -> list[Review]:
        """크리에이터가 받은 리뷰 — 최신순."""
        ...
