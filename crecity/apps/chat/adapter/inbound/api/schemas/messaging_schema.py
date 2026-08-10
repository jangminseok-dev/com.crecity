from datetime import datetime

from pydantic import BaseModel, Field


class SendMessageRequestSchema(BaseModel):

    body: str = Field(..., min_length=1, max_length=2000)


class MessageResponseSchema(BaseModel):

    id: int
    conversation_id: int
    sender_user_id: int
    body: str
    is_mine: bool
    created_at: datetime | None
