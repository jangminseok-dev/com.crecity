from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from order.adapter.outbound.pg.ledger_pg_repository import LedgerPgRepository
from order.app.ports.input.balance_lookup_use_case import BalanceLookupUseCase
from order.app.use_cases.balance_lookup_interactor import BalanceLookupInteractor


def get_balance_lookup_use_case(
    db: AsyncSession = Depends(get_db),
) -> BalanceLookupUseCase:
    return BalanceLookupInteractor(ledger=LedgerPgRepository(session=db))
