from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from admin.adapter.outbound.pg.audit_log_pg_repository import AuditLogPgRepository
from admin.adapter.outbound.pg.audit_record_adapters import PgAuditRecordAdapter
from admin.app.ports.input.withdrawal_settlement_use_case import WithdrawalSettlementUseCase
from admin.app.use_cases.withdrawal_settlement_interactor import WithdrawalSettlementInteractor
from core.database import get_db
from hub.dependencies.withdrawal_settlement_provider import get_withdrawal_settlement_port


def get_withdrawal_settlement_use_case(
    db: AsyncSession = Depends(get_db),
) -> WithdrawalSettlementUseCase:
    return WithdrawalSettlementInteractor(
        withdrawals=get_withdrawal_settlement_port(),
        record=PgAuditRecordAdapter(AuditLogPgRepository(session=db)),
    )
