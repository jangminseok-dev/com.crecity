from __future__ import annotations

from creator.app.dtos.profile_registration_dto import (
    ProfileRegistrationCommand,
    ProfileRegistrationResult,
)
from creator.app.exceptions import DuplicateSlugError
from creator.app.ports.input.profile_registration_use_case import ProfileRegistrationUseCase
from creator.app.ports.output.creator_profile_repository import CreatorProfileRepository
from creator.domain.entities.creator_profile_entity import ProfileStatus
from creator.domain.value_objects.slug import Slug


class ProfileRegistrationInteractor(ProfileRegistrationUseCase):

    def __init__(self, repository: CreatorProfileRepository) -> None:
        self._repository = repository

    async def register(self, command: ProfileRegistrationCommand) -> ProfileRegistrationResult:
        slug = Slug(command.slug)  # 형식 위반은 여기서 ValueError
        if await self._repository.exists_by_slug(slug.value):
            raise DuplicateSlugError(f"이미 사용 중인 슬러그입니다: {slug.value}")

        profile = await self._repository.create(
            slug=slug.value,
            name=command.name,
            tagline=command.tagline,
            bio=command.bio,
            location=command.location,
            primary_category=command.primary_category,
            status=ProfileStatus.PENDING,
        )
        return ProfileRegistrationResult(
            id=profile.id,
            slug=profile.slug,
            name=profile.name,
            tagline=profile.tagline,
            bio=profile.bio,
            location=profile.location,
            primary_category=profile.primary_category,
            status=profile.status.value,
            created_at=profile.created_at,
        )
