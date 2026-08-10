from datetime import datetime

from pydantic import BaseModel


class ProfileLookupResponseSchema(BaseModel):

    id: int
    slug: str
    name: str
    tagline: str
    bio: str
    location: str | None
    primary_category: str
    status: str
    created_at: datetime | None
