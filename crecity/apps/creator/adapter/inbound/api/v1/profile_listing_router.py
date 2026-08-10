from fastapi import APIRouter, Depends, Query

from creator.adapter.inbound.api.schemas.profile_listing_schema import (
    ProfileListingItemSchema,
    ProfileListingResponseSchema,
)
from creator.app.dtos.profile_listing_dto import ProfileListingQuery
from creator.app.ports.input.profile_listing_use_case import ProfileListingUseCase
from creator.dependencies.profile_listing_provider import get_profile_listing_use_case

profile_listing_router = APIRouter(prefix="/creator", tags=["creator"])


@profile_listing_router.get("/profiles", response_model=ProfileListingResponseSchema)
async def list_profiles(
    category: str | None = Query(None, max_length=50),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    use_case: ProfileListingUseCase = Depends(get_profile_listing_use_case),
) -> ProfileListingResponseSchema:
    result = await use_case.list_profiles(
        ProfileListingQuery(category=category, limit=limit, offset=offset)
    )
    return ProfileListingResponseSchema(
        items=[
            ProfileListingItemSchema(
                id=item.id,
                slug=item.slug,
                name=item.name,
                tagline=item.tagline,
                location=item.location,
                primary_category=item.primary_category,
                created_at=item.created_at,
            )
            for item in result.items
        ],
        total=result.total,
    )
