from __future__ import annotations

from abc import ABC, abstractmethod

from creator.app.dtos.popular_profiles_dto import PopularProfilesQuery
from creator.app.dtos.profile_listing_dto import ProfileListingItem


class PopularProfilesUseCase(ABC):
    """최근 주문이 많은 크리에이터 목록(홈 '이번 주 인기' 섹션)."""

    @abstractmethod
    async def list_popular(self, query: PopularProfilesQuery) -> list[ProfileListingItem]: ...
