from fastapi import APIRouter, Depends, HTTPException

from hub.app.dtos.verified_user_dto import VerifiedUser
from hub.dependencies.current_user_provider import get_optional_user
from review.adapter.inbound.api.schemas.review_listing_schema import (
    CreatorReviewsResponseSchema,
    ReviewListItemSchema,
)
from review.app.dtos.review_listing_dto import CreatorReviewsQuery
from review.app.exceptions import CreatorNotFoundError
from review.app.ports.input.review_listing_use_case import ReviewListingUseCase
from review.dependencies.review_listing_provider import get_review_listing_use_case

review_listing_router = APIRouter(prefix="/review", tags=["review"])


@review_listing_router.get("/creators/{slug}", response_model=CreatorReviewsResponseSchema)
async def list_creator_reviews(
    slug: str,
    viewer: VerifiedUser | None = Depends(get_optional_user),
    use_case: ReviewListingUseCase = Depends(get_review_listing_use_case),
) -> CreatorReviewsResponseSchema:
    try:
        result = await use_case.list_for_creator(
            CreatorReviewsQuery(slug=slug, viewer_logged_in=viewer is not None)
        )
    except CreatorNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    return CreatorReviewsResponseSchema(
        total=result.total,
        average_overall=result.average_overall,
        average_communication=result.average_communication,
        average_timeliness=result.average_timeliness,
        average_satisfaction=result.average_satisfaction,
        items=[
            ReviewListItemSchema(
                id=item.id,
                communication_score=item.communication_score,
                timeliness_score=item.timeliness_score,
                satisfaction_score=item.satisfaction_score,
                overall_score=item.overall_score,
                comment=item.comment,
                is_locked=item.is_locked,
                created_at=item.created_at,
            )
            for item in result.items
        ],
    )
