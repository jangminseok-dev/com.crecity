from __future__ import annotations

from abc import ABC, abstractmethod

from review.app.dtos.appraiser_dto import AppraiserQuery, AppraiserResponse


class AppraiserUseCase(ABC):
    """리뷰 (review) 유스케이스 — 3축 평점·리뷰 블러 정책 담당."""

    @abstractmethod
    async def introduce_myself(self, query: AppraiserQuery) -> AppraiserResponse:
        """리뷰 (review)의 자기소개 메소드."""
        ...
