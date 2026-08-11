from __future__ import annotations

from creator.app.dtos.profile_registration_dto import (
    ProfileRegistrationCommand,
    ProfileRegistrationResult,
)
from creator.app.exceptions import (
    DuplicateProfileError,
    DuplicateSlugError,
    NotCreatorAccountError,
)
from creator.app.ports.input.profile_registration_use_case import ProfileRegistrationUseCase
from creator.app.ports.output.creator_profile_repository import CreatorProfileRepository
from creator.domain.entities.creator_profile_entity import ProfileStatus
from creator.domain.value_objects.category import Category
from creator.domain.value_objects.slug import Slug


class ProfileRegistrationInteractor(ProfileRegistrationUseCase):

    def __init__(self, repository: CreatorProfileRepository) -> None:
        self._repository = repository

    async def register(self, command: ProfileRegistrationCommand) -> ProfileRegistrationResult:
        if command.account_type != "CREATOR":
            raise NotCreatorAccountError("크리에이터 계정만 프로필을 등록할 수 있습니다.")
        if await self._repository.find_by_user_id(command.user_id) is not None:
            raise DuplicateProfileError("이미 등록된 프로필이 있습니다 — 계정당 1개만 만들 수 있습니다.")
        slug = Slug(command.slug)  # 형식 위반은 여기서 ValueError
        category = Category(command.primary_category)  # 고정 목록 밖이면 ValueError
        if await self._repository.exists_by_slug(slug.value):
            raise DuplicateSlugError(f"이미 사용 중인 슬러그입니다: {slug.value}")

        profile = await self._repository.create(
            slug=slug.value,
            name=command.name,
            tagline=command.tagline,
            bio=command.bio,
            location=command.location,
            primary_category=category.value,
            status=ProfileStatus.PENDING,
            user_id=command.user_id,
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
