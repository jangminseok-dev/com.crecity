from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class WithdrawalRequestCommand:

    user_id: int
    account_type: str  # CREATOR만 인출 가능
    amount_krw: int
    bank_name: str
    account_number: str
    account_holder: str


@dataclass(frozen=True)
class WithdrawalResult:

    id: int
    amount_krw: int
    tax_krw: int
    payout_krw: int
    bank_name: str
    account_number: str
    account_holder: str
    status: str
    created_at: datetime | None
    settled_at: datetime | None
