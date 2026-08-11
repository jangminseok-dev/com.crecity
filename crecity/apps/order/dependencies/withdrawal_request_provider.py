from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import WITHDRAWAL_TAX_PERMILLE
from core.database import get_db
from order.adapter.outbound.pg.withdrawal_pg_repository import WithdrawalPgRepository
from order.app.ports.input.withdrawal_request_use_case import WithdrawalRequestUseCase
from order.app.use_cases.withdrawal_request_interactor import WithdrawalRequestInteractor


def get_withdrawal_request_use_case(
    db: AsyncSession = Depends(get_db),
) -> WithdrawalRequestUseCase:
    return WithdrawalRequestInteractor(
        withdrawals=WithdrawalPgRepository(session=db),
        tax_permille=WITHDRAWAL_TAX_PERMILLE,
    )
