import pytest

from creator.app.dtos.my_profile_lookup_dto import MyProfileQuery
from creator.app.exceptions import ProfileNotFoundError
from creator.app.use_cases.my_profile_lookup_interactor import MyProfileLookupInteractor
from creator.domain.entities.creator_profile_entity import CreatorProfile, ProfileStatus


class _StubRepository:
    def __init__(self, profile: CreatorProfile | None = None):
        self.profile = profile

    async def find_by_user_id(self, user_id):
        return self.profile if self.profile and self.profile.user_id == user_id else None


def _profile():
    return CreatorProfile(
        id=1,
        slug="kim-beauty",
        name="김뷰티",
        tagline="스킨케어 리뷰",
        bio="소개",
        location="서울",
        primary_category="뷰티",
        status=ProfileStatus.PENDING,
        user_id=7,
    )


async def test_내_프로필을_조회한다():
    interactor = MyProfileLookupInteractor(_StubRepository(profile=_profile()))
    result = await interactor.get_my_profile(MyProfileQuery(user_id=7))
    assert result.slug == "kim-beauty"
    assert result.status == "PENDING"


async def test_프로필이_없으면_ProfileNotFoundError():
    interactor = MyProfileLookupInteractor(_StubRepository(profile=None))
    with pytest.raises(ProfileNotFoundError):
        await interactor.get_my_profile(MyProfileQuery(user_id=7))
