import pytest

from creator.app.dtos.profile_registration_dto import ProfileRegistrationCommand
from creator.app.exceptions import (
    DuplicateProfileError,
    DuplicateSlugError,
    NotCreatorAccountError,
)
from creator.app.use_cases.profile_registration_interactor import ProfileRegistrationInteractor
from creator.domain.entities.creator_profile_entity import CreatorProfile, ProfileStatus


class _StubRepository:
    def __init__(
        self,
        existing_slugs: set[str] | None = None,
        profile_of_user: CreatorProfile | None = None,
    ):
        self.existing_slugs = existing_slugs or set()
        self.profile_of_user = profile_of_user
        self.created = []

    async def create(self, slug, name, tagline, bio, location, primary_category, status, user_id):
        profile = CreatorProfile(
            id=1,
            slug=slug,
            name=name,
            tagline=tagline,
            bio=bio,
            location=location,
            primary_category=primary_category,
            status=status,
            user_id=user_id,
        )
        self.created.append(profile)
        return profile

    async def find_by_slug(self, slug):
        return None

    async def exists_by_slug(self, slug):
        return slug in self.existing_slugs

    async def find_by_user_id(self, user_id):
        return self.profile_of_user


def _command(slug="kim-beauty", user_id=7, account_type="CREATOR"):
    return ProfileRegistrationCommand(
        slug=slug,
        name="김뷰티",
        tagline="20대 스킨케어·K뷰티 리뷰",
        bio="성분 분석 콘텐츠를 만듭니다.",
        location="서울",
        primary_category="뷰티",
        user_id=user_id,
        account_type=account_type,
    )


async def test_등록하면_심사대기_상태로_로그인_사용자에_귀속된다():
    repository = _StubRepository()
    result = await ProfileRegistrationInteractor(repository).register(_command())
    assert result.status == ProfileStatus.PENDING.value
    assert repository.created[0].slug == "kim-beauty"
    assert repository.created[0].user_id == 7


async def test_브랜드_계정이면_NotCreatorAccountError():
    repository = _StubRepository()
    with pytest.raises(NotCreatorAccountError):
        await ProfileRegistrationInteractor(repository).register(_command(account_type="BRAND"))
    assert repository.created == []


async def test_이미_프로필이_있으면_DuplicateProfileError():
    existing = CreatorProfile(
        id=9, slug="already", name="기존", tagline="t", bio="b",
        location=None, primary_category="뷰티", status=ProfileStatus.PENDING, user_id=7,
    )
    repository = _StubRepository(profile_of_user=existing)
    with pytest.raises(DuplicateProfileError):
        await ProfileRegistrationInteractor(repository).register(_command())
    assert repository.created == []


async def test_중복_슬러그면_DuplicateSlugError():
    repository = _StubRepository(existing_slugs={"kim-beauty"})
    with pytest.raises(DuplicateSlugError):
        await ProfileRegistrationInteractor(repository).register(_command())
    assert repository.created == []


async def test_형식_위반_슬러그면_ValueError_저장_없음():
    repository = _StubRepository()
    with pytest.raises(ValueError):
        await ProfileRegistrationInteractor(repository).register(_command(slug="Kim Beauty!"))
    assert repository.created == []


async def test_고정_목록_밖_카테고리는_거부한다():
    import pytest

    from creator.app.dtos.profile_registration_dto import ProfileRegistrationCommand

    interactor = ProfileRegistrationInteractor(_StubRepository())
    with pytest.raises(ValueError, match="지원하지 않는 카테고리"):
        await interactor.register(
            ProfileRegistrationCommand(
                user_id=1,
                account_type="CREATOR",
                slug="new-creator",
                name="이름",
                tagline="소개",
                bio="상세",
                location=None,
                primary_category="개발",
            )
        )
