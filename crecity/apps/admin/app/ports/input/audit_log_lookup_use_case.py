from __future__ import annotations

from abc import ABC, abstractmethod

from admin.app.dtos.audit_log_dto import AuditLogResult


class AuditLogLookupUseCase(ABC):
    """운영 감사 로그 조회(갭 #36) — 심사·인출 처리 이력을 최신순으로 본다."""

    @abstractmethod
    async def list_recent(self) -> list[AuditLogResult]:
        """최근 기록(상한 200건)."""
        ...
