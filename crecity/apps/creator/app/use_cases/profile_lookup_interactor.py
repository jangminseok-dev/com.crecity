from __future__ import annotations

from creator.app.dtos.profile_lookup_dto import ProfileLookupQuery, ProfileLookupResult
from creator.app.exceptions import ProfileNotFoundError
from creator.app.ports.input.profile_lookup_use_case import ProfileLookupUseCase
from creator.app.ports.output.analytics_repository import AnalyticsRepository
from creator.app.ports.output.creator_profile_repository import CreatorProfileRepository
from creator.domain.entities.creator_profile_entity import ProfileStatus


class ProfileLookupInteractor(ProfileLookupUseCase):

    def __init__(
        self, repository: CreatorProfileRepository, analytics: AnalyticsRepository
    ) -> None:
        self._repository = repository
        self._analytics = analytics

    async def lookup(self, query: ProfileLookupQuery) -> ProfileLookupResult:
        profile = await self._repository.find_by_slug(query.slug)
        if profile is None or profile.status is ProfileStatus.DELETED:
            raise ProfileNotFoundError(f"프로필을 찾을 수 없습니다: {query.slug}")
        return ProfileLookupResult(
            followers_total=await self._analytics.followers_total(profile.id),
            id=profile.id,
            slug=profile.slug,
            name=profile.name,
            tagline=profile.tagline,
            bio=profile.bio,
            location=profile.location,
            primary_category=profile.primary_category,
            status=profile.status.value,
            accepting_orders=profile.accepting_orders,
            created_at=profile.created_at,
        )
