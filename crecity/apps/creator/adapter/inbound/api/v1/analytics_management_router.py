import json

from fastapi import APIRouter, Depends, Form, HTTPException, Response, UploadFile

from creator.adapter.inbound.api.schemas.analytics_management_schema import (
    AnalyticsResponseSchema,
)
from creator.app.dtos.analytics_management_dto import (
    RemoveAnalyticsCommand,
    SubmitAnalyticsCommand,
)
from creator.app.exceptions import AnalyticsNotFoundError, ProfileNotFoundError
from creator.app.ports.input.analytics_management_use_case import AnalyticsManagementUseCase
from creator.dependencies.analytics_management_provider import (
    get_analytics_management_use_case,
)
from hub.app.dtos.verified_user_dto import VerifiedUser
from creator.domain.value_objects.audience_breakdown import (
    AudienceDimension,
    AudienceShare,
    InvalidAudienceShareError,
)
from hub.dependencies.current_user_provider import get_current_user

analytics_management_router = APIRouter(prefix="/creator", tags=["creator"])


def _parse_audience(raw: str | None) -> tuple[AudienceShare, ...]:
    """JSON 문자열 → VO. 형식 오류도 422로 떨어뜨린다(도메인 규칙 검증은 VO가 한다)."""
    if not raw:
        return ()
    try:
        items = json.loads(raw)
        return tuple(
            AudienceShare(
                dimension=AudienceDimension(item["dimension"]),
                bucket=item["bucket"],
                share_permille=int(item["share_permille"]),
            )
            for item in items
        )
    except InvalidAudienceShareError:
        raise
    except Exception as error:  # noqa: BLE001 — 잘못된 JSON·키 누락 등
        raise InvalidAudienceShareError(f"오디언스 형식이 올바르지 않습니다: {error}") from error


@analytics_management_router.post(
    "/my/analytics", response_model=AnalyticsResponseSchema, status_code=201
)
async def submit_analytics(
    file: UploadFile,
    platform: str = Form(...),
    followers_count: int = Form(...),
    engagement_permille: int | None = Form(None),
    top_audience_region: str | None = Form(None),
    # 오디언스 비율(갭 #67) — multipart라 JSON 문자열로 받는다.
    # 예: [{"dimension":"AGE","bucket":"20s","share_permille":450}]
    audience: str | None = Form(None),
    user: VerifiedUser = Depends(get_current_user),
    use_case: AnalyticsManagementUseCase = Depends(get_analytics_management_use_case),
) -> AnalyticsResponseSchema:
    try:
        shares = _parse_audience(audience)
        result = await use_case.submit(
            SubmitAnalyticsCommand(
                requester_user_id=user.id,
                platform=platform,
                followers_count=followers_count,
                engagement_permille=engagement_permille,
                content=await file.read(),
                content_type=file.content_type or "",
                top_audience_region=top_audience_region,
                audience=shares,
            )
        )
    except ProfileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except (ValueError, InvalidAudienceShareError) as error:
        raise HTTPException(status_code=422, detail=str(error))
    return AnalyticsResponseSchema.from_result(result)


@analytics_management_router.get(
    "/my/analytics", response_model=list[AnalyticsResponseSchema]
)
async def list_my_analytics(
    user: VerifiedUser = Depends(get_current_user),
    use_case: AnalyticsManagementUseCase = Depends(get_analytics_management_use_case),
) -> list[AnalyticsResponseSchema]:
    try:
        results = await use_case.list_mine(user.id)
    except ProfileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    return [AnalyticsResponseSchema.from_result(result) for result in results]


@analytics_management_router.delete("/my/analytics/{platform}", status_code=204)
async def remove_analytics(
    platform: str,
    user: VerifiedUser = Depends(get_current_user),
    use_case: AnalyticsManagementUseCase = Depends(get_analytics_management_use_case),
) -> Response:
    try:
        await use_case.remove(
            RemoveAnalyticsCommand(requester_user_id=user.id, platform=platform)
        )
    except ProfileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except AnalyticsNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    return Response(status_code=204)


@analytics_management_router.get(
    "/profiles/{slug}/analytics", response_model=list[AnalyticsResponseSchema]
)
async def list_profile_analytics(
    slug: str,
    _user: VerifiedUser = Depends(get_current_user),  # 가입 게이트 — 비로그인 401(§9.2)
    use_case: AnalyticsManagementUseCase = Depends(get_analytics_management_use_case),
) -> list[AnalyticsResponseSchema]:
    try:
        results = await use_case.list_public(slug)
    except ProfileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    return [AnalyticsResponseSchema.from_result(result) for result in results]
