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
