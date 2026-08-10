from datetime import datetime

from pydantic import BaseModel

from hub.app.dtos.profile_review_dto import ProfileReviewSummary


class ProfileReviewResponseSchema(BaseModel):

    id: int
    slug: str
    name: str
    tagline: str
    bio: str
    primary_category: str
    status: str
    created_at: datetime | None

    @classmethod
    def from_summary(cls, summary: ProfileReviewSummary) -> "ProfileReviewResponseSchema":
        return cls(
            id=summary.id,
            slug=summary.slug,
            name=summary.name,
            tagline=summary.tagline,
            bio=summary.bio,
            primary_category=summary.primary_category,
            status=summary.status,
            created_at=summary.created_at,
        )
