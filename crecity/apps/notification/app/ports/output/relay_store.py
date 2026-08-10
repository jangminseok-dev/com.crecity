from __future__ import annotations

from abc import ABC, abstractmethod

from notification.app.dtos.outbox_relay_dto import NotificationDraft, OutboxRecord


class RelayStore(ABC):
    """릴레이 저장소 포트 — Outbox 소비와 알림 생성을 원자적으로 묶는다."""

    @abstractmethod
    async def fetch_unpublished(self, limit: int) -> list[OutboxRecord]:
        """미발행 이벤트 — 오래된 순."""
        ...

    @abstractmethod
    async def publish(self, event_ids: list[int], drafts: list[NotificationDraft]) -> None:
        """알림 저장 + 발행 마킹 = 단일 커밋(중복 발송 방지)."""
        ...
