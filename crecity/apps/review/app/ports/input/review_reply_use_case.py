from __future__ import annotations

from abc import ABC, abstractmethod

from review.app.dtos.review_reply_dto import ReviewReplyCommand, ReviewReplyResult


class ReviewReplyUseCase(ABC):
    """리뷰 답글(갭 #53) — 받은 크리에이터가 한 번 해명·감사를 남긴다."""

    @abstractmethod
    async def reply(self, command: ReviewReplyCommand) -> ReviewReplyResult: ...
