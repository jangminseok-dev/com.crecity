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
from creator.domain.value_objects.audience_breakdown import validate_breakdown
from creator.domain.value_objects.image_file import ImageFile
from creator.domain.value_objects.metric_anomaly import detect_anomaly

_MAX_ENGAGEMENT_PERMILLE = 1000  # 100.0%


class AnalyticsManagementInteractor(AnalyticsManagementUseCase):

    def __init__(
        self,
        profiles: CreatorProfileRepository,
        analytics: AnalyticsRepository,
        storage: AnalyticsFileStorage,
        anomaly_surge_multiplier: int,
        anomaly_engagement_floor: int,
        anomaly_max_engagement_permille: int,
    ) -> None:
        self._profiles = profiles
        self._analytics = analytics
        self._storage = storage
        self._anomaly_surge_multiplier = anomaly_surge_multiplier
        self._anomaly_engagement_floor = anomaly_engagement_floor
        self._anomaly_max_engagement_permille = anomaly_max_engagement_permille

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
        if command.avg_views is not None and command.avg_views < 0:
            raise ValueError("평균 조회수는 0 이상이어야 합니다.")
        screenshot = ImageFile(content=command.content, content_type=command.content_type)
        # 오디언스 비율 검증(갭 #67) — 같은 축의 합이 100%를 넘으면 입력을 잘못 본 것이다
        audience = validate_breakdown(list(command.audience))

        profile = await self._my_profile(command.requester_user_id)
        # 이상치 판정(갭 #82) — 직전 제출값과 비교해 급증·고참여율을 플래그(저장은 그대로 진행)
        previous = next(
            (
                row
                for row in await self._analytics.list_by_profile_id(profile.id)
                if row.platform == command.platform
            ),
            None,
        )
        flag_reason = detect_anomaly(
            previous_followers=previous.followers_count if previous else None,
            new_followers=command.followers_count,
            engagement_permille=command.engagement_permille,
            surge_multiplier=self._anomaly_surge_multiplier,
            engagement_floor_followers=self._anomaly_engagement_floor,
            max_engagement_permille=self._anomaly_max_engagement_permille,
        )
        file_name = self._storage.save(screenshot.content, screenshot.extension)
        analytics = await self._analytics.upsert(
            profile_id=profile.id,
            platform=command.platform,
            followers_count=command.followers_count,
            engagement_permille=command.engagement_permille,
            avg_views=command.avg_views,
            screenshot_file_name=file_name,
            top_audience_region=(command.top_audience_region or None),
            audience=audience,
            flag_reason=flag_reason,
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
