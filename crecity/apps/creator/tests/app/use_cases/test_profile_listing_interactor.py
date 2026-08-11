from creator.app.dtos.profile_listing_dto import ProfileListingQuery
from creator.app.use_cases.profile_listing_interactor import ProfileListingInteractor
from creator.domain.entities.creator_profile_entity import CreatorProfile, ProfileStatus
from hub.app.dtos.creator_rating_dto import CreatorRatingSummary


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

    async def list_by_status(self, status, category, limit, offset, q=None):
        self.list_calls.append(
            {"status": status, "category": category, "limit": limit, "offset": offset, "q": q}
        )
        return self.profiles

    async def count_by_status(self, status, category, q=None):
        self.count_calls.append({"status": status, "category": category, "q": q})
        return len(self.profiles)

    async def list_categories(self, status):
        return sorted({p.primary_category for p in self.profiles})


class _StubPackages:
    def __init__(self, min_prices: dict[int, int] | None = None):
        self.min_prices = min_prices or {}
        self.calls: list[list[int]] = []

    async def min_prices_by_profile_ids(self, profile_ids):
        self.calls.append(profile_ids)
        return {pid: price for pid, price in self.min_prices.items() if pid in profile_ids}


class _StubPortfolio:
    def __init__(self, covers: dict[int, str] | None = None):
        self.covers = covers or {}
        self.calls: list[list[int]] = []

    async def first_file_names_by_profile_ids(self, profile_ids):
        self.calls.append(profile_ids)
        return {pid: name for pid, name in self.covers.items() if pid in profile_ids}


class _StubRatings:
    def __init__(self, summaries: dict[int, CreatorRatingSummary] | None = None):
        self.summaries = summaries or {}
        self.calls: list[list[int]] = []

    async def get_rating_summaries(self, creator_user_ids):
        self.calls.append(creator_user_ids)
        return {uid: s for uid, s in self.summaries.items() if uid in creator_user_ids}


def _interactor(
    repository=None, packages=None, portfolio=None, ratings=None
) -> ProfileListingInteractor:
    return ProfileListingInteractor(
        repository=repository or _StubRepository(),
        packages=packages or _StubPackages(),
        portfolio=portfolio or _StubPortfolio(),
        ratings=ratings or _StubRatings(),
    )


def _profile(id=1, slug="kim-beauty", category="뷰티", user_id=101):
    return CreatorProfile(
        id=id,
        slug=slug,
        name="김뷰티",
        tagline="20대 스킨케어·K뷰티 리뷰",
        bio="성분 분석 콘텐츠를 만듭니다.",
        location="서울",
        primary_category=category,
        status=ProfileStatus.APPROVED,
        user_id=user_id,
    )


async def test_승인된_프로필만_조회하도록_위임한다():
    repository = _StubRepository(profiles=[_profile()])
    interactor = _interactor(repository=repository)
    result = await interactor.list_profiles(
        ProfileListingQuery(category=None, q=None, limit=20, offset=0)
    )
    assert repository.list_calls == [
        {"status": ProfileStatus.APPROVED, "category": None, "limit": 20, "offset": 0, "q": None}
    ]
    assert repository.count_calls == [{"status": ProfileStatus.APPROVED, "category": None, "q": None}]
    assert len(result.items) == 1
    assert result.items[0].slug == "kim-beauty"
    assert result.total == 1


async def test_카테고리_필터를_그대로_전달한다():
    repository = _StubRepository(profiles=[_profile(category="뷰티")])
    interactor = _interactor(repository=repository)
    await interactor.list_profiles(ProfileListingQuery(category="뷰티", q=None, limit=10, offset=5))
    assert repository.list_calls[0]["category"] == "뷰티"
    assert repository.list_calls[0]["limit"] == 10
    assert repository.list_calls[0]["offset"] == 5
    assert repository.count_calls[0]["category"] == "뷰티"


async def test_결과가_없으면_빈_목록과_total_0을_반환한다():
    result = await _interactor().list_profiles(
        ProfileListingQuery(category=None, q=None, limit=20, offset=0)
    )
    assert result.items == []
    assert result.total == 0


async def test_목록_항목은_bio_없이_카드_필드만_담는다():
    interactor = _interactor(repository=_StubRepository(profiles=[_profile()]))
    result = await interactor.list_profiles(
        ProfileListingQuery(category=None, q=None, limit=20, offset=0)
    )
    item = result.items[0]
    assert item.name == "김뷰티"
    assert item.tagline == "20대 스킨케어·K뷰티 리뷰"
    assert item.primary_category == "뷰티"


async def test_카드_보강_필드를_프로필별로_병합한다():
    profiles = [_profile(id=1, slug="a", user_id=101), _profile(id=2, slug="b", user_id=102)]
    interactor = _interactor(
        repository=_StubRepository(profiles=profiles),
        packages=_StubPackages(min_prices={1: 350_000}),
        portfolio=_StubPortfolio(covers={2: "cover-b.webp"}),
        ratings=_StubRatings(
            summaries={
                101: CreatorRatingSummary(creator_user_id=101, average_overall=4.9, review_count=87)
            }
        ),
    )
    result = await interactor.list_profiles(
        ProfileListingQuery(category=None, q=None, limit=20, offset=0)
    )
    first, second = result.items
    assert first.price_from == 350_000
    assert first.cover_file_name is None
    assert first.rating_avg == 4.9
    assert first.rating_count == 87
    assert second.price_from is None
    assert second.cover_file_name == "cover-b.webp"
    assert second.rating_avg is None
    assert second.rating_count == 0


async def test_user_id_없는_레거시_프로필은_평점_조회에서_제외한다():
    profiles = [_profile(id=1, user_id=None), _profile(id=2, slug="b", user_id=102)]
    ratings = _StubRatings()
    interactor = _interactor(repository=_StubRepository(profiles=profiles), ratings=ratings)
    result = await interactor.list_profiles(
        ProfileListingQuery(category=None, q=None, limit=20, offset=0)
    )
    assert ratings.calls == [[102]]
    assert result.items[0].rating_avg is None
