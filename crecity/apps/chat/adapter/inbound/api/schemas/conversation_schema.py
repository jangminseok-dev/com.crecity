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
    unread_count: int = 0  # 내가 안 읽은 상대 메시지 수(갭 #35)
    created_at: datetime | None
