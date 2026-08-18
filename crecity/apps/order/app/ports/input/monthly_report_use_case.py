from __future__ import annotations

from abc import ABC, abstractmethod

from order.app.dtos.monthly_report_dto import MonthlyReportQuery, MonthlyReportRow


class MonthlyReportUseCase(ABC):
    """수익·지출 월별 리포트(갭 #90) — 원장 기입을 본인 기준으로 요약한다."""

    @abstractmethod
    async def report(self, query: MonthlyReportQuery) -> list[MonthlyReportRow]: ...
