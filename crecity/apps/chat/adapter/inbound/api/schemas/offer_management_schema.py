from datetime import datetime

from pydantic import BaseModel, Field


class OfferCreateRequestSchema(BaseModel):

    title: str = Field(min_length=1, max_length=100)
    price_krw: int = Field(gt=0)


class OfferResponseSchema(BaseModel):

    id: int
    conversation_id: int
    title: str
    price_krw: int
    status: str
    order_id: int | None
    created_at: datetime | None
