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
    interactor = ProfileLookupInteractor(_StubRepository(profile=_profile()))
    result = await interactor.lookup(ProfileLookupQuery(slug="kim-beauty"))
    assert result.slug == "kim-beauty"
    assert result.status == "APPROVED"


async def test_거절된_프로필도_직접_조회는_된다():
    interactor = ProfileLookupInteractor(_StubRepository(profile=_profile(ProfileStatus.REJECTED)))
    result = await interactor.lookup(ProfileLookupQuery(slug="kim-beauty"))
    assert result.status == "REJECTED"


async def test_없는_슬러그면_ProfileNotFoundError():
    interactor = ProfileLookupInteractor(_StubRepository(profile=None))
    with pytest.raises(ProfileNotFoundError):
        await interactor.lookup(ProfileLookupQuery(slug="no-one"))
