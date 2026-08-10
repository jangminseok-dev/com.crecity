from datetime import datetime

from pydantic import BaseModel, Field


class ReviewSubmissionRequestSchema(BaseModel):

    communication_score: int = Field(..., ge=1, le=5, description="소통 평점")
    timeliness_score: int = Field(..., ge=1, le=5, description="기한 준수 평점")
    satisfaction_score: int = Field(..., ge=1, le=5, description="만족도 평점")
    comment: str = Field(..., min_length=1, description="리뷰 본문")


class ReviewResponseSchema(BaseModel):

    id: int
    order_id: int
    communication_score: int
    timeliness_score: int
    satisfaction_score: int
    overall_score: float
    comment: str
    created_at: datetime | None
