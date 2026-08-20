from __future__ import annotations

from creator.app.dtos.my_profile_lookup_dto import MyProfileResult
from creator.app.dtos.profile_update_dto import ProfileUpdateCommand
from creator.app.exceptions import ProfileNotFoundError
from creator.app.ports.input.profile_update_use_case import ProfileUpdateUseCase
from creator.app.ports.output.creator_profile_repository import CreatorProfileRepository
from creator.domain.value_objects.category import Category


class ProfileUpdateInteractor(ProfileUpdateUseCase):

    def __init__(self, repository: CreatorProfileRepository) -> None:
        self._repository = repository

    async def update_my_profile(self, command: ProfileUpdateCommand) -> MyProfileResult:
        category = Category(command.primary_category)  # 고정 목록 밖이면 ValueError
        profile = await self._repository.update_profile(
            user_id=command.user_id,
            name=command.name,
            tagline=command.tagline,
            bio=command.bio,
            location=command.location,
            primary_category=category.value,
        )
        if profile is None:
            raise ProfileNotFoundError("등록된 프로필이 없습니다.")
        return MyProfileResult(
            id=profile.id,
            slug=profile.slug,
            name=profile.name,
            tagline=profile.tagline,
            bio=profile.bio,
            location=profile.location,
            primary_category=profile.primary_category,
            status=profile.status.value,
            created_at=profile.created_at,
            accepting_orders=profile.accepting_orders,
        )
