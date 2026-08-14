from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from review.app.dtos.review_reply_dto import ReviewReplyResult
from review.app.use_cases.review_reply_interactor import REPLY_MAX_LENGTH


class ReviewReplyRequestSchema(BaseModel):

    reply: str = Field(min_length=1, max_length=REPLY_MAX_LENGTH)


class ReviewReplyResponseSchema(BaseModel):

    review_id: int
    reply: str
    replied_at: datetime | None

    @classmethod
    def from_result(cls, result: ReviewReplyResult) -> ReviewReplyResponseSchema:
        return cls(
            review_id=result.review_id, reply=result.reply, replied_at=result.replied_at
        )
