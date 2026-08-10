from creator.app.dtos.profile_listing_dto import ProfileListingQuery
from creator.app.use_cases.profile_listing_interactor import ProfileListingInteractor
from creator.domain.entities.creator_profile_entity import CreatorProfile, ProfileStatus


class _StubRepository:
    def __init__(self, profiles: list[CreatorProfile] | None = None):
        self.profiles = profiles or []
        self.list_calls: list[dict] = []
        self.count_calls: list[dict] = []

    async def create(self, **kwargs):
        raise NotImplementedError

    async def find_by_slug(self, slug):
        raise NotImplementedError

    async def exists_by_slug(self, slug):
        raise NotImplementedError

    async def list_by_status(self, status, category, limit, offset):
        self.list_calls.append(
            {"status": status, "category": category, "limit": limit, "offset": offset}
        )
        return self.profiles

    async def count_by_status(self, status, category):
        self.count_calls.append({"status": status, "category": category})
        return len(self.profiles)


def _profile(id=1, slug="kim-beauty", category="뷰티"):
    return CreatorProfile(
        id=id,
        slug=slug,
        name="김뷰티",
        tagline="20대 스킨케어·K뷰티 리뷰",
        bio="성분 분석 콘텐츠를 만듭니다.",
        location="서울",
        primary_category=category,
        status=ProfileStatus.APPROVED,
    )


async def test_승인된_프로필만_조회하도록_위임한다():
    repository = _StubRepository(profiles=[_profile()])
    interactor = ProfileListingInteractor(repository)
    result = await interactor.list_profiles(
        ProfileListingQuery(category=None, limit=20, offset=0)
    )
    assert repository.list_calls == [
        {"status": ProfileStatus.APPROVED, "category": None, "limit": 20, "offset": 0}
    ]
    assert repository.count_calls == [{"status": ProfileStatus.APPROVED, "category": None}]
    assert len(result.items) == 1
    assert result.items[0].slug == "kim-beauty"
    assert result.total == 1


async def test_카테고리_필터를_그대로_전달한다():
    repository = _StubRepository(profiles=[_profile(category="뷰티")])
    interactor = ProfileListingInteractor(repository)
    await interactor.list_profiles(ProfileListingQuery(category="뷰티", limit=10, offset=5))
    assert repository.list_calls[0]["category"] == "뷰티"
    assert repository.list_calls[0]["limit"] == 10
    assert repository.list_calls[0]["offset"] == 5
    assert repository.count_calls[0]["category"] == "뷰티"


async def test_결과가_없으면_빈_목록과_total_0을_반환한다():
    interactor = ProfileListingInteractor(_StubRepository(profiles=[]))
    result = await interactor.list_profiles(
        ProfileListingQuery(category=None, limit=20, offset=0)
    )
    assert result.items == []
    assert result.total == 0


async def test_목록_항목은_bio_없이_카드_필드만_담는다():
    interactor = ProfileListingInteractor(_StubRepository(profiles=[_profile()]))
    result = await interactor.list_profiles(
        ProfileListingQuery(category=None, limit=20, offset=0)
    )
    item = result.items[0]
    assert item.name == "김뷰티"
    assert item.tagline == "20대 스킨케어·K뷰티 리뷰"
    assert item.primary_category == "뷰티"
    assert not hasattr(item, "bio")
