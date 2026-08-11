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
