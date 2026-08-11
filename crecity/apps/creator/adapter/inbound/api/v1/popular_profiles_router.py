from fastapi import APIRouter, Depends, Query

from creator.adapter.inbound.api.schemas.profile_listing_schema import ProfileListingItemSchema
from creator.app.dtos.popular_profiles_dto import PopularProfilesQuery
from creator.app.ports.input.popular_profiles_use_case import PopularProfilesUseCase
from creator.dependencies.popular_profiles_provider import get_popular_profiles_use_case

# 주의: /profiles/{slug} 라우트와 겹치므로 main.py에서 profile_lookup보다 먼저 등록한다.
popular_profiles_router = APIRouter(prefix="/creator", tags=["creator"])


@popular_profiles_router.get("/profiles/popular", response_model=list[ProfileListingItemSchema])
async def list_popular_profiles(
    limit: int = Query(4, ge=1, le=12),
    use_case: PopularProfilesUseCase = Depends(get_popular_profiles_use_case),
) -> list[ProfileListingItemSchema]:
    items = await use_case.list_popular(PopularProfilesQuery(limit=limit))
    return [
        ProfileListingItemSchema(
            id=item.id,
            slug=item.slug,
            name=item.name,
            tagline=item.tagline,
            location=item.location,
            primary_category=item.primary_category,
            created_at=item.created_at,
            cover_image_url=(
                f"/uploads/portfolio/{item.cover_file_name}" if item.cover_file_name else None
            ),
            price_from=item.price_from,
            rating_avg=item.rating_avg,
            rating_count=item.rating_count,
        )
        for item in items
    ]
