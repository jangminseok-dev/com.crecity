from fastapi import APIRouter, Depends, HTTPException

from hub.app.dtos.verified_user_dto import VerifiedUser
from hub.dependencies.current_user_provider import get_current_user
from review.adapter.inbound.api.schemas.brand_review_schema import (
    BrandRatingResponseSchema,
    BrandReviewResponseSchema,
    BrandReviewSubmissionSchema,
)
from review.app.dtos.brand_review_dto import BrandReviewSubmissionCommand
from review.app.exceptions import (
    NotOrderCreatorError,
    OrderNotCompletedError,
    OrderNotFoundError,
    ReviewAlreadyExistsError,
    ReviewNotFoundError,
)
from review.app.ports.input.brand_review_use_case import BrandReviewUseCase
from review.domain.entities.review_entity import InvalidScoreError
from review.dependencies.brand_review_provider import get_brand_review_use_case

brand_review_router = APIRouter(prefix="/review", tags=["review"])


@brand_review_router.post(
    "/orders/{order_id}/brand-review", response_model=BrandReviewResponseSchema, status_code=201
)
async def submit_brand_review(
    order_id: int,
    body: BrandReviewSubmissionSchema,
    user: VerifiedUser = Depends(get_current_user),
    use_case: BrandReviewUseCase = Depends(get_brand_review_use_case),
) -> BrandReviewResponseSchema:
    """브랜드 평가(갭 #83) — 완료 주문의 크리에이터만, 주문당 1회."""
    try:
        result = await use_case.submit(
            BrandReviewSubmissionCommand(
                order_id=order_id,
                requester_user_id=user.id,
                score=body.score,
                comment=body.comment,
            )
        )
    except OrderNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except NotOrderCreatorError as error:
        raise HTTPException(status_code=403, detail=str(error))
    except (OrderNotCompletedError, ReviewAlreadyExistsError) as error:
        raise HTTPException(status_code=409, detail=str(error))
    except InvalidScoreError as error:
        raise HTTPException(status_code=422, detail=str(error))
    return BrandReviewResponseSchema.from_result(result)


@brand_review_router.get(
    "/orders/{order_id}/brand-review", response_model=BrandReviewResponseSchema
)
async def get_order_brand_review(
    order_id: int,
    user: VerifiedUser = Depends(get_current_user),
    use_case: BrandReviewUseCase = Depends(get_brand_review_use_case),
) -> BrandReviewResponseSchema:
    try:
        result = await use_case.get_order_brand_review(order_id, user.id)
    except OrderNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except NotOrderCreatorError as error:
        raise HTTPException(status_code=403, detail=str(error))
    except ReviewNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    return BrandReviewResponseSchema.from_result(result)


@brand_review_router.get("/brands/{brand_user_id}/rating", response_model=BrandRatingResponseSchema)
async def get_brand_rating(
    brand_user_id: int,
    use_case: BrandReviewUseCase = Depends(get_brand_review_use_case),
) -> BrandRatingResponseSchema:
    """**공개** 브랜드 평점 집계 — 크리에이터 평점이 공개인 것과 대칭이다."""
    return BrandRatingResponseSchema.from_result(await use_case.get_brand_rating(brand_user_id))
