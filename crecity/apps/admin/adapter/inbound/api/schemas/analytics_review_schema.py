from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from hub.app.dtos.profile_review_dto import FlaggedAnalyticsSummary


class FlaggedAnalyticsResponseSchema(BaseModel):

    id: int
    profile_slug: str
    profile_name: str
    platform: str
    followers_count: int
    engagement_permille: int | None
    flag_reason: str
    updated_at: datetime | None

    @classmethod
    def from_summary(cls, summary: FlaggedAnalyticsSummary) -> FlaggedAnalyticsResponseSchema:
        return cls(
            id=summary.id,
            profile_slug=summary.profile_slug,
            profile_name=summary.profile_name,
            platform=summary.platform,
            followers_count=summary.followers_count,
            engagement_permille=summary.engagement_permille,
            flag_reason=summary.flag_reason,
            updated_at=summary.updated_at,
        )
