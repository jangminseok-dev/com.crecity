from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ProfileListingQuery:

    category: str | None
    limit: int
    offset: int


@dataclass(frozen=True)
class ProfileListingItem:

    id: int
    slug: str
    name: str
    tagline: str
    location: str | None
    primary_category: str
    created_at: datetime | None


@dataclass(frozen=True)
class ProfileListingResult:

    items: list[ProfileListingItem]
    total: int
