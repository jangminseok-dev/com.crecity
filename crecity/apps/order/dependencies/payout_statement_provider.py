from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from order.adapter.outbound.pg.withdrawal_pg_repository import WithdrawalPgRepository
from order.app.ports.input.payout_statement_use_case import PayoutStatementUseCase
from order.app.use_cases.payout_statement_interactor import PayoutStatementInteractor


def get_payout_statement_use_case(db: AsyncSession = Depends(get_db)) -> PayoutStatementUseCase:
    return PayoutStatementInteractor(withdrawals=WithdrawalPgRepository(session=db))
