from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CreatorReviewsQuery:

    slug: str
    viewer_logged_in: bool  # 블러 정책 — 비로그인은 리뷰 원문 잠금(collabstr §2.3)
    viewer_user_id: int | None = None  # 답글 자격 판정용(갭 #53) — 비로그인은 None


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
    # 크리에이터 답글(갭 #53) — 원문이 잠기면 답글도 함께 잠근다
    reply: str | None = None
    replied_at: datetime | None = None
    can_reply: bool = False  # 보는 사람이 이 리뷰의 대상 크리에이터이고 아직 답글이 없을 때만


@dataclass(frozen=True)
class CreatorReviewsResult:
    """집계는 항상 공개, 원문은 로그인 시에만(가입 유도 장치)."""

    total: int
    average_overall: float | None  # 리뷰 없으면 None
    average_communication: float | None
    average_timeliness: float | None
    average_satisfaction: float | None
    items: list[ReviewListItem]
