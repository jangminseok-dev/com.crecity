from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from admin.adapter.outbound.pg.audit_log_pg_repository import AuditLogPgRepository
from admin.adapter.outbound.pg.audit_record_adapters import PgAuditRecordAdapter
from admin.app.ports.input.dispute_resolution_use_case import DisputeResolutionUseCase
from admin.app.use_cases.dispute_resolution_interactor import DisputeResolutionInteractor
from core.database import get_db
from hub.dependencies.dispute_resolution_provider import get_dispute_resolution_port


def get_dispute_resolution_use_case(
    db: AsyncSession = Depends(get_db),
) -> DisputeResolutionUseCase:
    return DisputeResolutionInteractor(
        disputes=get_dispute_resolution_port(),
        record=PgAuditRecordAdapter(AuditLogPgRepository(session=db)),
    )
