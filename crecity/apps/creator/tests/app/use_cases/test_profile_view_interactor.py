from datetime import date, timedelta

import pytest

from creator.app.dtos.profile_view_dto import DailyView, ProfileViewRecordCommand
from creator.app.exceptions import ProfileNotFoundError
from creator.app.use_cases.profile_view_interactor import RECENT_DAYS, ProfileViewInteractor
from creator.domain.entities.creator_profile_entity import CreatorProfile, ProfileStatus

OWNER_ID = 101


def _profile(profile_id: int = 1, slug: str = "kim-beauty") -> CreatorProfile:
    return CreatorProfile(
        id=profile_id,
        slug=slug,
        name="김뷰티",
        tagline="20대 스킨케어",
        bio="성분 분석 콘텐츠",
        location="서울",
        primary_category="뷰티",
        status=ProfileStatus.APPROVED,
        user_id=OWNER_ID,
    )


class _StubProfiles:
    def __init__(self, profile: CreatorProfile | None = None):
        self.profile = profile

    async def find_by_slug(self, slug: str) -> CreatorProfile | None:
        return self.profile if self.profile and self.profile.slug == slug else None

    async def find_by_user_id(self, user_id: int) -> CreatorProfile | None:
        return self.profile if self.profile and self.profile.user_id == user_id else None


class _StubViews:
    def __init__(self, recent: list[DailyView] | None = None):
        self.recent = recent or []
        self.incremented: list[int] = []

    async def increment(self, profile_id: int) -> None:
        self.incremented.append(profile_id)

    async def list_recent(self, profile_id: int, days: int) -> list[DailyView]:
        return self.recent


async def test_슬러그로_찾은_프로필의_조회수를_올린다():
    views = _StubViews()
    await ProfileViewInteractor(profiles=_StubProfiles(_profile()), views=views).record(
        ProfileViewRecordCommand(slug="kim-beauty")
    )
    assert views.incremented == [1]


async def test_없는_슬러그는_조용히_무시한다():
    views = _StubViews()
    await ProfileViewInteractor(profiles=_StubProfiles(_profile()), views=views).record(
        ProfileViewRecordCommand(slug="nope")
    )
    assert views.incremented == []


async def test_조회가_없던_날도_0으로_채운다():
    today = date.today()
    views = _StubViews(recent=[DailyView(view_date=today, view_count=5)])
    result = await ProfileViewInteractor(
        profiles=_StubProfiles(_profile()), views=views
    ).get_my_views(OWNER_ID)

    assert len(result.daily) == RECENT_DAYS
    assert result.daily[-1] == DailyView(view_date=today, view_count=5)
    assert result.daily[0].view_date == today - timedelta(days=RECENT_DAYS - 1)
    assert result.daily[0].view_count == 0
    assert result.total == 5


async def test_프로필이_없으면_예외():
    with pytest.raises(ProfileNotFoundError):
        await ProfileViewInteractor(
            profiles=_StubProfiles(None), views=_StubViews()
        ).get_my_views(OWNER_ID)


async def test_남의_조회수는_볼_수_없다():
    # find_by_user_id가 소유자만 매칭하므로 다른 사용자는 프로필 없음으로 떨어진다
    with pytest.raises(ProfileNotFoundError):
        await ProfileViewInteractor(
            profiles=_StubProfiles(_profile()), views=_StubViews()
        ).get_my_views(user_id=999)
