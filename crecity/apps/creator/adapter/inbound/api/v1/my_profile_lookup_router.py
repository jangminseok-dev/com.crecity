from fastapi import APIRouter, Depends, HTTPException

from creator.adapter.inbound.api.schemas.my_profile_lookup_schema import MyProfileResponseSchema
from creator.app.dtos.my_profile_lookup_dto import MyProfileQuery
from creator.app.exceptions import ProfileNotFoundError
from creator.app.ports.input.my_profile_lookup_use_case import MyProfileLookupUseCase
from creator.dependencies.my_profile_lookup_provider import get_my_profile_lookup_use_case
from hub.app.dtos.verified_user_dto import VerifiedUser
from hub.dependencies.current_user_provider import get_current_user

my_profile_lookup_router = APIRouter(prefix="/creator", tags=["creator"])


@my_profile_lookup_router.get("/my/profile", response_model=MyProfileResponseSchema)
async def get_my_profile(
    user: VerifiedUser = Depends(get_current_user),
    use_case: MyProfileLookupUseCase = Depends(get_my_profile_lookup_use_case),
) -> MyProfileResponseSchema:
    try:
        result = await use_case.get_my_profile(MyProfileQuery(user_id=user.id))
    except ProfileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
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
        created_at=result.created_at,
    )
