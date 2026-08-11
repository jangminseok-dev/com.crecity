from datetime import datetime

from pydantic import BaseModel


class ProfileListingItemSchema(BaseModel):

    id: int
    slug: str
    name: str
    tagline: str
    location: str | None
    primary_category: str
    created_at: datetime | None
    cover_image_url: str | None  # 정적 서빙 경로(/uploads/portfolio/...) — 프론트는 그대로 <img src>
    price_from: int | None  # 최저 패키지 가격 — "N원부터"
    rating_avg: float | None
    rating_count: int


class ProfileListingResponseSchema(BaseModel):

    items: list[ProfileListingItemSchema]
    total: int
