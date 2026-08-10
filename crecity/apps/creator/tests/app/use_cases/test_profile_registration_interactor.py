import pytest

from creator.app.dtos.profile_registration_dto import ProfileRegistrationCommand
from creator.app.exceptions import DuplicateSlugError
from creator.app.use_cases.profile_registration_interactor import ProfileRegistrationInteractor
from creator.domain.entities.creator_profile_entity import CreatorProfile, ProfileStatus


class _StubRepository:
    def __init__(self, existing_slugs: set[str] | None = None):
        self.existing_slugs = existing_slugs or set()
        self.created = []

    async def create(self, slug, name, tagline, bio, location, primary_category, status):
        profile = CreatorProfile(
            id=1,
            slug=slug,
            name=name,
            tagline=tagline,
            bio=bio,
            location=location,
            primary_category=primary_category,
            status=status,
        )
        self.created.append(profile)
        return profile

    async def find_by_slug(self, slug):
        return None

    async def exists_by_slug(self, slug):
        return slug in self.existing_slugs


def _command(slug="kim-beauty"):
    return ProfileRegistrationCommand(
        slug=slug,
        name="김뷰티",
        tagline="20대 스킨케어·K뷰티 리뷰",
        bio="성분 분석 콘텐츠를 만듭니다.",
        location="서울",
        primary_category="뷰티",
    )


async def test_등록하면_심사대기_상태로_저장된다():
    repository = _StubRepository()
    result = await ProfileRegistrationInteractor(repository).register(_command())
    assert result.status == ProfileStatus.PENDING.value
    assert repository.created[0].slug == "kim-beauty"


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
