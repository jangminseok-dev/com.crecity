from datetime import datetime

from pydantic import BaseModel, Field


class ApplyRequestSchema(BaseModel):

    message: str = Field(..., min_length=10, description="제안 내용(10자 이상)")
    proposed_price_krw: int = Field(..., description="자체 견적(원)")


class ApplicationResponseSchema(BaseModel):

    id: int
    campaign_id: int
    creator_user_id: int
    creator_name: str
    creator_slug: str
    message: str
    proposed_price_krw: int
    order_id: int | None  # 수락(결제)된 지원이면 생성된 주문 id
    created_at: datetime | None


class MyApplicationResponseSchema(BaseModel):
    """내 지원 1건(갭 #103) — 상태는 order_id·공고 상태에서 화면이 파생한다."""

    id: int
    campaign_id: int
    campaign_title: str
    campaign_status: str  # OPEN | CLOSED
    campaign_deadline_at: datetime | None
    message: str
    proposed_price_krw: int
    order_id: int | None
    created_at: datetime | None
