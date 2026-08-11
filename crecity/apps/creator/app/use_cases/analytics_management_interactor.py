from __future__ import annotations

from creator.app.dtos.analytics_management_dto import (
    AnalyticsResult,
    RemoveAnalyticsCommand,
    SubmitAnalyticsCommand,
)
from creator.app.exceptions import AnalyticsNotFoundError, ProfileNotFoundError
from creator.app.ports.input.analytics_management_use_case import AnalyticsManagementUseCase
from creator.app.ports.output.analytics_file_storage import AnalyticsFileStorage
from creator.app.ports.output.analytics_repository import AnalyticsRepository
from creator.app.ports.output.creator_profile_repository import CreatorProfileRepository
from creator.domain.entities.creator_profile_entity import CreatorProfile
from creator.domain.entities.profile_analytics_entity import ANALYTICS_PLATFORMS
from creator.domain.value_objects.image_file import ImageFile

_MAX_ENGAGEMENT_PERMILLE = 1000  # 100.0%


class AnalyticsManagementInteractor(AnalyticsManagementUseCase):

    def __init__(
        self,
        profiles: CreatorProfileRepository,
        analytics: AnalyticsRepository,
        storage: AnalyticsFileStorage,
    ) -> None:
        self._profiles = profiles
        self._analytics = analytics
        self._storage = storage

    async def _my_profile(self, requester_user_id: int) -> CreatorProfile:
        profile = await self._profiles.find_by_user_id(requester_user_id)
        if profile is None:
            raise ProfileNotFoundError("프로필을 먼저 등록해 주세요.")
        return profile

    async def submit(self, command: SubmitAnalyticsCommand) -> AnalyticsResult:
        if command.platform not in ANALYTICS_PLATFORMS:
            allowed = ", ".join(ANALYTICS_PLATFORMS)
            raise ValueError(f"지원하지 않는 플랫폼입니다: {command.platform} (허용: {allowed})")
        if command.followers_count <= 0:
            raise ValueError("팔로워 수는 0보다 커야 합니다.")
        if command.engagement_permille is not None and not (
            0 <= command.engagement_permille <= _MAX_ENGAGEMENT_PERMILLE
        ):
            raise ValueError("참여율은 0~100% 범위여야 합니다.")
        screenshot = ImageFile(content=command.content, content_type=command.content_type)

        profile = await self._my_profile(command.requester_user_id)
        file_name = self._storage.save(screenshot.content, screenshot.extension)
        analytics = await self._analytics.upsert(
            profile_id=profile.id,
            platform=command.platform,
            followers_count=command.followers_count,
            engagement_permille=command.engagement_permille,
            screenshot_file_name=file_name,
        )
        return AnalyticsResult.from_entity(analytics)

    async def list_mine(self, requester_user_id: int) -> list[AnalyticsResult]:
        profile = await self._my_profile(requester_user_id)
        rows = await self._analytics.list_by_profile_id(profile.id)
        return [AnalyticsResult.from_entity(row) for row in rows]

    async def remove(self, command: RemoveAnalyticsCommand) -> None:
        profile = await self._my_profile(command.requester_user_id)
        if not await self._analytics.delete(profile.id, command.platform):
            raise AnalyticsNotFoundError(f"해당 플랫폼 지표가 없습니다: {command.platform}")

    async def list_public(self, slug: str) -> list[AnalyticsResult]:
        profile = await self._profiles.find_by_slug(slug)
        if profile is None:
            raise ProfileNotFoundError(f"프로필을 찾을 수 없습니다: {slug}")
        rows = await self._analytics.list_by_profile_id(profile.id)
        return [AnalyticsResult.from_entity(row) for row in rows]
