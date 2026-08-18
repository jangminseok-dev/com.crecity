from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ProfileReviewSummary:
    """심사 대상 프로필 요약 — admin → creator 허브 계약(BOUNDARIES §5 어드민 패턴)."""

    id: int
    slug: str
    name: str
    tagline: str
    bio: str
    primary_category: str
    status: str
    created_at: datetime | None
    # 정량 vetting 자동 체크(갭 #16) — 참고선일 뿐, 승인·반려는 운영자가 결정한다
    platform_count: int = 0
    total_followers: int = 0
    best_engagement_permille: int | None = None
    min_followers: int = 0
    min_engagement_permille: int = 0
    vetting_passed: bool = False


@dataclass(frozen=True)
class FlaggedAnalyticsSummary:
    """이상치 플래그된 채널 지표(갭 #82) — 운영자 재검토 큐 한 행."""

    id: int  # profile_analytics 행 id
    profile_slug: str
    profile_name: str
    platform: str
    followers_count: int
    engagement_permille: int | None
    flag_reason: str
    updated_at: datetime | None
