from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class NotificationItem:

    id: int
    event_type: str
    body: str
    link: str | None
    is_read: bool
    created_at: datetime | None


@dataclass(frozen=True)
class NotificationsResult:

    unread_count: int
    items: list[NotificationItem]
