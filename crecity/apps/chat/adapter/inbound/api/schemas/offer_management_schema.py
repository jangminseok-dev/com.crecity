from datetime import datetime

from pydantic import BaseModel, Field


class OfferCreateRequestSchema(BaseModel):

    title: str = Field(min_length=1, max_length=100)
    price_krw: int = Field(gt=0)
    # 합의 조건(갭 #98) — 패키지 표준계약 필드와 동일 범위
    revision_limit: int = Field(2, ge=0, le=10)
    usage_rights: str = Field("", max_length=300)


class OfferResponseSchema(BaseModel):

    id: int
    conversation_id: int
    title: str
    price_krw: int
    revision_limit: int
    usage_rights: str
    status: str
    order_id: int | None
    created_at: datetime | None
