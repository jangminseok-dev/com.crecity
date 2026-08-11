from datetime import datetime

from pydantic import BaseModel, Field


class WithdrawalRequestSchema(BaseModel):

    amount_krw: int = Field(..., gt=0)
    bank_name: str = Field(..., min_length=1, max_length=50)
    account_number: str = Field(..., min_length=1, max_length=50)
    account_holder: str = Field(..., min_length=1, max_length=50)


class WithdrawalResponseSchema(BaseModel):

    id: int
    amount_krw: int
    tax_krw: int  # 원천징수 3.3%
    payout_krw: int  # 실지급액
    bank_name: str
    account_number: str
    account_holder: str
    status: str  # REQUESTED | PAID | FAILED
    created_at: datetime | None
    settled_at: datetime | None
