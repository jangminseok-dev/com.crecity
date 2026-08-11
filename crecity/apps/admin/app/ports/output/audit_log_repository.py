from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class AuditLogEntry:
    """저장된 감사 기록 — 조회 응답용."""

    id: int
    subject: str
    note: str
    created_at: datetime | None


class AuditLogRepository(ABC):
    """감사 로그 영속성 포트 — append-only."""

    @abstractmethod
    async def append(self, subject: str, note: str) -> None: ...

    @abstractmethod
    async def list_recent(self, limit: int) -> list[AuditLogEntry]:
        """최신순."""
        ...
