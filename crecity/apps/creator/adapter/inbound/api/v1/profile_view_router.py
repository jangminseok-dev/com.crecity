from fastapi import APIRouter, Depends, HTTPException, Response

from creator.adapter.inbound.api.schemas.profile_view_schema import ProfileViewsResponseSchema
from creator.app.dtos.profile_view_dto import ProfileViewRecordCommand
from creator.app.exceptions import ProfileNotFoundError
from creator.app.ports.input.profile_view_use_case import ProfileViewUseCase
from creator.dependencies.profile_view_provider import get_profile_view_use_case
from hub.app.dtos.verified_user_dto import VerifiedUser
from hub.dependencies.current_user_provider import get_current_user

profile_view_router = APIRouter(prefix="/creator", tags=["creator"])


@profile_view_router.post("/profiles/{slug}/views", status_code=204)
async def record_profile_view(
    slug: str,
    use_case: ProfileViewUseCase = Depends(get_profile_view_use_case),
) -> Response:
    """조회 1건 기록(갭 #57) — 브라우저가 부르므로 크롤러 트래픽이 대체로 빠진다.

    로그인을 요구하지 않는다(비회원 열람도 크리에이터에겐 의미 있는 신호다).
    """
    await use_case.record(ProfileViewRecordCommand(slug=slug))
    return Response(status_code=204)


@profile_view_router.get("/my/profile/views", response_model=ProfileViewsResponseSchema)
async def get_my_profile_views(
    user: VerifiedUser = Depends(get_current_user),
    use_case: ProfileViewUseCase = Depends(get_profile_view_use_case),
) -> ProfileViewsResponseSchema:
    """내 프로필 조회수 추이 — 항상 본인 기준(남의 조회수는 볼 수 없다)."""
    try:
        result = await use_case.get_my_views(user.id)
    except ProfileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return ProfileViewsResponseSchema.from_result(result)
