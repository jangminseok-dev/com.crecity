from __future__ import annotations

from order.app.dtos.monthly_report_dto import MonthlyReportQuery, MonthlyReportRow
from order.app.ports.input.monthly_report_use_case import MonthlyReportUseCase
from order.app.ports.output.ledger_repository import LedgerRepository


class MonthlyReportInteractor(MonthlyReportUseCase):

    def __init__(self, ledger: LedgerRepository) -> None:
        self._ledger = ledger

    async def report(self, query: MonthlyReportQuery) -> list[MonthlyReportRow]:
        # 돈의 정본은 원장 — 주문 표가 아니라 기입을 집계해야 환불·인출·복원이 다 잡힌다
        summary = await self._ledger.monthly_summary(query.user_id, query.year)
        return [
            MonthlyReportRow(month=month, entry_type=entry_type, total_krw=total, count=count)
            for month, entry_type, total, count in summary
        ]
