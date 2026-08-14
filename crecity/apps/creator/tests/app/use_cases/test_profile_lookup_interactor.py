import pytest

from creator.app.dtos.profile_lookup_dto import ProfileLookupQuery
from creator.app.exceptions import ProfileNotFoundError
from creator.app.use_cases.profile_lookup_interactor import ProfileLookupInteractor
from hub.app.dtos.creator_trade_stats_dto import CreatorTradeStats
from creator.domain.entities.creator_profile_entity import CreatorProfile, ProfileStatus


class _StubRepository:
    def __init__(self, profile: CreatorProfile | None = None):
        self.profile = profile

    async def create(self, **kwargs):
        raise NotImplementedError

    async def find_by_slug(self, slug):
        return self.profile if self.profile and self.profile.slug == slug else None

    async def exists_by_slug(self, slug):
        return self.profile is not None and self.profile.slug == slug


class _StubAnalyticsRepository:
    def __init__(self, total=125000):
        self.total = total

    async def followers_total(self, profile_id):
        return self.total

    async def upsert(self, **kwargs):
        raise NotImplementedError

    async def list_by_profile_id(self, profile_id):
        raise NotImplementedError

    async def delete(self, profile_id, platform):
        raise NotImplementedError


class _StubTradeStats:
    """허브 CreatorTradeStatsPort 스텁 — 기본은 '이력 없음'."""

    def __init__(self, stats: CreatorTradeStats | None = None):
        self.stats = stats or CreatorTradeStats(0, 0, 0, 0)
        self.calls: list[int] = []

    async def get_creator_stats(self, creator_user_id: int) -> CreatorTradeStats:
        self.calls.append(creator_user_id)
        return self.stats


def _interactor(profile=None, stats=None):
    return ProfileLookupInteractor(
        repository=_StubRepository(profile=profile),
        analytics=_StubAnalyticsRepository(),
        trade_stats=_StubTradeStats(stats),
    )


def _profile(status=ProfileStatus.APPROVED, user_id=None):
    return CreatorProfile(
        id=1,
        slug="kim-beauty",
        name="김뷰티",
        tagline="20대 스킨케어·K뷰티 리뷰",
        bio="성분 분석 콘텐츠를 만듭니다.",
        location="서울",
        primary_category="뷰티",
        status=status,
        user_id=user_id,
    )


async def test_슬러그로_프로필을_조회한다():
    result = await _interactor(_profile()).lookup(ProfileLookupQuery(slug="kim-beauty"))
    assert result.slug == "kim-beauty"
    assert result.status == "APPROVED"
    assert result.followers_total == 125000  # 헤더 배지(§2.1-2)


async def test_거절된_프로필도_직접_조회는_된다():
    result = await _interactor(_profile(ProfileStatus.REJECTED)).lookup(
        ProfileLookupQuery(slug="kim-beauty")
    )
    assert result.status == "REJECTED"


async def test_없는_슬러그면_ProfileNotFoundError():
    with pytest.raises(ProfileNotFoundError):
        await _interactor(None).lookup(ProfileLookupQuery(slug="no-one"))


async def test_거래_실적을_함께_내려준다():
    stats = CreatorTradeStats(
        completed_orders=7, accepted_orders=8, received_orders=10, accept_expired_orders=1
    )
    result = await _interactor(_profile(user_id=101), stats=stats).lookup(
        ProfileLookupQuery(slug="kim-beauty")
    )
    assert result.completed_orders == 7
    assert result.accepted_orders == 8
    assert result.received_orders == 10


async def test_받은_주문이_없으면_실적을_비운다():
    # "완료 0건"을 보여주면 신규 크리에이터가 부당하게 나빠 보인다
    result = await _interactor(_profile(user_id=101)).lookup(
        ProfileLookupQuery(slug="kim-beauty")
    )
    assert result.completed_orders is None
    assert result.received_orders is None
