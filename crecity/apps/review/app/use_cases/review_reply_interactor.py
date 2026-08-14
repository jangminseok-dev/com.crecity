from __future__ import annotations

from review.app.dtos.review_reply_dto import ReviewReplyCommand, ReviewReplyResult
from review.app.exceptions import ReviewNotFoundError
from review.app.ports.input.review_reply_use_case import ReviewReplyUseCase
from review.app.ports.output.review_repository import ReviewRepository

REPLY_MAX_LENGTH = 1000


class ReviewReplyInteractor(ReviewReplyUseCase):

    def __init__(self, reviews: ReviewRepository) -> None:
        self._reviews = reviews

    async def reply(self, command: ReviewReplyCommand) -> ReviewReplyResult:
        review = await self._reviews.find_by_id(command.review_id)
        if review is None:
            raise ReviewNotFoundError(f"리뷰를 찾을 수 없습니다: {command.review_id}")
        # 자격·중복 판단은 도메인이 한다(403/409 변환은 라우터 몫)
        review.ensure_can_reply(command.requester_user_id)

        saved = await self._reviews.save_reply(command.review_id, command.reply.strip())
        if saved is None:
            raise ReviewNotFoundError(f"리뷰를 찾을 수 없습니다: {command.review_id}")
        return ReviewReplyResult(
            review_id=saved.id, reply=saved.reply, replied_at=saved.replied_at
        )
