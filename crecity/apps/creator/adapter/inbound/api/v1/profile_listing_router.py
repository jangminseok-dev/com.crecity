from fastapi import APIRouter, Depends, Query

from creator.adapter.inbound.api.schemas.profile_listing_schema import (
    ProfileListingItemSchema,
    ProfileListingResponseSchema,
)
from creator.app.dtos.profile_listing_dto import ProfileListingQuery
from creator.app.ports.input.profile_listing_use_case import ProfileListingUseCase
from creator.dependencies.profile_listing_provider import get_profile_listing_use_case
from creator.domain.entities.creator_package_entity import PackagePlatform

profile_listing_router = APIRouter(prefix="/creator", tags=["creator"])


@profile_listing_router.get("/categories", response_model=list[str])
async def list_categories(
    use_case: ProfileListingUseCase = Depends(get_profile_listing_use_case),
) -> list[str]:
    return await use_case.list_categories()


@profile_listing_router.get("/profiles", response_model=ProfileListingResponseSchema)
async def list_profiles(
    category: str | None = Query(None, max_length=50),
    q: str | None = Query(None, max_length=100, description="이름·한 줄 소개 키워드"),
    platform: PackagePlatform | None = Query(None, description="해당 플랫폼 패키지가 있는 프로필"),
    price_min: int | None = Query(None, ge=0, description="패키지 가격 하한(원)"),
    price_max: int | None = Query(None, ge=0, description="패키지 가격 상한(원)"),
    location: str | None = Query(None, max_length=100, description="활동 지역 부분 일치"),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    use_case: ProfileListingUseCase = Depends(get_profile_listing_use_case),
) -> ProfileListingResponseSchema:
    result = await use_case.list_profiles(
        ProfileListingQuery(
            category=category,
            q=q,
            limit=limit,
            offset=offset,
            platform=platform.value if platform else None,
            price_min=price_min,
            price_max=price_max,
            location=location,
        )
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
                cover_image_url=(
                    f"/uploads/portfolio/{item.cover_file_name}" if item.cover_file_name else None
                ),
                price_from=item.price_from,
                rating_avg=item.rating_avg,
                rating_count=item.rating_count,
            )
            for item in result.items
        ],
        total=result.total,
    )
