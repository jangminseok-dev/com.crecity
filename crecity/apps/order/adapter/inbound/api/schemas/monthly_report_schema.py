from __future__ import annotations

from pydantic import BaseModel

from order.app.dtos.monthly_report_dto import MonthlyReportRow


class MonthlyReportRowSchema(BaseModel):
    """월×기입유형 요약 1행(갭 #90) — 화면이 계정 유형에 맞게 표를 구성한다."""

    month: int
    entry_type: str
    total_krw: int
    count: int

    @classmethod
    def from_row(cls, row: MonthlyReportRow) -> MonthlyReportRowSchema:
        return cls(
            month=row.month,
            entry_type=row.entry_type,
            total_krw=row.total_krw,
            count=row.count,
        )
