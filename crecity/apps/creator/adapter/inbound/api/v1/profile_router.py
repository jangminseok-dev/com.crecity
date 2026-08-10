from fastapi import APIRouter, Depends

from creator.adapter.inbound.api.schemas.profile_schema import ProfileResponseSchema
from creator.app.dtos.profile_dto import ProfileQuery
from creator.app.ports.input.profile_use_case import ProfileUseCase
from creator.dependencies.profile_provider import get_profile_use_case

profile_router = APIRouter(prefix="/creator", tags=["creator"])


@profile_router.get("/myself", response_model=ProfileResponseSchema)
async def introduce_myself(
    profile: ProfileUseCase = Depends(get_profile_use_case),
) -> ProfileResponseSchema:
    result = await profile.introduce_myself(
        ProfileQuery(
            id=3,
            name="크리에이터 (creator)",
        )
    )
    return ProfileResponseSchema(
        id=result.id, name=result.name, introduction=result.introduction
    )
