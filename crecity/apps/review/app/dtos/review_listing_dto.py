from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CreatorReviewsQuery:

    slug: str
    viewer_logged_in: bool  # 블러 정책 — 비로그인은 리뷰 원문 잠금(collabstr §2.3)


@dataclass(frozen=True)
class ReviewListItem:

    id: int
    communication_score: int
    timeliness_score: int
    satisfaction_score: int
    overall_score: float
    comment: str | None  # 비로그인이면 None(잠김)
    is_locked: bool
    created_at: datetime | None


@dataclass(frozen=True)
class CreatorReviewsResult:
    """집계는 항상 공개, 원문은 로그인 시에만(가입 유도 장치)."""

    total: int
    average_overall: float | None  # 리뷰 없으면 None
    average_communication: float | None
    average_timeliness: float | None
    average_satisfaction: float | None
    items: list[ReviewListItem]
