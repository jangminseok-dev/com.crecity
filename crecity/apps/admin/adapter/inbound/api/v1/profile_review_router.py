from fastapi import APIRouter, Depends, HTTPException

from admin.adapter.inbound.api.schemas.profile_review_schema import ProfileReviewResponseSchema
from admin.app.dtos.profile_review_dto import ReviewDecisionCommand
from admin.app.exceptions import ReviewTargetNotFoundError
from admin.app.ports.input.profile_review_use_case import ProfileReviewUseCase
from admin.dependencies.profile_review_provider import get_profile_review_use_case
from hub.app.dtos.verified_user_dto import VerifiedUser
from hub.dependencies.current_user_provider import require_permission

profile_review_router = APIRouter(prefix="/admin", tags=["admin"])

# RBAC — 이 라우터의 모든 엔드포인트는 profile.review 권한 보유자만(403)
_reviewer = require_permission("profile.review")


@profile_review_router.get("/profiles/pending", response_model=list[ProfileReviewResponseSchema])
async def list_pending_profiles(
    user: VerifiedUser = Depends(_reviewer),
    use_case: ProfileReviewUseCase = Depends(get_profile_review_use_case),
) -> list[ProfileReviewResponseSchema]:
    results = await use_case.list_pending()
    return [ProfileReviewResponseSchema.from_summary(result) for result in results]


async def _review(
    profile_id: int, approved: bool, user: VerifiedUser, use_case: ProfileReviewUseCase
) -> ProfileReviewResponseSchema:
    try:
        result = await use_case.review(
            ReviewDecisionCommand(
                profile_id=profile_id,
                approved=approved,
                reviewer_id=user.id,
                reviewer_email=user.email,
            )
        )
    except ReviewTargetNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    return ProfileReviewResponseSchema.from_summary(result)


@profile_review_router.post(
    "/profiles/{profile_id}/approve", response_model=ProfileReviewResponseSchema
)
async def approve_profile(
    profile_id: int,
    user: VerifiedUser = Depends(_reviewer),
    use_case: ProfileReviewUseCase = Depends(get_profile_review_use_case),
) -> ProfileReviewResponseSchema:
    return await _review(profile_id, True, user, use_case)


@profile_review_router.post(
    "/profiles/{profile_id}/reject", response_model=ProfileReviewResponseSchema
)
async def reject_profile(
    profile_id: int,
    user: VerifiedUser = Depends(_reviewer),
    use_case: ProfileReviewUseCase = Depends(get_profile_review_use_case),
) -> ProfileReviewResponseSchema:
    return await _review(profile_id, False, user, use_case)
