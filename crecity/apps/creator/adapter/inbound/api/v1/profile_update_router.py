from fastapi import APIRouter, Depends, HTTPException

from creator.adapter.inbound.api.schemas.my_profile_lookup_schema import MyProfileResponseSchema
from creator.adapter.inbound.api.schemas.profile_update_schema import ProfileUpdateRequestSchema
from creator.app.dtos.profile_update_dto import ProfileUpdateCommand
from creator.app.exceptions import ProfileNotFoundError
from creator.app.ports.input.profile_update_use_case import ProfileUpdateUseCase
from creator.dependencies.profile_update_provider import get_profile_update_use_case
from hub.app.dtos.verified_user_dto import VerifiedUser
from hub.dependencies.current_user_provider import get_current_user

profile_update_router = APIRouter(prefix="/creator", tags=["creator"])


@profile_update_router.put("/my/profile", response_model=MyProfileResponseSchema)
async def update_my_profile(
    body: ProfileUpdateRequestSchema,
    user: VerifiedUser = Depends(get_current_user),
    use_case: ProfileUpdateUseCase = Depends(get_profile_update_use_case),
) -> MyProfileResponseSchema:
    try:
        result = await use_case.update_my_profile(
            ProfileUpdateCommand(
                user_id=user.id,
                name=body.name,
                tagline=body.tagline,
                bio=body.bio,
                location=body.location,
                primary_category=body.primary_category,
            )
        )
    except ProfileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))
    return MyProfileResponseSchema(
        id=result.id,
        slug=result.slug,
        name=result.name,
        tagline=result.tagline,
        bio=result.bio,
        location=result.location,
        primary_category=result.primary_category,
        status=result.status,
        created_at=result.created_at,
        accepting_orders=result.accepting_orders,
    )
