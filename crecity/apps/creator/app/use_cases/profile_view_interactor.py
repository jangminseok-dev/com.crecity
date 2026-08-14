from __future__ import annotations

from datetime import date, timedelta

from creator.app.dtos.profile_view_dto import (
    DailyView,
    ProfileViewRecordCommand,
    ProfileViewsResult,
)
from creator.app.exceptions import ProfileNotFoundError
from creator.app.ports.input.profile_view_use_case import ProfileViewUseCase
from creator.app.ports.output.creator_profile_repository import CreatorProfileRepository
from creator.app.ports.output.profile_view_repository import ProfileViewRepository

RECENT_DAYS = 30


class ProfileViewInteractor(ProfileViewUseCase):

    def __init__(
        self, profiles: CreatorProfileRepository, views: ProfileViewRepository
    ) -> None:
        self._profiles = profiles
        self._views = views

    async def record(self, command: ProfileViewRecordCommand) -> None:
        profile = await self._profiles.find_by_slug(command.slug)
        if profile is None:
            return  # 없는 슬러그는 조용히 무시 — 집계가 열람 흐름을 막지 않는다
        await self._views.increment(profile.id)

    async def get_my_views(self, user_id: int) -> ProfileViewsResult:
        profile = await self._profiles.find_by_user_id(user_id)
        if profile is None:
            raise ProfileNotFoundError("등록된 프로필이 없습니다.")

        recorded = {row.view_date: row.view_count for row in
                    await self._views.list_recent(profile.id, RECENT_DAYS)}
        # 조회가 없던 날도 0으로 채워 그래프가 끊기지 않게 한다
        start = date.today() - timedelta(days=RECENT_DAYS - 1)
        daily = [
            DailyView(
                view_date=start + timedelta(days=offset),
                view_count=recorded.get(start + timedelta(days=offset), 0),
            )
            for offset in range(RECENT_DAYS)
        ]
        return ProfileViewsResult(
            days=RECENT_DAYS, total=sum(row.view_count for row in daily), daily=daily
        )
