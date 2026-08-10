from __future__ import annotations

from abc import ABC, abstractmethod

from notification.domain.entities.notification_entity import Notification


class NotificationRepository(ABC):
    """알림 영속성 포트 (도메인어 명명 예외) — 조회·읽음 처리 전용(생성은 RelayStore)."""

    @abstractmethod
    async def list_by_user(self, user_id: int, limit: int) -> list[Notification]:
        """최신순."""
        ...

    @abstractmethod
    async def unread_count(self, user_id: int) -> int: ...

    @abstractmethod
    async def mark_all_read(self, user_id: int) -> None: ...
