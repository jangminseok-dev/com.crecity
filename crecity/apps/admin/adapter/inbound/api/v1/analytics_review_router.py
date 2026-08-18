from fastapi import APIRouter, Depends, HTTPException

from admin.adapter.inbound.api.schemas.analytics_review_schema import (
    FlaggedAnalyticsResponseSchema,
)
from admin.app.dtos.analytics_review_dto import ClearFlagCommand
from admin.app.exceptions import ReviewTargetNotFoundError
from admin.app.ports.input.analytics_review_use_case import AnalyticsReviewUseCase
from admin.dependencies.analytics_review_provider import get_analytics_review_use_case
from hub.app.dtos.verified_user_dto import VerifiedUser
from hub.dependencies.current_user_provider import require_permission

analytics_review_router = APIRouter(prefix="/admin", tags=["admin"])

# 프로필 심사와 같은 권한 — 지표 재검토도 심사 업무의 연장이다(갭 #82)
_reviewer = require_permission("profile.review")


@analytics_review_router.get(
    "/analytics/flagged", response_model=list[FlaggedAnalyticsResponseSchema]
)
async def list_flagged_analytics(
    user: VerifiedUser = Depends(_reviewer),
    use_case: AnalyticsReviewUseCase = Depends(get_analytics_review_use_case),
) -> list[FlaggedAnalyticsResponseSchema]:
    """이상치 플래그된 채널 지표(갭 #82) — 오래된 순."""
    results = await use_case.list_flagged()
    return [FlaggedAnalyticsResponseSchema.from_summary(result) for result in results]


@analytics_review_router.post("/analytics/{analytics_id}/clear-flag", status_code=204)
async def clear_analytics_flag(
    analytics_id: int,
    user: VerifiedUser = Depends(_reviewer),
    use_case: AnalyticsReviewUseCase = Depends(get_analytics_review_use_case),
) -> None:
    """운영자 확인 처리 — 플래그 해제(스크린샷 대조 후 문제면 프로필 반려로 대응)."""
    try:
        await use_case.clear_flag(
            ClearFlagCommand(
                analytics_id=analytics_id, reviewer_id=user.id, reviewer_email=user.email
            )
        )
    except ReviewTargetNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
