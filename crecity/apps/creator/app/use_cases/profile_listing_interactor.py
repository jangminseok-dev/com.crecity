from __future__ import annotations

from creator.app.dtos.profile_listing_dto import (
    ProfileListingItem,
    ProfileListingQuery,
    ProfileListingResult,
)
from creator.app.ports.input.profile_listing_use_case import ProfileListingUseCase
from creator.app.ports.output.creator_profile_repository import CreatorProfileRepository
from creator.domain.entities.creator_profile_entity import ProfileStatus


class ProfileListingInteractor(ProfileListingUseCase):

    def __init__(self, repository: CreatorProfileRepository) -> None:
        self._repository = repository

    async def list_profiles(self, query: ProfileListingQuery) -> ProfileListingResult:
        profiles = await self._repository.list_by_status(
            status=ProfileStatus.APPROVED,
            category=query.category,
            limit=query.limit,
            offset=query.offset,
            q=query.q,
        )
        total = await self._repository.count_by_status(
            status=ProfileStatus.APPROVED, category=query.category, q=query.q
        )
        return ProfileListingResult(
            items=[
                ProfileListingItem(
                    id=profile.id,
                    slug=profile.slug,
                    name=profile.name,
                    tagline=profile.tagline,
                    location=profile.location,
                    primary_category=profile.primary_category,
                    created_at=profile.created_at,
                )
                for profile in profiles
            ],
            total=total,
        )

    async def list_categories(self) -> list[str]:
        return await self._repository.list_categories(status=ProfileStatus.APPROVED)
