from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from creator.app.dtos.faq_management_dto import FaqResult


class FaqRequestSchema(BaseModel):

    question: str = Field(..., max_length=200, description="자주 묻는 질문")
    answer: str = Field(..., max_length=2000, description="답변")


class FaqResponseSchema(BaseModel):

    id: int
    question: str
    answer: str
    created_at: datetime | None

    @classmethod
    def from_result(cls, result: FaqResult) -> FaqResponseSchema:
        return cls(
            id=result.id,
            question=result.question,
            answer=result.answer,
            created_at=result.created_at,
        )
