from fastapi import APIRouter, Depends, HTTPException

from creator.adapter.inbound.api.schemas.profile_lookup_schema import ProfileLookupResponseSchema
from creator.app.dtos.profile_lookup_dto import ProfileLookupQuery
from creator.app.exceptions import ProfileNotFoundError
from creator.app.ports.input.profile_lookup_use_case import ProfileLookupUseCase
from creator.dependencies.profile_lookup_provider import get_profile_lookup_use_case

profile_lookup_router = APIRouter(prefix="/creator", tags=["creator"])


@profile_lookup_router.get("/profiles/{slug}", response_model=ProfileLookupResponseSchema)
async def lookup_profile(
    slug: str,
    use_case: ProfileLookupUseCase = Depends(get_profile_lookup_use_case),
) -> ProfileLookupResponseSchema:
    try:
        result = await use_case.lookup(ProfileLookupQuery(slug=slug))
    except ProfileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    return ProfileLookupResponseSchema(
        id=result.id,
        slug=result.slug,
        name=result.name,
        tagline=result.tagline,
        bio=result.bio,
        location=result.location,
        primary_category=result.primary_category,
        status=result.status,
        created_at=result.created_at,
        followers_total=result.followers_total,
        accepting_orders=result.accepting_orders,
        completed_orders=result.completed_orders,
        accepted_orders=result.accepted_orders,
        received_orders=result.received_orders,
        avg_accept_hours=result.avg_accept_hours,
        fast_responder=result.fast_responder,
    )
