from fastapi import APIRouter, Depends, HTTPException

from hub.app.dtos.verified_user_dto import VerifiedUser
from hub.dependencies.current_user_provider import get_current_user
from review.adapter.inbound.api.schemas.review_reply_schema import (
    ReviewReplyRequestSchema,
    ReviewReplyResponseSchema,
)
from review.app.dtos.review_reply_dto import ReviewReplyCommand
from review.app.exceptions import ReviewNotFoundError
from review.app.ports.input.review_reply_use_case import ReviewReplyUseCase
from review.dependencies.review_reply_provider import get_review_reply_use_case
from review.domain.entities.review_entity import ReplyAlreadyExistsError, ReplyNotAllowedError

review_reply_router = APIRouter(prefix="/review", tags=["review"])


@review_reply_router.post(
    "/reviews/{review_id}/reply", response_model=ReviewReplyResponseSchema, status_code=201
)
async def reply_to_review(
    review_id: int,
    body: ReviewReplyRequestSchema,
    user: VerifiedUser = Depends(get_current_user),
    use_case: ReviewReplyUseCase = Depends(get_review_reply_use_case),
) -> ReviewReplyResponseSchema:
    """리뷰 답글(갭 #53) — 대상 크리에이터만, 리뷰당 1회."""
    try:
        result = await use_case.reply(
            ReviewReplyCommand(
                review_id=review_id, requester_user_id=user.id, reply=body.reply
            )
        )
    except ReviewNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ReplyNotAllowedError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except ReplyAlreadyExistsError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return ReviewReplyResponseSchema.from_result(result)
