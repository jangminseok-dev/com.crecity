import pytest

from review.app.dtos.review_reply_dto import ReviewReplyCommand
from review.app.exceptions import ReviewNotFoundError
from review.app.use_cases.review_reply_interactor import ReviewReplyInteractor
from review.domain.entities.review_entity import (
    ReplyAlreadyExistsError,
    ReplyNotAllowedError,
    Review,
)

CREATOR_ID = 22
BRAND_ID = 11


def _review(reply: str = "") -> Review:
    return Review(
        id=1,
        order_id=5,
        brand_user_id=BRAND_ID,
        creator_user_id=CREATOR_ID,
        communication_score=5,
        timeliness_score=4,
        satisfaction_score=5,
        comment="결과물이 기대 이상이었어요.",
        reply=reply,
    )


class _StubReviews:
    def __init__(self, review: Review | None = None):
        self.review = review
        self.saved: list[tuple[int, str]] = []

    async def find_by_id(self, review_id: int) -> Review | None:
        return self.review

    async def save_reply(self, review_id: int, reply: str) -> Review | None:
        self.saved.append((review_id, reply))
        assert self.review is not None
        from dataclasses import replace

        self.review = replace(self.review, reply=reply)
        return self.review


async def test_대상_크리에이터는_답글을_남긴다():
    reviews = _StubReviews(_review())
    result = await ReviewReplyInteractor(reviews=reviews).reply(
        ReviewReplyCommand(review_id=1, requester_user_id=CREATOR_ID, reply="  감사합니다!  ")
    )
    # 앞뒤 공백은 저장 전에 정리한다
    assert reviews.saved == [(1, "감사합니다!")]
    assert result.reply == "감사합니다!"
    assert result.review_id == 1


async def test_브랜드는_답글을_남길_수_없다():
    reviews = _StubReviews(_review())
    with pytest.raises(ReplyNotAllowedError):
        await ReviewReplyInteractor(reviews=reviews).reply(
            ReviewReplyCommand(review_id=1, requester_user_id=BRAND_ID, reply="답글")
        )
    assert reviews.saved == []


async def test_이미_답글이_있으면_거부한다():
    reviews = _StubReviews(_review(reply="이미 남긴 답글"))
    with pytest.raises(ReplyAlreadyExistsError):
        await ReviewReplyInteractor(reviews=reviews).reply(
            ReviewReplyCommand(review_id=1, requester_user_id=CREATOR_ID, reply="또 남기기")
        )
    assert reviews.saved == []


async def test_없는_리뷰면_404_예외():
    with pytest.raises(ReviewNotFoundError):
        await ReviewReplyInteractor(reviews=_StubReviews(None)).reply(
            ReviewReplyCommand(review_id=999, requester_user_id=CREATOR_ID, reply="답글")
        )
