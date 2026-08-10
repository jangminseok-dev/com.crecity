from datetime import datetime

from pydantic import BaseModel, Field


class OpenConversationRequestSchema(BaseModel):

    creator_slug: str = Field(..., description="문의할 크리에이터의 슬러그")


class ConversationResponseSchema(BaseModel):

    id: int
    counterpart_name: str
    counterpart_slug: str | None
    last_message: str | None
    last_message_at: datetime | None
    created_at: datetime | None
