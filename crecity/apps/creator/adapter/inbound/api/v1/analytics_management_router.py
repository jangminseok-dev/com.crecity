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
from hub.dependencies.current_user_provider import get_current_user

analytics_management_router = APIRouter(prefix="/creator", tags=["creator"])


@analytics_management_router.post(
    "/my/analytics", response_model=AnalyticsResponseSchema, status_code=201
)
async def submit_analytics(
    file: UploadFile,
    platform: str = Form(...),
    followers_count: int = Form(...),
    engagement_permille: int | None = Form(None),
    user: VerifiedUser = Depends(get_current_user),
    use_case: AnalyticsManagementUseCase = Depends(get_analytics_management_use_case),
) -> AnalyticsResponseSchema:
    try:
        result = await use_case.submit(
            SubmitAnalyticsCommand(
                requester_user_id=user.id,
                platform=platform,
                followers_count=followers_count,
                engagement_permille=engagement_permille,
                content=await file.read(),
                content_type=file.content_type or "",
            )
        )
    except ProfileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except ValueError as error:
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
