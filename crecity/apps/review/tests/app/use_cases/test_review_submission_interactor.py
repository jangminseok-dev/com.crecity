import pytest

from hub.app.dtos.creator_ref_dto import CreatorRef
from hub.app.dtos.order_participants_dto import OrderParticipants
from review.app.dtos.review_submission_dto import ReviewSubmissionCommand
from review.app.exceptions import (
    NotOrderBrandError,
    OrderNotCompletedError,
    OrderNotFoundError,
    ReviewAlreadyExistsError,
)
from review.app.use_cases.review_submission_interactor import ReviewSubmissionInteractor
from review.domain.entities.review_entity import InvalidScoreError, Review

BRAND, CREATOR = 100, 200
_REF = CreatorRef(creator_user_id=CREATOR, slug="kim-beauty", name="김뷰티")


class _StubOrderParticipantsPort:
    def __init__(self, order: OrderParticipants | None):
        self.order = order

    async def get_order_participants(self, order_id):
        return self.order if self.order and self.order.order_id == order_id else None


class _StubReviewRepository:
    def __init__(self, existing: Review | None = None):
        self.published: list = []          # 함께 적재된 알림 이벤트(갭 #75)
        self.existing = existing
        self.created = []

    async def create(self, order_id, brand_user_id, creator_user_id,
                     communication_score, timeliness_score, satisfaction_score, comment,
                     events=None):
        self.published += list(events or [])
        review = Review(
            id=1, order_id=order_id, brand_user_id=brand_user_id,
            creator_user_id=creator_user_id, communication_score=communication_score,
            timeliness_score=timeliness_score, satisfaction_score=satisfaction_score,
            comment=comment,
        )
        self.created.append(review)
        return review

    async def find_by_order_id(self, order_id):
        return self.existing if self.existing and self.existing.order_id == order_id else None

    async def list_by_creator(self, creator_user_id):
        raise NotImplementedError


class _StubCreators:
    def __init__(self, ref: CreatorRef | None = _REF):
        self.ref = ref

    async def get_creator_by_slug(self, slug):
        raise NotImplementedError

    async def get_creator_by_user_id(self, user_id):
        return self.ref


def _order(status="COMPLETED"):
    return OrderParticipants(order_id=10, status=status, brand_user_id=BRAND, creator_user_id=CREATOR)


def _command(requester=BRAND, communication=5):
    return ReviewSubmissionCommand(
        order_id=10, requester_user_id=requester,
        communication_score=communication, timeliness_score=4, satisfaction_score=5,
        comment="소통이 빨랐고 결과물도 좋았습니다.",
    )


async def test_완료_주문의_브랜드가_리뷰를_작성한다():
    repo = _StubReviewRepository()
    interactor = ReviewSubmissionInteractor(repo, _StubOrderParticipantsPort(_order()), _StubCreators())
    result = await interactor.submit(_command())
    assert result.overall_score == 4.7
    assert repo.created[0].creator_user_id == CREATOR  # 대상은 주문의 크리에이터


async def test_완료되지_않은_주문이면_OrderNotCompletedError():
    interactor = ReviewSubmissionInteractor(
        _StubReviewRepository(), _StubOrderParticipantsPort(_order(status="IN_REVIEW")),
        _StubCreators(),
    )
    with pytest.raises(OrderNotCompletedError):
        await interactor.submit(_command())


async def test_브랜드가_아니면_NotOrderBrandError():
    interactor = ReviewSubmissionInteractor(
        _StubReviewRepository(), _StubOrderParticipantsPort(_order()), _StubCreators()
    )
    with pytest.raises(NotOrderBrandError):
        await interactor.submit(_command(requester=CREATOR))


async def test_이미_리뷰가_있으면_ReviewAlreadyExistsError():
    existing = Review(
        id=9, order_id=10, brand_user_id=BRAND, creator_user_id=CREATOR,
        communication_score=5, timeliness_score=5, satisfaction_score=5, comment="이전 리뷰",
    )
    interactor = ReviewSubmissionInteractor(
        _StubReviewRepository(existing), _StubOrderParticipantsPort(_order()), _StubCreators()
    )
    with pytest.raises(ReviewAlreadyExistsError):
        await interactor.submit(_command())


async def test_없는_주문이면_OrderNotFoundError():
    interactor = ReviewSubmissionInteractor(
        _StubReviewRepository(), _StubOrderParticipantsPort(None), _StubCreators()
    )
    with pytest.raises(OrderNotFoundError):
        await interactor.submit(_command())


async def test_평점_범위_위반이면_InvalidScoreError_저장_없음():
    repo = _StubReviewRepository()
    interactor = ReviewSubmissionInteractor(repo, _StubOrderParticipantsPort(_order()), _StubCreators())
    with pytest.raises(InvalidScoreError):
        await interactor.submit(_command(communication=6))
    assert repo.created == []


async def test_리뷰를_받으면_크리에이터에게_알림이_간다():
    """답글(갭 #53)을 달 계기가 없으면 답글 기능이 죽는다(갭 #75)."""
    repo = _StubReviewRepository()
    interactor = ReviewSubmissionInteractor(
        repo, _StubOrderParticipantsPort(_order()), _StubCreators()
    )
    await interactor.submit(_command())
    assert len(repo.published) == 1
    event = repo.published[0]
    assert event.event_type == "review.received"
    assert event.payload["creator_user_id"] == CREATOR
    assert event.payload["creator_slug"] == "kim-beauty"


async def test_프로필이_없으면_리뷰_알림을_보내지_않는다():
    """링크할 공개 프로필이 없으면 알림이 갈 곳도 없다."""
    repo = _StubReviewRepository()
    interactor = ReviewSubmissionInteractor(
        repo, _StubOrderParticipantsPort(_order()), _StubCreators(ref=None)
    )
    await interactor.submit(_command())
    assert repo.published == []
    assert len(repo.created) == 1  # 리뷰 저장은 그대로 된다
