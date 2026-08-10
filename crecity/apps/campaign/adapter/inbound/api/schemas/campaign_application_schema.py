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
    created_at: datetime | None
