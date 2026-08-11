from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from admin.adapter.outbound.pg.audit_log_pg_repository import AuditLogPgRepository
from admin.app.ports.input.audit_log_lookup_use_case import AuditLogLookupUseCase
from admin.app.use_cases.audit_log_lookup_interactor import AuditLogLookupInteractor
from core.database import get_db


def get_audit_log_lookup_use_case(
    db: AsyncSession = Depends(get_db),
) -> AuditLogLookupUseCase:
    return AuditLogLookupInteractor(repository=AuditLogPgRepository(session=db))
