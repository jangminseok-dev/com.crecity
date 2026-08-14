from datetime import datetime

from pydantic import BaseModel


class ReviewListItemSchema(BaseModel):

    id: int
    communication_score: int
    timeliness_score: int
    satisfaction_score: int
    overall_score: float
    comment: str | None  # 비로그인이면 null(잠김)
    is_locked: bool
    created_at: datetime | None
    # 크리에이터 답글(갭 #53) — 답글이 없거나 원문이 잠기면 null
    reply: str | None = None
    replied_at: datetime | None = None
    can_reply: bool = False  # 이 리뷰에 답글을 남길 수 있는 사람인지(대상 크리에이터 본인)


class CreatorReviewsResponseSchema(BaseModel):

    total: int
    average_overall: float | None
    average_communication: float | None
    average_timeliness: float | None
    average_satisfaction: float | None
    items: list[ReviewListItemSchema]
