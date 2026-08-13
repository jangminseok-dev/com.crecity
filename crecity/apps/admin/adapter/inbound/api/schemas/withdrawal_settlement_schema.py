from datetime import datetime

from pydantic import BaseModel


class AnnualPayoutSummarySchema(BaseModel):

    creator_user_id: int
    account_holder: str
    count: int
    total_amount_krw: int
    total_tax_krw: int
    total_payout_krw: int


class WithdrawalSummarySchema(BaseModel):

    id: int
    creator_user_id: int
    amount_krw: int
    tax_krw: int
    payout_krw: int
    bank_name: str
    account_number: str
    account_holder: str
    status: str
    created_at: datetime | None
