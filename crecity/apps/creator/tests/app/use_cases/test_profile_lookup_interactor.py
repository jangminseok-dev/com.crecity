import pytest

from creator.app.dtos.profile_lookup_dto import ProfileLookupQuery
from creator.app.exceptions import ProfileNotFoundError
from creator.app.use_cases.profile_lookup_interactor import ProfileLookupInteractor
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


def _interactor(profile=None):
    return ProfileLookupInteractor(_StubRepository(profile=profile), _StubAnalyticsRepository())


def _profile(status=ProfileStatus.APPROVED):
    return CreatorProfile(
        id=1,
        slug="kim-beauty",
        name="김뷰티",
        tagline="20대 스킨케어·K뷰티 리뷰",
        bio="성분 분석 콘텐츠를 만듭니다.",
        location="서울",
        primary_category="뷰티",
        status=status,
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
