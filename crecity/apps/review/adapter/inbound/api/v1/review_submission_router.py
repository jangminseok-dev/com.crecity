from fastapi import APIRouter, Depends, HTTPException

from hub.app.dtos.verified_user_dto import VerifiedUser
from hub.dependencies.current_user_provider import get_current_user
from review.adapter.inbound.api.schemas.review_submission_schema import (
    ReviewResponseSchema,
    ReviewSubmissionRequestSchema,
)
from review.app.dtos.review_submission_dto import ReviewSubmissionCommand
from review.app.exceptions import (
    NotOrderBrandError,
    OrderNotCompletedError,
    OrderNotFoundError,
    ReviewAlreadyExistsError,
    ReviewNotFoundError,
)
from review.app.ports.input.review_submission_use_case import ReviewSubmissionUseCase
from review.dependencies.review_submission_provider import get_review_submission_use_case
from review.domain.entities.review_entity import InvalidScoreError

review_submission_router = APIRouter(prefix="/review", tags=["review"])


def _to_schema(result) -> ReviewResponseSchema:
    return ReviewResponseSchema(
        id=result.id,
        order_id=result.order_id,
        communication_score=result.communication_score,
        timeliness_score=result.timeliness_score,
        satisfaction_score=result.satisfaction_score,
        overall_score=result.overall_score,
        comment=result.comment,
        created_at=result.created_at,
    )


@review_submission_router.post(
    "/orders/{order_id}/review", response_model=ReviewResponseSchema, status_code=201
)
async def submit_review(
    order_id: int,
    body: ReviewSubmissionRequestSchema,
    user: VerifiedUser = Depends(get_current_user),
    use_case: ReviewSubmissionUseCase = Depends(get_review_submission_use_case),
) -> ReviewResponseSchema:
    try:
        result = await use_case.submit(
            ReviewSubmissionCommand(
                order_id=order_id,
                requester_user_id=user.id,
                communication_score=body.communication_score,
                timeliness_score=body.timeliness_score,
                satisfaction_score=body.satisfaction_score,
                comment=body.comment,
            )
        )
    except OrderNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except NotOrderBrandError as error:
        raise HTTPException(status_code=403, detail=str(error))
    except (OrderNotCompletedError, ReviewAlreadyExistsError) as error:
        raise HTTPException(status_code=409, detail=str(error))
    except InvalidScoreError as error:
        raise HTTPException(status_code=422, detail=str(error))
    return _to_schema(result)


@review_submission_router.get("/orders/{order_id}/review", response_model=ReviewResponseSchema)
async def get_order_review(
    order_id: int,
    user: VerifiedUser = Depends(get_current_user),
    use_case: ReviewSubmissionUseCase = Depends(get_review_submission_use_case),
) -> ReviewResponseSchema:
    try:
        result = await use_case.get_order_review(order_id, user.id)
    except ReviewNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    return _to_schema(result)
