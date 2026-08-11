from dataclasses import dataclass


@dataclass(frozen=True)
class CreatorRatingSummary:
    """크리에이터 평점 요약 — 3축 평균(overall)의 평균과 리뷰 수."""

    creator_user_id: int
    average_overall: float
    review_count: int
