from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from creator.app.dtos.analytics_management_dto import AnalyticsResult


class AnalyticsResponseSchema(BaseModel):

    platform: str
    followers_count: int
    engagement_permille: int | None  # 참여율 ×10 (3.5% → 35)
    screenshot_url: str  # 인증 스크린샷
    updated_at: datetime | None

    @classmethod
    def from_result(cls, result: AnalyticsResult) -> AnalyticsResponseSchema:
        return cls(
            platform=result.platform,
            followers_count=result.followers_count,
            engagement_permille=result.engagement_permille,
            screenshot_url=f"/uploads/analytics/{result.screenshot_file_name}",
            updated_at=result.updated_at,
        )
