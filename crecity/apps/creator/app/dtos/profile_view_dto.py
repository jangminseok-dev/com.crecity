from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class ProfileViewRecordCommand:

    slug: str


@dataclass(frozen=True)
class DailyView:

    view_date: date
    view_count: int


@dataclass(frozen=True)
class ProfileViewsResult:
    """최근 N일 추이 + 합계 — 크리에이터 본인만 본다."""

    days: int
    total: int
    daily: list[DailyView]
