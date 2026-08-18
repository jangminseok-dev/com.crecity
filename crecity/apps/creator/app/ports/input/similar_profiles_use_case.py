from __future__ import annotations

from abc import ABC, abstractmethod

from creator.app.dtos.profile_listing_dto import ProfileListingItem
from creator.app.dtos.similar_profiles_dto import SimilarProfilesQuery


class SimilarProfilesUseCase(ABC):
    """유사 크리에이터 추천(갭 #88) — 프로필 하단 '비슷한 크리에이터' 섹션."""

    @abstractmethod
    async def list_similar(self, query: SimilarProfilesQuery) -> list[ProfileListingItem]: ...
