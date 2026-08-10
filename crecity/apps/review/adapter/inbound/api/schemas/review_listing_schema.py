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


class CreatorReviewsResponseSchema(BaseModel):

    total: int
    average_overall: float | None
    average_communication: float | None
    average_timeliness: float | None
    average_satisfaction: float | None
    items: list[ReviewListItemSchema]
