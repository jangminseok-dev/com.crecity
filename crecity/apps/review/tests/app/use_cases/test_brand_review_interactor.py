import pytest

from hub.app.dtos.order_participants_dto import OrderParticipants
from review.app.dtos.brand_review_dto import (
    BrandRatingResult,
    BrandReviewResult,
    BrandReviewSubmissionCommand,
)
from review.app.exceptions import (
    NotOrderCreatorError,
    OrderNotCompletedError,
    OrderNotFoundError,
    ReviewAlreadyExistsError,
)
from review.app.use_cases.brand_review_interactor import BrandReviewInteractor
from review.domain.entities.review_entity import InvalidScoreError

BRAND, CREATOR = 100, 200


class _StubOrders:
    def __init__(self, order: OrderParticipants | None):
        self.order = order

    async def get_order_participants(self, order_id):
        return self.order


class _StubBrandReviews:
    def __init__(self, existing: BrandReviewResult | None = None):
        self.existing = existing
        self.created = []  # (kwargs, events)

    async def create(self, order_id, brand_user_id, creator_user_id, score, comment, events=None):
        self.created.append((order_id, brand_user_id, score, events))
        return BrandReviewResult(
            id=1, order_id=order_id, score=score, comment=comment, created_at=None
        )

    async def find_by_order_id(self, order_id):
        return self.existing

    async def get_brand_rating(self, brand_user_id):
        return BrandRatingResult(average_score=4.5, total=2)


def _order(status="COMPLETED"):
    return OrderParticipants(
        order_id=7, status=status, brand_user_id=BRAND, creator_user_id=CREATOR
    )


def _command(score=5, requester=CREATOR):
    return BrandReviewSubmissionCommand(
        order_id=7, requester_user_id=requester, score=score, comment="소통이 명확했습니다"
    )


async def test_완료_주문의_크리에이터가_브랜드를_평가한다():
    reviews = _StubBrandReviews()
    result = await BrandReviewInteractor(reviews, _StubOrders(_order())).submit(_command())
    assert result.score == 5
    order_id, brand_id, score, events = reviews.created[0]
    assert (order_id, brand_id) == (7, BRAND)
    # 평가받은 사실은 브랜드에게 알린다 — 저장과 같은 트랜잭션에 실린다
    assert events[0].event_type == "review.brand_received"
    assert events[0].payload["brand_user_id"] == BRAND


async def test_브랜드_본인은_평가할_수_없다():
    with pytest.raises(NotOrderCreatorError):
        await BrandReviewInteractor(_StubBrandReviews(), _StubOrders(_order())).submit(
            _command(requester=BRAND)
        )


async def test_완료_전_주문은_평가할_수_없다():
    with pytest.raises(OrderNotCompletedError):
        await BrandReviewInteractor(
            _StubBrandReviews(), _StubOrders(_order(status="IN_REVIEW"))
        ).submit(_command())


async def test_중복_평가는_거부된다():
    existing = BrandReviewResult(id=1, order_id=7, score=4, comment="", created_at=None)
    with pytest.raises(ReviewAlreadyExistsError):
        await BrandReviewInteractor(_StubBrandReviews(existing), _StubOrders(_order())).submit(
            _command()
        )


async def test_없는_주문이면_OrderNotFoundError():
    with pytest.raises(OrderNotFoundError):
        await BrandReviewInteractor(_StubBrandReviews(), _StubOrders(None)).submit(_command())


async def test_점수_범위를_벗어나면_거부된다():
    with pytest.raises(InvalidScoreError):
        await BrandReviewInteractor(_StubBrandReviews(), _StubOrders(_order())).submit(
            _command(score=6)
        )
