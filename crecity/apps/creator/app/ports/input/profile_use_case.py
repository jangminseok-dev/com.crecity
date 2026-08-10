from __future__ import annotations

from abc import ABC, abstractmethod

from creator.app.dtos.profile_dto import ProfileQuery, ProfileResponse


class ProfileUseCase(ABC):
    """크리에이터 (creator) 유스케이스 — 크리에이터 프로필·판매 패키지 — 마켓플레이스 공급 측 상품 단위."""

    @abstractmethod
    async def introduce_myself(self, query: ProfileQuery) -> ProfileResponse:
        """크리에이터 (creator)의 자기소개 메소드."""
        ...
