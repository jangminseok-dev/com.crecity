from __future__ import annotations

from abc import ABC, abstractmethod

from hub.app.dtos.creator_rating_dto import CreatorRatingSummary


class CreatorRatingPort(ABC):
    """크리에이터 평점 요약 포트 — 구현은 review가 제공하고 main.py가 조립한다."""

    @abstractmethod
    async def get_rating_summaries(
        self, creator_user_ids: list[int]
    ) -> dict[int, CreatorRatingSummary]:
        """리뷰가 있는 크리에이터만 담긴 dict — 리뷰가 없으면 키 부재."""
        ...
