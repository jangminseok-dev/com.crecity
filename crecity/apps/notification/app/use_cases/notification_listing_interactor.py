from __future__ import annotations

from notification.app.dtos.notification_listing_dto import NotificationItem, NotificationsResult
from notification.app.ports.input.notification_listing_use_case import NotificationListingUseCase
from notification.app.ports.output.notification_repository import NotificationRepository

_LIST_LIMIT = 50


class NotificationListingInteractor(NotificationListingUseCase):

    def __init__(self, notifications: NotificationRepository) -> None:
        self._notifications = notifications

    async def list_mine(self, user_id: int) -> NotificationsResult:
        items = await self._notifications.list_by_user(user_id, _LIST_LIMIT)
        unread = await self._notifications.unread_count(user_id)
        return NotificationsResult(
            unread_count=unread,
            items=[
                NotificationItem(
                    id=n.id,
                    event_type=n.event_type,
                    body=n.body,
                    link=n.link,
                    is_read=n.is_read,
                    created_at=n.created_at,
                )
                for n in items
            ],
        )

    async def mark_all_read(self, user_id: int) -> None:
        await self._notifications.mark_all_read(user_id)
