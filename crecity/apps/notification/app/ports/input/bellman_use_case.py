from __future__ import annotations

from abc import ABC, abstractmethod

from notification.app.dtos.bellman_dto import BellmanQuery, BellmanResponse


class BellmanUseCase(ABC):
    """알림 (notification) 유스케이스 — Outbox 릴레이·인앱 알림 담당."""

    @abstractmethod
    async def introduce_myself(self, query: BellmanQuery) -> BellmanResponse:
        """알림 (notification)의 자기소개 메소드."""
        ...
