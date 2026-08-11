from __future__ import annotations

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from admin.adapter.outbound.orm.audit_log_orm import AdminAuditLogOrm
from admin.app.ports.output.audit_log_repository import AuditLogEntry, AuditLogRepository


class AuditLogPgRepository(AuditLogRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(self, subject: str, note: str) -> None:
        await self._session.execute(
            insert(AdminAuditLogOrm).values(subject=subject, note=note)
        )
        await self._session.commit()

    async def list_recent(self, limit: int) -> list[AuditLogEntry]:
        result = await self._session.execute(
            select(AdminAuditLogOrm)
            .order_by(AdminAuditLogOrm.created_at.desc(), AdminAuditLogOrm.id.desc())
            .limit(limit)
        )
        return [
            AuditLogEntry(id=o.id, subject=o.subject, note=o.note, created_at=o.created_at)
            for o in result.scalars()
        ]
