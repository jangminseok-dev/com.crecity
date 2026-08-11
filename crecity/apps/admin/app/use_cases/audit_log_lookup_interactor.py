from __future__ import annotations

from admin.app.dtos.audit_log_dto import AuditLogResult
from admin.app.ports.input.audit_log_lookup_use_case import AuditLogLookupUseCase
from admin.app.ports.output.audit_log_repository import AuditLogRepository

_LIST_LIMIT = 200


class AuditLogLookupInteractor(AuditLogLookupUseCase):

    def __init__(self, repository: AuditLogRepository) -> None:
        self._repository = repository

    async def list_recent(self) -> list[AuditLogResult]:
        entries = await self._repository.list_recent(_LIST_LIMIT)
        return [
            AuditLogResult(
                id=entry.id,
                subject=entry.subject,
                note=entry.note,
                created_at=entry.created_at,
            )
            for entry in entries
        ]
