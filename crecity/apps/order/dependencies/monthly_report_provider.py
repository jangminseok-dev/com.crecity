from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from order.adapter.outbound.pg.ledger_pg_repository import LedgerPgRepository
from order.app.ports.input.monthly_report_use_case import MonthlyReportUseCase
from order.app.use_cases.monthly_report_interactor import MonthlyReportInteractor


def get_monthly_report_use_case(
    db: AsyncSession = Depends(get_db),
) -> MonthlyReportUseCase:
    return MonthlyReportInteractor(ledger=LedgerPgRepository(session=db))
