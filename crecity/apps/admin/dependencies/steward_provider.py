from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from admin.adapter.outbound.pg.audit_log_pg_repository import AuditLogPgRepository
from admin.adapter.outbound.pg.audit_record_adapters import PgAuditRecordAdapter
from admin.app.ports.input.steward_use_case import StewardUseCase
from admin.app.use_cases.steward_interactor import StewardInteractor
from core.database import get_db


def get_steward_use_case(db: AsyncSession = Depends(get_db)) -> StewardUseCase:
    return StewardInteractor(record=PgAuditRecordAdapter(AuditLogPgRepository(session=db)))
