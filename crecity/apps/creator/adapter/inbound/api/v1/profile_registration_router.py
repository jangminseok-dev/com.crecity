from fastapi import APIRouter, Depends, HTTPException

from creator.adapter.inbound.api.schemas.profile_registration_schema import (
    ProfileRegistrationRequestSchema,
    ProfileRegistrationResponseSchema,
)
from creator.app.dtos.profile_registration_dto import ProfileRegistrationCommand
from creator.app.exceptions import DuplicateSlugError
from creator.app.ports.input.profile_registration_use_case import ProfileRegistrationUseCase
from creator.dependencies.profile_registration_provider import get_profile_registration_use_case

profile_registration_router = APIRouter(prefix="/creator", tags=["creator"])


@profile_registration_router.post(
    "/profiles", response_model=ProfileRegistrationResponseSchema, status_code=201
)
async def register_profile(
    body: ProfileRegistrationRequestSchema,
    use_case: ProfileRegistrationUseCase = Depends(get_profile_registration_use_case),
) -> ProfileRegistrationResponseSchema:
    try:
        result = await use_case.register(
            ProfileRegistrationCommand(
                slug=body.slug,
                name=body.name,
                tagline=body.tagline,
                bio=body.bio,
                location=body.location,
                primary_category=body.primary_category,
            )
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))
    except DuplicateSlugError as error:
        raise HTTPException(status_code=409, detail=str(error))
    return ProfileRegistrationResponseSchema(
        id=result.id,
        slug=result.slug,
        name=result.name,
        tagline=result.tagline,
        bio=result.bio,
        location=result.location,
        primary_category=result.primary_category,
        status=result.status,
        created_at=result.created_at,
    )
