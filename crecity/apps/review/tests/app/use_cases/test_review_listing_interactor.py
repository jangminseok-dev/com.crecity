import pytest

from hub.app.dtos.creator_ref_dto import CreatorRef
from review.app.dtos.review_listing_dto import CreatorReviewsQuery
from review.app.exceptions import CreatorNotFoundError
from review.app.use_cases.review_listing_interactor import ReviewListingInteractor
from review.domain.entities.review_entity import Review

CREATOR = 200


class _StubCreatorRefPort:
    def __init__(self, ref: CreatorRef | None):
        self.ref = ref

    async def get_creator_by_slug(self, slug):
        return self.ref if self.ref and self.ref.slug == slug else None


class _StubReviewRepository:
    def __init__(self, reviews: list[Review]):
        self.reviews = reviews

    async def create(self, **kwargs):
        raise NotImplementedError

    async def find_by_order_id(self, order_id):
        raise NotImplementedError

    async def list_by_creator(self, creator_user_id):
        return [r for r in self.reviews if r.creator_user_id == creator_user_id]


def _review(id=1, communication=5, timeliness=4, satisfaction=3):
    return Review(
        id=id, order_id=id, brand_user_id=100, creator_user_id=CREATOR,
        communication_score=communication, timeliness_score=timeliness,
        satisfaction_score=satisfaction, comment="자세한 리뷰 본문",
    )


_REF = CreatorRef(creator_user_id=CREATOR, slug="kim-beauty", name="김뷰티")


def _interactor(reviews=None, ref=_REF):
    return ReviewListingInteractor(
        reviews=_StubReviewRepository(reviews if reviews is not None else [_review()]),
        creators=_StubCreatorRefPort(ref),
    )


async def test_로그인_사용자는_리뷰_원문을_본다():
    result = await _interactor().list_for_creator(
        CreatorReviewsQuery(slug="kim-beauty", viewer_logged_in=True)
    )
    assert result.items[0].comment == "자세한 리뷰 본문"
    assert result.items[0].is_locked is False


async def test_비로그인은_원문이_잠긴다_집계는_공개():
    result = await _interactor().list_for_creator(
        CreatorReviewsQuery(slug="kim-beauty", viewer_logged_in=False)
    )
    assert result.items[0].comment is None  # 블러 정책
    assert result.items[0].is_locked is True
    assert result.average_overall == 4.0  # 집계는 항상 공개
    assert result.average_communication == 5.0


async def test_집계는_전체_리뷰_평균이다():
    reviews = [_review(id=1, communication=5, timeliness=5, satisfaction=5),
               _review(id=2, communication=3, timeliness=3, satisfaction=3)]
    result = await _interactor(reviews=reviews).list_for_creator(
        CreatorReviewsQuery(slug="kim-beauty", viewer_logged_in=True)
    )
    assert result.total == 2
    assert result.average_overall == 4.0
    assert result.average_timeliness == 4.0


async def test_리뷰가_없으면_평균은_None():
    result = await _interactor(reviews=[]).list_for_creator(
        CreatorReviewsQuery(slug="kim-beauty", viewer_logged_in=False)
    )
    assert result.total == 0
    assert result.average_overall is None


async def test_없는_크리에이터면_CreatorNotFoundError():
    with pytest.raises(CreatorNotFoundError):
        await _interactor(ref=None).list_for_creator(
            CreatorReviewsQuery(slug="no-one", viewer_logged_in=False)
        )
