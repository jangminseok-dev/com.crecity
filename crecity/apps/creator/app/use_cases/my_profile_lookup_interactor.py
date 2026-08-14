from __future__ import annotations

from creator.app.dtos.my_profile_lookup_dto import MyProfileQuery, MyProfileResult
from creator.app.exceptions import ProfileNotFoundError
from creator.app.ports.input.my_profile_lookup_use_case import MyProfileLookupUseCase
from creator.app.ports.output.creator_profile_repository import CreatorProfileRepository


class MyProfileLookupInteractor(MyProfileLookupUseCase):

    def __init__(self, repository: CreatorProfileRepository) -> None:
        self._repository = repository

    async def get_my_profile(self, query: MyProfileQuery) -> MyProfileResult:
        profile = await self._repository.find_by_user_id(query.user_id)
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
            accepting_orders=profile.accepting_orders,
            created_at=profile.created_at,
        )
