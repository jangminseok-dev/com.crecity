from creator.app.dtos.popular_profiles_dto import PopularProfilesQuery
from creator.app.use_cases.popular_profiles_interactor import PopularProfilesInteractor
from creator.domain.entities.creator_profile_entity import CreatorProfile, ProfileStatus
from hub.app.dtos.creator_popularity_dto import CreatorOrderCount
from hub.app.dtos.creator_rating_dto import CreatorRatingSummary


class _StubRepository:
    def __init__(self, profiles: list[CreatorProfile]):
        self.profiles = profiles
        self.calls: list[dict] = []

    async def list_by_user_ids(self, user_ids, status):
        self.calls.append({"user_ids": user_ids, "status": status})
        return [p for p in self.profiles if p.user_id in user_ids and p.status is status]


class _StubPackages:
    async def min_prices_by_profile_ids(self, profile_ids):
        return {}


class _StubPortfolio:
    async def first_file_names_by_profile_ids(self, profile_ids):
        return {}


class _StubRatings:
    def __init__(self, summaries=None):
        self.summaries = summaries or {}

    async def get_rating_summaries(self, creator_user_ids):
        return {uid: s for uid, s in self.summaries.items() if uid in creator_user_ids}


class _StubPopularity:
    def __init__(self, ranking: list[CreatorOrderCount]):
        self.ranking = ranking
        self.calls: list[dict] = []

    async def top_creators_by_recent_orders(self, days, limit):
        self.calls.append({"days": days, "limit": limit})
        return self.ranking[:limit]


def _profile(id, user_id, slug, status=ProfileStatus.APPROVED):
    return CreatorProfile(
        id=id,
        slug=slug,
        name=f"크리에이터{id}",
        tagline="소개",
        bio="상세",
        location=None,
        primary_category="뷰티",
        status=status,
        user_id=user_id,
    )


def _interactor(repository, popularity, ratings=None):
    return PopularProfilesInteractor(
        repository=repository,
        packages=_StubPackages(),
        portfolio=_StubPortfolio(),
        ratings=ratings or _StubRatings(),
        popularity=popularity,
    )


async def test_주문_수_순위_순서를_유지한다():
    repository = _StubRepository(
        [_profile(1, 101, "a"), _profile(2, 102, "b"), _profile(3, 103, "c")]
    )
    popularity = _StubPopularity(
        [
            CreatorOrderCount(creator_user_id=103, order_count=9),
            CreatorOrderCount(creator_user_id=101, order_count=5),
            CreatorOrderCount(creator_user_id=102, order_count=2),
        ]
    )
    result = await _interactor(repository, popularity).list_popular(PopularProfilesQuery(limit=3))
    assert [item.slug for item in result] == ["c", "a", "b"]


async def test_미승인_프로필은_건너뛰고_limit을_지킨다():
    repository = _StubRepository(
        [
            _profile(1, 101, "a", status=ProfileStatus.PENDING),
            _profile(2, 102, "b"),
            _profile(3, 103, "c"),
        ]
    )
    popularity = _StubPopularity(
        [
            CreatorOrderCount(creator_user_id=101, order_count=9),
            CreatorOrderCount(creator_user_id=102, order_count=5),
            CreatorOrderCount(creator_user_id=103, order_count=2),
        ]
    )
    result = await _interactor(repository, popularity).list_popular(PopularProfilesQuery(limit=2))
    assert [item.slug for item in result] == ["b", "c"]  # PENDING 제외
    # 여유 조회(limit*3)로 미승인이 섞여도 채운다
    assert popularity.calls[0]["limit"] == 6


async def test_순위가_비면_빈_목록():
    result = await _interactor(_StubRepository([]), _StubPopularity([])).list_popular(
        PopularProfilesQuery(limit=4)
    )
    assert result == []


async def test_평점_보강을_병합한다():
    repository = _StubRepository([_profile(1, 101, "a")])
    popularity = _StubPopularity([CreatorOrderCount(creator_user_id=101, order_count=3)])
    ratings = _StubRatings(
        {101: CreatorRatingSummary(creator_user_id=101, average_overall=4.8, review_count=12)}
    )
    result = await _interactor(repository, popularity, ratings).list_popular(
        PopularProfilesQuery(limit=4)
    )
    assert result[0].rating_avg == 4.8
    assert result[0].rating_count == 12
