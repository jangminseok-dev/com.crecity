from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from creator.domain.entities.profile_analytics_entity import ProfileAnalytics


@dataclass(frozen=True)
class SubmitAnalyticsCommand:
    """자가입력 제출 — 스크린샷이 증빙이며 재제출 시 해당 플랫폼 행을 갱신한다."""

    requester_user_id: int
    platform: str
    followers_count: int
    engagement_permille: int | None  # 참여율 ×10 (3.5% → 35)
    content: bytes  # 인증 스크린샷
    content_type: str


@dataclass(frozen=True)
class RemoveAnalyticsCommand:

    requester_user_id: int
    platform: str


@dataclass(frozen=True)
class AnalyticsResult:

    platform: str
    followers_count: int
    engagement_permille: int | None
    screenshot_file_name: str
    updated_at: datetime | None

    @classmethod
    def from_entity(cls, analytics: ProfileAnalytics) -> AnalyticsResult:
        return cls(
            platform=analytics.platform,
            followers_count=analytics.followers_count,
            engagement_permille=analytics.engagement_permille,
            screenshot_file_name=analytics.screenshot_file_name,
            updated_at=analytics.updated_at,
        )
