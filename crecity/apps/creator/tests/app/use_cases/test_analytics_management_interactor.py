from datetime import datetime, timezone

import pytest

from creator.app.dtos.analytics_management_dto import (
    RemoveAnalyticsCommand,
    SubmitAnalyticsCommand,
)
from creator.app.exceptions import AnalyticsNotFoundError, ProfileNotFoundError
from creator.app.use_cases.analytics_management_interactor import (
    AnalyticsManagementInteractor,
)
from creator.domain.entities.creator_profile_entity import CreatorProfile, ProfileStatus
from creator.domain.entities.profile_analytics_entity import ProfileAnalytics

_NOW = datetime(2026, 8, 11, 12, 0, tzinfo=timezone.utc)
OWNER = 100

_PROFILE = CreatorProfile(
    id=1, slug="kim-beauty", name="김뷰티", tagline="뷰티 크리에이터",
    bio="소개", location="서울", primary_category="뷰티",
    status=ProfileStatus.APPROVED, user_id=OWNER,
)


class _StubProfileRepository:
    def __init__(self, profile=_PROFILE):
        self.profile = profile

    async def find_by_user_id(self, user_id):
        return self.profile if self.profile and self.profile.user_id == user_id else None

    async def find_by_slug(self, slug):
        return self.profile if self.profile and self.profile.slug == slug else None


class _StubAnalyticsRepository:
    def __init__(self):
        self.rows: dict[str, ProfileAnalytics] = {}

    async def upsert(self, profile_id, platform, followers_count, engagement_permille, screenshot_file_name, top_audience_region=None, audience=None):
        row = ProfileAnalytics(
            id=len(self.rows) + 1, profile_id=profile_id, platform=platform,
            followers_count=followers_count, engagement_permille=engagement_permille,
            screenshot_file_name=screenshot_file_name, updated_at=_NOW,
            top_audience_region=top_audience_region, audience=tuple(audience or ()),
        )
        self.rows[platform] = row
        return row

    async def list_by_profile_id(self, profile_id):
        return sorted(self.rows.values(), key=lambda r: -r.followers_count)

    async def delete(self, profile_id, platform):
        return self.rows.pop(platform, None) is not None

    async def followers_total(self, profile_id):
        return sum(r.followers_count for r in self.rows.values())


class _StubStorage:
    def save(self, content, extension):
        return f"stub.{extension}"


def _interactor(profile=_PROFILE):
    analytics = _StubAnalyticsRepository()
    interactor = AnalyticsManagementInteractor(
        profiles=_StubProfileRepository(profile), analytics=analytics, storage=_StubStorage()
    )
    return interactor, analytics


def _command(platform="INSTAGRAM", followers=25000, engagement=35, owner=OWNER):
    return SubmitAnalyticsCommand(
        requester_user_id=owner, platform=platform, followers_count=followers,
        engagement_permille=engagement, content=b"img", content_type="image/png",
    )


async def test_제출하면_스크린샷과_함께_기록된다():
    interactor, analytics = _interactor()
    result = await interactor.submit(_command())
    assert result.platform == "INSTAGRAM"
    assert result.followers_count == 25000
    assert result.engagement_permille == 35  # 3.5%
    assert result.screenshot_file_name == "stub.png"
    assert "INSTAGRAM" in analytics.rows


async def test_같은_플랫폼_재제출은_갱신이다():
    interactor, analytics = _interactor()
    await interactor.submit(_command(followers=10000))
    await interactor.submit(_command(followers=30000))
    assert len(analytics.rows) == 1
    assert analytics.rows["INSTAGRAM"].followers_count == 30000


async def test_지원하지_않는_플랫폼이면_ValueError():
    interactor, _ = _interactor()
    with pytest.raises(ValueError):
        await interactor.submit(_command(platform="UGC"))  # 채널이 아니라 제외


async def test_팔로워가_0이면_ValueError():
    interactor, _ = _interactor()
    with pytest.raises(ValueError):
        await interactor.submit(_command(followers=0))


async def test_참여율이_100퍼센트를_넘으면_ValueError():
    interactor, _ = _interactor()
    with pytest.raises(ValueError):
        await interactor.submit(_command(engagement=1001))


async def test_프로필이_없으면_ProfileNotFoundError():
    interactor, _ = _interactor(profile=None)
    with pytest.raises(ProfileNotFoundError):
        await interactor.submit(_command())


async def test_삭제와_없는_플랫폼_삭제_404():
    interactor, _ = _interactor()
    await interactor.submit(_command())
    await interactor.remove(RemoveAnalyticsCommand(requester_user_id=OWNER, platform="INSTAGRAM"))
    with pytest.raises(AnalyticsNotFoundError):
        await interactor.remove(
            RemoveAnalyticsCommand(requester_user_id=OWNER, platform="INSTAGRAM")
        )


async def test_공개_목록은_슬러그로_조회한다():
    interactor, _ = _interactor()
    await interactor.submit(_command())
    await interactor.submit(_command(platform="YOUTUBE", followers=90000))
    results = await interactor.list_public("kim-beauty")
    assert [r.platform for r in results] == ["YOUTUBE", "INSTAGRAM"]  # 팔로워 내림차순


async def test_오디언스_비율을_저장한다():
    from creator.domain.value_objects.audience_breakdown import AudienceDimension, AudienceShare

    interactor, _ = _interactor()
    result = await interactor.submit(
        SubmitAnalyticsCommand(
            requester_user_id=OWNER,
            platform="INSTAGRAM",
            followers_count=12000,
            engagement_permille=35,
            content=b"img",
            content_type="image/png",
            top_audience_region="서울",
            audience=(
                AudienceShare(AudienceDimension.AGE, "20s", 450),
                AudienceShare(AudienceDimension.AGE, "30s", 300),
                AudienceShare(AudienceDimension.GENDER, "FEMALE", 700),
            ),
        )
    )
    assert result.top_audience_region == "서울"
    assert len(result.audience) == 3


async def test_같은_축_비율_합이_100퍼센트를_넘으면_거부한다():
    from creator.domain.value_objects.audience_breakdown import (
        AudienceDimension,
        AudienceShare,
        InvalidAudienceShareError,
    )

    interactor, _ = _interactor()
    with pytest.raises(InvalidAudienceShareError):
        await interactor.submit(
            SubmitAnalyticsCommand(
                requester_user_id=OWNER,
                platform="INSTAGRAM",
                followers_count=12000,
                engagement_permille=35,
                content=b"img",
                content_type="image/png",
                audience=(
                    AudienceShare(AudienceDimension.AGE, "20s", 700),
                    AudienceShare(AudienceDimension.AGE, "30s", 500),
                ),
            )
        )
