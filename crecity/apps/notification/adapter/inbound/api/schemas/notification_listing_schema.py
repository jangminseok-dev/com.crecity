from datetime import datetime

from pydantic import BaseModel


class NotificationItemSchema(BaseModel):

    id: int
    event_type: str
    body: str
    link: str | None
    is_read: bool
    created_at: datetime | None


class NotificationsResponseSchema(BaseModel):

    unread_count: int
    items: list[NotificationItemSchema]
