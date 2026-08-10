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


class ProfileListingResponseSchema(BaseModel):

    items: list[ProfileListingItemSchema]
    total: int
