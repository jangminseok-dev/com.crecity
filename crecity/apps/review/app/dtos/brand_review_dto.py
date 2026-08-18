from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class BrandReviewSubmissionCommand:

    order_id: int
    requester_user_id: int
    score: int
    comment: str


@dataclass(frozen=True)
class BrandReviewResult:
    """브랜드 리뷰 1건(갭 #83)."""

    id: int
    order_id: int
    score: int
    comment: str
    created_at: datetime | None


@dataclass(frozen=True)
class BrandRatingResult:
    """브랜드 평점 집계(공개) — 크리에이터가 수락 판단에 쓴다."""

    average_score: float | None  # 리뷰가 없으면 None
    total: int
