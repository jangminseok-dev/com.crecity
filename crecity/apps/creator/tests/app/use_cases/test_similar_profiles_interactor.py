import pytest

from creator.app.dtos.similar_profiles_dto import SimilarProfilesQuery
from creator.app.exceptions import ProfileNotFoundError
from creator.app.use_cases.similar_profiles_interactor import SimilarProfilesInteractor
from creator.domain.entities.creator_profile_entity import CreatorProfile, ProfileStatus


class _StubRepository:
    def __init__(self, profiles: list[CreatorProfile]):
        self.profiles = profiles
        self.list_calls: list[dict] = []

    async def find_by_slug(self, slug):
        return next((p for p in self.profiles if p.slug == slug), None)

    async def list_by_status(self, status, category, limit, offset, **kwargs):
        self.list_calls.append({"status": status, "category": category, "limit": limit})
        return [
            p
            for p in self.profiles
            if p.status is status and p.primary_category == category
        ][:limit]


class _StubPackages:
    def __init__(self, prices=None, platforms=None):
        self.prices = prices or {}
        self.platforms = platforms or {}

    async def min_prices_by_profile_ids(self, profile_ids):
        return {pid: price for pid, price in self.prices.items() if pid in profile_ids}

    async def platforms_by_profile_ids(self, profile_ids):
        return {pid: ps for pid, ps in self.platforms.items() if pid in profile_ids}


class _StubPortfolio:
    async def first_file_names_by_profile_ids(self, profile_ids):
        return {}


class _StubRatings:
    async def get_rating_summaries(self, creator_user_ids):
        return {}


def _profile(id, slug, category="뷰티", status=ProfileStatus.APPROVED):
    return CreatorProfile(
        id=id,
        slug=slug,
        name=f"크리에이터{id}",
        tagline="소개",
        bio="상세",
        location=None,
        primary_category=category,
        status=status,
        user_id=100 + id,
    )


def _interactor(repository, packages=None):
    return SimilarProfilesInteractor(
        repository=repository,
        packages=packages or _StubPackages(),
        portfolio=_StubPortfolio(),
        ratings=_StubRatings(),
    )


async def test_없는_슬러그는_404_예외():
    with pytest.raises(ProfileNotFoundError):
        await _interactor(_StubRepository([])).list_similar(
            SimilarProfilesQuery(slug="ghost", limit=4)
        )


async def test_탈퇴_프로필도_404_예외():
    repository = _StubRepository([_profile(1, "gone", status=ProfileStatus.DELETED)])
    with pytest.raises(ProfileNotFoundError):
        await _interactor(repository).list_similar(SimilarProfilesQuery(slug="gone", limit=4))


async def test_같은_카테고리에서_자신을_제외한다():
    repository = _StubRepository(
        [
            _profile(1, "target"),
            _profile(2, "same-a"),
            _profile(3, "other", category="여행"),
        ]
    )
    result = await _interactor(repository).list_similar(SimilarProfilesQuery(slug="target", limit=4))
    assert [item.slug for item in result] == ["same-a"]
    assert repository.list_calls[0]["category"] == "뷰티"


async def test_가격이_가까운_순으로_정렬한다():
    repository = _StubRepository(
        [_profile(1, "target"), _profile(2, "far"), _profile(3, "near"), _profile(4, "no-price")]
    )
    packages = _StubPackages(prices={1: 300_000, 2: 900_000, 3: 350_000})
    result = await _interactor(repository, packages).list_similar(
        SimilarProfilesQuery(slug="target", limit=4)
    )
    # 가격 차: near 5만 < far 60만 < no-price(가격 없음 — 항상 뒤)
    assert [item.slug for item in result] == ["near", "far", "no-price"]


async def test_플랫폼이_겹치는_프로필이_가격보다_우선한다():
    repository = _StubRepository(
        [_profile(1, "target"), _profile(2, "same-platform"), _profile(3, "closer-price")]
    )
    packages = _StubPackages(
        prices={1: 300_000, 2: 800_000, 3: 310_000},
        platforms={1: {"INSTAGRAM"}, 2: {"INSTAGRAM", "YOUTUBE"}, 3: {"TIKTOK"}},
    )
    result = await _interactor(repository, packages).list_similar(
        SimilarProfilesQuery(slug="target", limit=4)
    )
    assert [item.slug for item in result] == ["same-platform", "closer-price"]


async def test_타깃_가격이_없으면_가격_비교_없이_플랫폼과_최신순():
    repository = _StubRepository(
        [_profile(1, "target"), _profile(2, "old"), _profile(3, "recent")]
    )
    packages = _StubPackages(prices={2: 100_000, 3: 900_000})  # 타깃(1)은 패키지 없음
    result = await _interactor(repository, packages).list_similar(
        SimilarProfilesQuery(slug="target", limit=4)
    )
    # 가격 차를 만들지 않고 id 내림차순(최신 프로필 우선)
    assert [item.slug for item in result] == ["recent", "old"]


async def test_limit을_지키고_최저가를_카드에_싣는다():
    repository = _StubRepository(
        [_profile(1, "target"), _profile(2, "a"), _profile(3, "b"), _profile(4, "c")]
    )
    packages = _StubPackages(prices={1: 300_000, 2: 310_000, 3: 320_000, 4: 330_000})
    result = await _interactor(repository, packages).list_similar(
        SimilarProfilesQuery(slug="target", limit=2)
    )
    assert len(result) == 2
    assert result[0].price_from == 310_000
