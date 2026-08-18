from fastapi import APIRouter, Depends, HTTPException, Query

from creator.adapter.inbound.api.schemas.profile_listing_schema import ProfileListingItemSchema
from creator.app.dtos.similar_profiles_dto import SimilarProfilesQuery
from creator.app.exceptions import ProfileNotFoundError
from creator.app.ports.input.similar_profiles_use_case import SimilarProfilesUseCase
from creator.dependencies.similar_profiles_provider import get_similar_profiles_use_case

similar_profiles_router = APIRouter(prefix="/creator", tags=["creator"])


@similar_profiles_router.get(
    "/profiles/{slug}/similar", response_model=list[ProfileListingItemSchema]
)
async def list_similar_profiles(
    slug: str,
    limit: int = Query(4, ge=1, le=12),
    use_case: SimilarProfilesUseCase = Depends(get_similar_profiles_use_case),
) -> list[ProfileListingItemSchema]:
    """**공개** 유사 크리에이터 추천(갭 #88) — 카테고리·가격대·플랫폼 규칙 기반."""
    try:
        items = await use_case.list_similar(SimilarProfilesQuery(slug=slug, limit=limit))
    except ProfileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
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
