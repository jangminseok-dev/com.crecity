from fastapi import APIRouter, Depends, HTTPException

from creator.adapter.inbound.api.schemas.my_profile_lookup_schema import MyProfileResponseSchema
from creator.app.dtos.profile_resubmission_dto import ProfileResubmissionCommand
from creator.app.exceptions import NotRejectedProfileError, ProfileNotFoundError
from creator.app.ports.input.profile_resubmission_use_case import ProfileResubmissionUseCase
from creator.dependencies.profile_resubmission_provider import get_profile_resubmission_use_case
from hub.app.dtos.verified_user_dto import VerifiedUser
from hub.dependencies.current_user_provider import get_current_user

profile_resubmission_router = APIRouter(prefix="/creator", tags=["creator"])


@profile_resubmission_router.post("/my/profile/resubmit", response_model=MyProfileResponseSchema)
async def resubmit_my_profile(
    user: VerifiedUser = Depends(get_current_user),
    use_case: ProfileResubmissionUseCase = Depends(get_profile_resubmission_use_case),
) -> MyProfileResponseSchema:
    """반려 프로필 재심사 요청(갭 #101) — 보완 후 REJECTED → PENDING 복귀."""
    try:
        result = await use_case.resubmit(ProfileResubmissionCommand(user_id=user.id))
    except ProfileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except NotRejectedProfileError as error:
        raise HTTPException(status_code=409, detail=str(error))
    return MyProfileResponseSchema(
        id=result.id,
        slug=result.slug,
        name=result.name,
        tagline=result.tagline,
        bio=result.bio,
        location=result.location,
        primary_category=result.primary_category,
        status=result.status,
        accepting_orders=result.accepting_orders,
        rejection_reason=result.rejection_reason,
        created_at=result.created_at,
    )
