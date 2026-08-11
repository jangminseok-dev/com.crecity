from __future__ import annotations

from abc import ABC, abstractmethod

from notification.app.dtos.notification_listing_dto import NotificationsResult


class NotificationListingUseCase(ABC):
    """내 알림 조회·읽음 처리 유스케이스."""

    @abstractmethod
    async def list_mine(self, user_id: int) -> NotificationsResult:
        """내 알림 — 최신순(최근 50개) + 안 읽음 개수."""
        ...

    @abstractmethod
    async def mark_read(self, user_id: int, notification_id: int) -> None:
        """알림 하나만 읽음 처리(갭 #34).

        Raises:
            NotificationNotFoundError: 없거나 본인 알림이 아님.
        """
        ...

    @abstractmethod
    async def mark_all_read(self, user_id: int) -> None:
        """내 알림 전체 읽음 처리."""
        ...
