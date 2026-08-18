from dataclasses import dataclass


@dataclass(frozen=True)
class MonthlyReportQuery:

    user_id: int  # 항상 본인 — 남의 리포트 조회 불가
    year: int


@dataclass(frozen=True)
class MonthlyReportRow:
    """월×기입유형 요약 1행 — 화면이 계정 유형에 맞게 표를 구성한다."""

    month: int
    entry_type: str
    total_krw: int
    count: int
