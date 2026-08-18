from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from review.app.dtos.brand_review_dto import BrandRatingResult, BrandReviewResult


class BrandReviewSubmissionSchema(BaseModel):
    """브랜드 평가 제출(갭 #83) — 단일 종합 평점 + 코멘트."""

    score: int = Field(ge=1, le=5)
    comment: str = Field(min_length=1, max_length=2000)


class BrandReviewResponseSchema(BaseModel):

    id: int
    order_id: int
    score: int
    comment: str
    created_at: datetime | None

    @classmethod
    def from_result(cls, result: BrandReviewResult) -> BrandReviewResponseSchema:
        return cls(
            id=result.id,
            order_id=result.order_id,
            score=result.score,
            comment=result.comment,
            created_at=result.created_at,
        )


class BrandRatingResponseSchema(BaseModel):
    """브랜드 평점 집계(공개) — 평점·건수만, 원문 비공개."""

    average_score: float | None
    total: int

    @classmethod
    def from_result(cls, result: BrandRatingResult) -> BrandRatingResponseSchema:
        return cls(average_score=result.average_score, total=result.total)
