from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ProfileLookupQuery:

    slug: str


@dataclass(frozen=True)
class ProfileLookupResult:

    id: int
    slug: str
    name: str
    tagline: str
    bio: str
    location: str | None
    primary_category: str
    status: str
    created_at: datetime | None
