from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from creator.app.dtos.analytics_management_dto import AnalyticsResult


class AudienceShareSchema(BaseModel):

    dimension: str  # AGE | GENDER
    bucket: str
    share_permille: int  # 450 = 45.0%


class AnalyticsResponseSchema(BaseModel):

    platform: str
    followers_count: int
    engagement_permille: int | None  # 참여율 ×10 (3.5% → 35)
    screenshot_url: str  # 인증 스크린샷
    updated_at: datetime | None
    # 오디언스(§2.1-6, 갭 #67)
    top_audience_region: str | None = None
    audience: list[AudienceShareSchema] = []

    @classmethod
    def from_result(cls, result: AnalyticsResult) -> AnalyticsResponseSchema:
        return cls(
            platform=result.platform,
            followers_count=result.followers_count,
            engagement_permille=result.engagement_permille,
            screenshot_url=f"/uploads/analytics/{result.screenshot_file_name}",
            updated_at=result.updated_at,
            top_audience_region=result.top_audience_region,
            audience=[
                AudienceShareSchema(
                    dimension=share.dimension.value,
                    bucket=share.bucket,
                    share_permille=share.share_permille,
                )
                for share in result.audience
            ],
        )
