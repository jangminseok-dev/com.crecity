from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class WithdrawalSummary:
    """운영 처리용 인출 요약 — order가 소유한 인출을 admin이 처리할 때의 계약."""

    id: int
    creator_user_id: int
    amount_krw: int
    tax_krw: int
    payout_krw: int
    bank_name: str
    account_number: str
    account_holder: str
    status: str  # REQUESTED | PAID | FAILED
    created_at: datetime | None


@dataclass(frozen=True)
class AnnualPayoutSummary:
    """크리에이터별 연간 지급 집계 — 국세청 지급명세서 제출 자료(갭 #2).

    지급일(settled_at) 연도 기준, 지급 완료(PAID)된 인출만 센다.
    """

    creator_user_id: int
    account_holder: str  # 마지막 지급의 예금주 스냅샷(표시용)
    count: int
    total_amount_krw: int
    total_tax_krw: int
    total_payout_krw: int
